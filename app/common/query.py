"""
Generic, reusable "list endpoint" engine.

Use the SAME three things for every resource in the app:

    params: ListParams = Depends(list_query_params)     # parses page/pageSize/filter/orderBy/fields
    return await list_records(db, Task, TaskResponse, params)

Query params (exactly these, nothing else):
    page      -> 1-indexed page number
    pageSize  -> items per page
    filter    -> used ONCE. A JSON object string: {"field": value, ...}
    orderBy   -> repeatable, format "field direction"  e.g. "name desc"
    fields    -> comma-separated sparse fieldset, e.g. "id,name,status"

Response shape (always):
    { "count": <int>, "data": [ ... ] }

--------------------------------------------------------------------------
Filter param shape
--------------------------------------------------------------------------
`filter` is a single query param holding a JSON object. No colons, no
delimiter-parsing ambiguity -- each key is a field name, each value is
either a scalar or an array (for ranges / multi-select).

    filter={"name":"proj","status":["in_progress","done"],
            "due_time":["2026-07-01T00:00:00","2026-07-31T23:59:59"]}

URL-encoded, that's just one `filter=...` in the query string -- this is
also literally what MUI DataGrid's filterModel looks like, so the frontend
can often just JSON.stringify() its own filter state and send it as-is.

Filter semantics (per column type, auto-detected via SQLAlchemy column type):
    string   -> ILIKE '%value%' per token                (partial match)
    number   -> CAST(col AS TEXT) ILIKE '%value%' per token
    date     -> 1 value -> equality
                2 values -> BETWEEN
    datetime -> exactly 2 values -> BETWEEN (start, end)
    enum     -> 1+ values -> IN (...)                     (multi-select)
    boolean  -> exact match, accepts true/false/1/0/yes/no

All individual conditions (regardless of field) are combined with OR,
per spec. Nested/relationship/JSON dotted filters (e.g. "user.name") are
intentionally NOT supported -- only the resource's own columns are filterable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import date, datetime
from enum import Enum as PyEnum
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    cast,
    func,
    or_,
    select,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, noload, selectinload
from sqlalchemy.sql.elements import ColumnElement


# --------------------------------------------------------------------------
# 1. Query-param parsing -- identical for every resource
# --------------------------------------------------------------------------
@dataclass
class ListParams:
    page: int
    page_size: int
    filters: dict[str, Any] = dc_field(default_factory=dict)
    order_by: list[str] = dc_field(default_factory=list)
    fields: str | None = None


def list_query_params(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    pageSize: int = Query(20, ge=1, le=200, description="Items per page"),
    filter: str | None = Query(  # noqa: A002
        None,
        description=(
            'Single JSON object, e.g. {"name":"proj","status":["in_progress","done"]}'
        ),
    ),
    orderBy: list[str] | None = Query(
        None, description="Repeatable. Format 'field direction', e.g. 'name desc'."
    ),
    fields: str | None = Query(
        None, description="Comma-separated fields to return."),
) -> ListParams:
    filters: dict[str, Any] = {}
    if filter:
        try:
            parsed = json.loads(filter)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'filter' must be valid JSON, e.g. {\"name\":\"proj\"}.",
            ) from None
        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'filter' must be a JSON object mapping field -> value.",
            )
        filters = parsed

    return ListParams(
        page=page,
        page_size=pageSize,
        filters=filters,
        order_by=orderBy or [],
        fields=fields,
    )


# --------------------------------------------------------------------------
# 2. Per-model introspection, built once and cached (not per-request)
# --------------------------------------------------------------------------
class _ModelIntrospection:
    __slots__ = ("model", "columns", "relationships", "response_fields")

    def __init__(self, model: type[DeclarativeBase], schema: type[BaseModel]) -> None:
        mapper = model.__mapper__
        self.model = model
        self.columns = {c.key: c for c in mapper.columns}
        self.relationships = set(mapper.relationships.keys())
        self.response_fields = set(schema.model_fields.keys())


@lru_cache(maxsize=None)
def _get_introspection(model: type[DeclarativeBase], schema: type[BaseModel]) -> _ModelIntrospection:
    return _ModelIntrospection(model, schema)


def _column_category(sa_type: Any) -> str:
    if isinstance(sa_type, SAEnum):
        return "enum"
    if isinstance(sa_type, Boolean):
        return "boolean"
    if isinstance(sa_type, DateTime):
        return "datetime"
    if isinstance(sa_type, Date):
        return "date"
    if isinstance(sa_type, (Integer, Numeric)):
        return "number"
    return "string"  # String, Text, Unicode, etc. -- safe default


def _as_list(value: Any) -> list[str]:
    """Normalize a filter value (scalar or array) into a list of strings."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip() != ""]
    return [str(value).strip()]


# --------------------------------------------------------------------------
# 3. Filter condition builder -- one field:value(s) entry -> 1+ conditions
# --------------------------------------------------------------------------
def _build_conditions_for_field(
    intro: _ModelIntrospection, field: str, raw_value: Any
) -> list[ColumnElement[bool]]:
    if field not in intro.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field}' is not filterable.",
        )

    column: InstrumentedAttribute = getattr(intro.model, field)
    category = _column_category(intro.columns[field].type)
    values = _as_list(raw_value)

    if not values:
        return []

    if category == "string":
        return [column.ilike(f"%{v}%") for v in values]

    if category == "number":
        return [cast(column, String).ilike(f"%{v}%") for v in values]

    if category == "boolean":
        # Exact match only, always a single value -- last one wins if an
        # array was sent by mistake.
        return [column.is_(_coerce_boolean(values[-1], field))]

    if category == "enum":
        enum_cls: type[PyEnum] = intro.columns[field].type.enum_class
        coerced = [_coerce_enum(enum_cls, v, field) for v in values]
        return [column.in_(coerced)]

    if category == "date":
        parsed = [_coerce_date(v, field) for v in values]
        if len(parsed) == 1:
            return [column == parsed[0]]
        if len(parsed) == 2:
            lo, hi = sorted(parsed)
            return [column.between(lo, hi)]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field}' accepts either 1 date or 2 dates (range).",
        )

    if category == "datetime":
        if len(values) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field}' requires exactly 2 ISO datetimes: [start, end].",
            )
        lo, hi = sorted(_coerce_datetime(v, field) for v in values)
        return [column.between(lo, hi)]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported column type for field '{field}'.",
    )


def _coerce_enum(enum_cls: type[PyEnum], token: str, field: str) -> PyEnum:
    try:
        return enum_cls[token.upper()]
    except KeyError:
        try:
            return enum_cls(token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value '{token}' for enum field '{field}'.",
            ) from None


_TRUE_TOKENS = {"true", "1", "yes"}
_FALSE_TOKENS = {"false", "0", "no"}


def _coerce_boolean(value: str, field: str) -> bool:
    token = value.strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid boolean '{value}' for field '{field}'. Use true/false.",
    )


def _coerce_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date '{value}' for field '{field}'. Use YYYY-MM-DD.",
        ) from None


def _coerce_datetime(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid datetime '{value}' for field '{field}'. Use ISO-8601.",
        ) from None


# --------------------------------------------------------------------------
# 4. Order-by builder -- "field direction", top-level columns only
# --------------------------------------------------------------------------
def _build_order_clauses(intro: _ModelIntrospection, raw_order_by: list[str]) -> list[ColumnElement[Any]]:
    if not raw_order_by:
        pk_columns = [c.key for c in intro.model.__mapper__.primary_key]
        return [getattr(intro.model, pk).asc() for pk in pk_columns]

    clauses: list[ColumnElement[Any]] = []
    for raw in raw_order_by:
        parts = raw.strip().split()
        field = parts[0]
        direction = parts[1].lower() if len(parts) > 1 else "asc"

        if field not in intro.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field}' is not sortable.",
            )
        if direction not in {"asc", "desc"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort direction '{direction}' for field '{field}'.",
            )

        column = getattr(intro.model, field)
        clauses.append(column.asc() if direction == "asc" else column.desc())

    return clauses


# --------------------------------------------------------------------------
# 5. Sparse fieldset resolution
# --------------------------------------------------------------------------
def _resolve_fields(intro: _ModelIntrospection, raw_fields: str | None) -> set[str]:
    if not raw_fields:
        return set(intro.response_fields)

    requested = {f.strip() for f in raw_fields.split(",") if f.strip()}
    invalid = requested - intro.response_fields
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown field(s): {', '.join(sorted(invalid))}.",
        )
    if "id" in intro.response_fields:
        requested.add("id")
    return requested


# --------------------------------------------------------------------------
# 6. The single reusable entry point every list endpoint calls
# --------------------------------------------------------------------------
async def list_records(
    db: AsyncSession,
    model: type[DeclarativeBase],
    schema: type[BaseModel],
    params: ListParams,
) -> dict[str, Any]:
    intro = _get_introspection(model, schema)

    conditions: list[ColumnElement[bool]] = []
    for field, raw_value in params.filters.items():
        conditions.extend(_build_conditions_for_field(intro, field, raw_value))
    where_clause = or_(*conditions) if conditions else None

    # --- total count, same filter, no order/limit/joins ---
    count_stmt = select(func.count()).select_from(model)
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    # --- page of data ---
    selected_fields = _resolve_fields(intro, params.fields)

    stmt = select(model)
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    stmt = stmt.order_by(*_build_order_clauses(intro, params.order_by))
    stmt = stmt.offset((params.page - 1) *
                       params.page_size).limit(params.page_size)

    # Only pay for relationship loads the caller actually asked for.
    for rel_name in intro.relationships:
        rel_attr = getattr(model, rel_name)
        stmt = stmt.options(
            selectinload(
                rel_attr) if rel_name in selected_fields else noload(rel_attr)
        )

    rows = (await db.execute(stmt)).scalars().all()

    data = [
        {k: v for k, v in schema.model_validate(row).model_dump(
            mode="json").items() if k in selected_fields}
        for row in rows
    ]

    return {"count": total, "data": data}

"""
Generic, reusable "list endpoint" engine.

Use the SAME three things for every resource in the app:

    params: ListParams = Depends(list_query_params)     # parses page/pageSize/filter/orderBy/fields
    return await list_records(db, Task, TaskResponse, params)

Query params (exactly these, nothing else):
    page      -> 1-indexed page number
    pageSize  -> items per page
    filter    -> repeatable, format "field:value"  (operator is auto-picked from column type)
    orderBy   -> repeatable, format "field direction"  e.g. "name desc"
    fields    -> comma-separated sparse fieldset, e.g. "id,name,status"

Response shape (always):
    { "count": <int>, "data": [ ... ] }

Filter semantics (per column type, auto-detected via SQLAlchemy column type):
    string   -> ILIKE '%value%'                          (partial match)
    number   -> CAST(col AS TEXT) ILIKE '%value%'         (partial match on int/float/numeric)
    date     -> single value -> equality
                two comma-separated values -> BETWEEN
    datetime -> two comma-separated ISO values -> BETWEEN (start,end)
    enum     -> comma-separated values -> IN (...)         (multi-select)

All individual filter conditions (regardless of field) are combined with OR,
per spec. Nested/relationship/JSON dotted filters (e.g. "user.name") are
intentionally NOT supported -- only the resource's own columns are filterable.
This keeps the surface area small, safe, and identical across every resource.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import date, datetime
from enum import Enum as PyEnum
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import Date, DateTime, Integer, Numeric, String, cast, func, or_, select
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
    filters: list[str] = dc_field(default_factory=list)
    order_by: list[str] = dc_field(default_factory=list)
    fields: str | None = None


def list_query_params(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    pageSize: int = Query(20, ge=1, le=200, description="Items per page"),
    filter: list[str] | None = Query(  # noqa: A002
        None, description="Repeatable. Format 'field:value'."
    ),
    orderBy: list[str] | None = Query(
        None, description="Repeatable. Format 'field direction', e.g. 'name desc'."
    ),
    fields: str | None = Query(
        None, description="Comma-separated fields to return."),
) -> ListParams:
    return ListParams(
        page=page,
        page_size=pageSize,
        filters=filter or [],
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
    if isinstance(sa_type, DateTime):
        return "datetime"
    if isinstance(sa_type, Date):
        return "date"
    if isinstance(sa_type, (Integer, Numeric)):
        return "number"
    return "string"  # String, Text, Unicode, etc. -- safe default


# --------------------------------------------------------------------------
# 3. Filter condition builder -- one condition per "field:value" pair
# --------------------------------------------------------------------------
def _build_condition(intro: _ModelIntrospection, raw: str) -> ColumnElement[bool]:
    field, sep, raw_value = raw.partition(":")
    if not sep:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed filter '{raw}'. Expected 'field:value'.",
        )
    field = field.strip()
    raw_value = raw_value.strip()

    if field not in intro.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field}' is not filterable.",
        )

    column: InstrumentedAttribute = getattr(intro.model, field)
    category = _column_category(intro.columns[field].type)

    if category == "string":
        return column.ilike(f"%{raw_value}%")

    if category == "number":
        return cast(column, String).ilike(f"%{raw_value}%")

    if category == "enum":
        enum_cls: type[PyEnum] = intro.columns[field].type.enum_class
        values: list[PyEnum] = []
        for token in raw_value.split(","):
            token = token.strip()
            if not token:
                continue
            values.append(_coerce_enum(enum_cls, token, field))
        if not values:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid values supplied for field '{field}'.",
            )
        return column.in_(values)

    if category == "date":
        parts = [p.strip() for p in raw_value.split(",") if p.strip()]
        parsed = [_coerce_date(p, field) for p in parts]
        if len(parsed) == 1:
            return column == parsed[0]
        if len(parsed) == 2:
            lo, hi = sorted(parsed)
            return column.between(lo, hi)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field}' accepts either 1 date or 2 comma-separated dates (range).",
        )

    if category == "datetime":
        parts = [p.strip() for p in raw_value.split(",") if p.strip()]
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field}' requires exactly 2 comma-separated ISO datetimes (start,end).",
            )
        lo, hi = sorted(_coerce_datetime(p, field) for p in parts)
        return column.between(lo, hi)

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
# 5. Sparse fieldset resolution + serialization
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

    conditions = [_build_condition(intro, raw) for raw in params.filters]
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

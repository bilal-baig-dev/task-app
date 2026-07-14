from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(
    scheme_name="Bearer Authentication",
    description="Paste your JWT access token.",
)

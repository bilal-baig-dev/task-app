from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):

    email: EmailStr
    name: str


class UserUpdate(BaseModel):
    name: str


class UserResponse(BaseModel):

    id: str
    email: EmailStr
    name: str

    model_config = {
        "from_attributes": True
    }


class EmailQueryParam(BaseModel):
    email: EmailStr


class UserNotFoundException(Exception):
    pass

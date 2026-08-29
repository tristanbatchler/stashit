from pydantic import BaseModel


class Message(BaseModel):
    detail: str


class GoogleLoginLocation(BaseModel):
    url: str

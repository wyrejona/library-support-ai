# app/schemas.py
from pydantic import BaseModel

class Query(BaseModel):
    query: str

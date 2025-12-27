from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class AppCreate(BaseModel):
    name: str
    description: str


class AppResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: str
    port: int | None
    wasp_schema: str | None
    prisma_schema: str | None
    source_files: dict | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppListResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: str
    port: int | None
    created_at: datetime

    class Config:
        from_attributes = True


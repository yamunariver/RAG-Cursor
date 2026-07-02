import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: str = "viewer"
    department: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    department: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseCreate(BaseModel):
    name: str
    slug: str
    department: str | None = None
    description: str | None = None


class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    department: str | None
    description: str | None
    qdrant_collection: str
    is_active: bool

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    version: int
    page_count: int | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str
    knowledge_base_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    stream: bool = True


class Citation(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    page_number: int | None
    snippet: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    conversation_id: uuid.UUID


class SearchRequest(BaseModel):
    query: str
    knowledge_base_id: uuid.UUID
    top_k: int = 20
    filters: dict | None = None


class SearchResult(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    content: str
    score: float
    page_number: int | None = None

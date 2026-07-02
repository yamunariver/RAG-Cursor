from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "production"
    app_secret_key: str = "change-me"
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://rag:ragsecret@postgres:5432/enterprise_rag"

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    celery_concurrency: int = 8

    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_bucket: str = "documents"
    minio_secure: bool = False

    ollama_base_url: str = "http://ollama:11434"
    chat_model: str = "qwen2.5:7b-instruct"
    vision_model: str = "qwen2.5-vl"
    embedding_model: str = "bge-m3"
    reranker_model: str = "bge-reranker-large"

    knowledge_root: str = "/data/knowledge"
    upload_root: str = "/data/uploads"
    max_upload_mb: int = 500
    ingestion_workers: int = 40
    chunk_size: int = 512
    chunk_overlap: int = 64
    enable_ocr: bool = True

    retrieval_top_k: int = 20
    rerank_top_k: int = 8
    hybrid_vector_weight: float = 0.7

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    enable_virus_scan: bool = False
    clamav_host: str = "clamav"
    clamav_port: int = 3310


settings = Settings()

import io
from functools import lru_cache

import clamd
from minio import Minio

from app.config import settings


@lru_cache
def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=settings.minio_secure,
    )


def ensure_bucket() -> None:
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_bytes(object_name: str, data: bytes, content_type: str) -> str:
    ensure_bucket()
    client = get_minio_client()
    client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return f"{settings.minio_bucket}/{object_name}"


def download_bytes(storage_path: str) -> bytes:
    bucket, object_name = storage_path.split("/", 1)
    client = get_minio_client()
    response = client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def scan_bytes(data: bytes) -> None:
    if not settings.enable_virus_scan:
        return

    cd = clamd.ClamdNetworkHost(settings.clamav_host, settings.clamav_port)
    result = cd.instream(io.BytesIO(data))
    status, signature = result.get("stream", ("OK", None))
    if status == "FOUND":
        raise ValueError(f"Malware detected: {signature}")

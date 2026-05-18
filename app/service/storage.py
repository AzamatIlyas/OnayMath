from __future__ import annotations

import re
from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.core.settings import settings


@lru_cache(maxsize=1)
def get_r2_client() -> BaseClient | None:
    if not settings.R2_ENABLED:
        return None

    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def _extract_key(value: str) -> str:
    key = value.strip()
    key = re.sub(r"^s3://[^/]+/", "", key)
    key = re.sub(r"^https?://[^/]+/", "", key)
    key = key.lstrip("/")
    bucket_prefix = f"{settings.R2_BUCKET_NAME}/" if settings.R2_BUCKET_NAME else None
    if bucket_prefix and key.startswith(bucket_prefix):
        key = key[len(bucket_prefix) :]
    return key


def build_book_signed_url(file_url_or_key: str) -> str:
    if not file_url_or_key:
        return file_url_or_key

    client = get_r2_client()
    if not client or not settings.R2_BUCKET_NAME:
        return file_url_or_key

    key = _extract_key(file_url_or_key)
    if not key:
        return file_url_or_key

    try:
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
            ExpiresIn=settings.R2_PRESIGNED_EXPIRES_SECONDS,
        )
    except Exception:
        return file_url_or_key


def build_r2_object_url(key: str) -> str:
    if not settings.R2_ENDPOINT_URL or not settings.R2_BUCKET_NAME:
        return key
    normalized = key.lstrip("/")
    return f"{settings.R2_ENDPOINT_URL.rstrip('/')}/{settings.R2_BUCKET_NAME}/{normalized}"


def upload_book_pdf(file_obj: BinaryIO, key: str, content_type: str = "application/pdf") -> str:
    client = get_r2_client()
    if not client or not settings.R2_BUCKET_NAME:
        raise RuntimeError("R2 storage is not configured")

    normalized_key = key.lstrip("/")
    file_obj.seek(0)
    client.upload_fileobj(
        file_obj,
        settings.R2_BUCKET_NAME,
        normalized_key,
        ExtraArgs={"ContentType": content_type},
    )
    return build_r2_object_url(normalized_key)

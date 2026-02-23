from __future__ import annotations

from typing import BinaryIO
from urllib.parse import quote

import boto3

import settings


class S3Service:
    def __init__(
        self,
        *,
        bucket_name: str = settings.S3_BUCKET_NAME,
        endpoint_url: str = settings.S3_ENDPOINT_URL,
        region_name: str = settings.S3_REGION_NAME,
        access_key_id: str = settings.S3_ACCESS_KEY_ID,
        secret_access_key: str = settings.S3_SECRET_ACCESS_KEY,
    ) -> None:
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def upload_bytes(
        self,
        content: bytes,
        key: str,
        *,
        content_type: str | None = None,
        make_public: bool = True,
    ) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if make_public:
            extra_args["ACL"] = "public-read"

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            **extra_args,
        )
        return self.build_public_url(key)

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        key: str,
        *,
        content_type: str | None = None,
        make_public: bool = True,
    ) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if make_public:
            extra_args["ACL"] = "public-read"

        kwargs = {
            "Fileobj": file_obj,
            "Bucket": self.bucket_name,
            "Key": key,
        }
        if extra_args:
            kwargs["ExtraArgs"] = extra_args

        self.client.upload_fileobj(**kwargs)
        return self.build_public_url(key)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=key)

    def build_public_url(self, key: str) -> str:
        normalized_key = key.lstrip("/")
        return f"{self.endpoint_url}/{self.bucket_name}/{quote(normalized_key)}"


s3_service = S3Service()

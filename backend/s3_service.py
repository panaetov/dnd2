from __future__ import annotations

from datetime import datetime
from typing import BinaryIO
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

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

    def _resolve_bucket(self, bucket_name: str | None = None) -> str:
        return bucket_name or self.bucket_name

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchBucket"}:
                self.client.create_bucket(Bucket=bucket_name)
                return
            raise

    def upload_bytes(
        self,
        content: bytes,
        key: str,
        *,
        content_type: str | None = None,
        make_public: bool = True,
        bucket_name: str | None = None,
    ) -> str:
        bucket = self._resolve_bucket(bucket_name)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if make_public:
            extra_args["ACL"] = "public-read"

        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            **extra_args,
        )
        return self.build_public_url(key, bucket_name=bucket)

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        key: str,
        *,
        content_type: str | None = None,
        make_public: bool = True,
        bucket_name: str | None = None,
    ) -> str:
        bucket = self._resolve_bucket(bucket_name)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if make_public:
            extra_args["ACL"] = "public-read"

        kwargs = {
            "Fileobj": file_obj,
            "Bucket": bucket,
            "Key": key,
        }
        if extra_args:
            kwargs["ExtraArgs"] = extra_args

        self.client.upload_fileobj(**kwargs)
        return self.build_public_url(key, bucket_name=bucket)

    def delete(self, key: str, *, bucket_name: str | None = None) -> None:
        bucket = self._resolve_bucket(bucket_name)
        self.client.delete_object(Bucket=bucket, Key=key)

    def build_public_url(self, key: str, *, bucket_name: str | None = None) -> str:
        bucket = self._resolve_bucket(bucket_name)
        normalized_key = key.lstrip("/")
        return f"{self.endpoint_url}/{bucket}/{quote(normalized_key)}"

    def list_objects(self, prefix: str = "", *, bucket_name: str | None = None) -> list[dict]:
        bucket = self._resolve_bucket(bucket_name)
        objects: list[dict] = []
        continuation_token = None

        while True:
            kwargs = {
                "Bucket": bucket,
                "Prefix": prefix,
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            response = self.client.list_objects_v2(**kwargs)
            for obj in response.get("Contents", []):
                last_modified = obj.get("LastModified")
                if isinstance(last_modified, datetime):
                    last_modified_iso = last_modified.isoformat()
                else:
                    last_modified_iso = None

                objects.append(
                    {
                        "key": obj["Key"],
                        "size": obj.get("Size", 0),
                        "last_modified": last_modified_iso,
                    }
                )

            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")

        return objects


s3_service = S3Service()

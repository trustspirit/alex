from __future__ import annotations

import gzip
import json
import logging

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


class R2Client:
    """Thin wrapper around boto3 S3 client for Cloudflare R2."""

    def __init__(self, endpoint: str, access_key_id: str, secret_access_key: str, bucket: str) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
        )

    def upload(self, key: str, data: dict) -> None:
        body = gzip.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        self._client.put_object(Bucket=self._bucket, Key=key, Body=body)
        logger.info("Uploaded %s (%d bytes)", key, len(body))

    def download(self, key: str) -> dict:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        compressed = response["Body"].read()
        return json.loads(gzip.decompress(compressed))

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)
        logger.info("Deleted %s", key)

    def list_objects(self, prefix: str) -> list[str]:
        response = self._client.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
        contents = response.get("Contents", [])
        return [obj["Key"] for obj in contents]

    def test_connection(self) -> bool:
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return True
        except Exception as exc:
            logger.warning("R2 connection test failed: %s", exc)
            return False

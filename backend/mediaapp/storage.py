"""S3-compatible media storage backend (boto3) — selected via MEDIA_BACKEND=s3.

Objects stay private; reads go through presigned URLs so wardrobe/outfit photos
are never publicly enumerable (PRD §41 security posture).
"""
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class MediaS3Storage(Storage):
    """Drop-in Storage that persists uploads to S3 and serves presigned GETs."""

    def __init__(self):
        from django.conf import settings

        self._settings = settings
        self._bucket = settings.AWS_S3_BUCKET
        self._region = getattr(settings, "AWS_S3_REGION", "ap-south-1")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                region_name=self._region,
                aws_access_key_id=getattr(self._settings, "AWS_ACCESS_KEY_ID", ""),
                aws_secret_access_key=getattr(self._settings, "AWS_SECRET_ACCESS_KEY", ""),
            )
        return self._client

    # ---- write path ------------------------------------------------------

    def _save(self, name: str, content) -> str:
        name = self.get_available_name(name)
        body = content.read() if hasattr(content, "read") else bytes(content)
        self.client.put_object(
            Bucket=self._bucket, Key=name,
            Body=body,
            ContentType=getattr(content, "content_type", "application/octet-stream"),
        )
        return name

    def delete(self, name: str) -> None:
        try:
            self.client.delete_object(Bucket=self._bucket, Key=name)
        except Exception:  # noqa: BLE001 - deletion is best-effort
            pass

    def exists(self, name: str) -> bool:
        try:
            self.client.head_object(Bucket=self._bucket, Key=name)
            return True
        except Exception:  # noqa: BLE001
            return False

    def size(self, name: str) -> int:
        obj = self.client.head_object(Bucket=self._bucket, Key=name)
        return int(obj.get("ContentLength", 0))

    # ---- read path -------------------------------------------------------

    def url(self, name: str, parameters=None, expire=900, http_method=None) -> str:
        """Presigned URL — short-lived; no public bucket required."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": name},
            ExpiresIn=int(expire),
        )

    def _open(self, name: str, mode="rb"):
        obj = self.client.get_object(Bucket=self._bucket, Key=name)
        return ContentFile(obj["Body"].read(), name=name)

    def listdir(self, path: str):
        keys, prefixes = [], []
        response = self.client.list_objects_v2(Bucket=self._bucket, Prefix=path or "")
        for item in response.get("Contents", []):
            keys.append(item["Key"])
        for common in response.get("CommonPrefixes", []):
            prefixes.append(common["Prefix"])
        return prefixes, keys

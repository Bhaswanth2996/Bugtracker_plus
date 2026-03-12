from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()

try:
    from azure.storage.blob import BlobServiceClient
except Exception:  # pragma: no cover - optional dependency path at runtime.
    BlobServiceClient = None  # type: ignore


class AttachmentStorage:
    def __init__(self) -> None:
        self.local_root = Path(settings.local_upload_dir)
        self.local_root.mkdir(parents=True, exist_ok=True)
        self.blob_client = None
        if settings.azure_blob_connection_string and BlobServiceClient is not None:
            service = BlobServiceClient.from_connection_string(settings.azure_blob_connection_string)
            self.blob_client = service.get_container_client(settings.azure_blob_container_name)
            if not self.blob_client.exists():
                self.blob_client.create_container()

    async def save_file(self, upload: UploadFile) -> tuple[str, str]:
        file_id = str(uuid4())
        filename = upload.filename or "attachment.bin"
        content = await upload.read()
        if self.blob_client is not None:
            blob_name = f"{file_id}-{filename}"
            self.blob_client.upload_blob(blob_name, content, overwrite=True)
            return self.blob_client.url + "/" + blob_name, filename

        local_path = self.local_root / f"{file_id}-{filename}"
        local_path.write_bytes(content)
        return str(local_path), filename


storage = AttachmentStorage()

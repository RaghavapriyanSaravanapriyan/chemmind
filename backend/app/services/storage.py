import hashlib
import os
import uuid
import aiofiles
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import logger


class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_upload_file(
        self, workspace_id: str, upload_file: UploadFile
    ) -> tuple[str, str, int]:
        # Ensure workspace subdirectory exists
        ws_dir = os.path.join(self.base_dir, workspace_id)
        os.makedirs(ws_dir, exist_ok=True)

        # Generate unique filename to avoid collisions
        file_ext = os.path.splitext(upload_file.filename or "")[1].lower()
        if not file_ext:
            file_ext = ".pdf"

        unique_filename = f"{uuid.uuid4()}{file_ext}"
        target_path = os.path.join(ws_dir, unique_filename)

        sha256_hash = hashlib.sha256()
        file_size = 0

        async with aiofiles.open(target_path, "wb") as out_file:
            while chunk := await upload_file.read(1024 * 1024):
                file_size += len(chunk)
                sha256_hash.update(chunk)
                await out_file.write(chunk)

        checksum = sha256_hash.hexdigest()
        logger.info(f"Saved file {upload_file.filename} ({file_size} bytes) to {target_path}")
        return target_path, checksum, file_size

    def delete_file(self, storage_path: str) -> bool:
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
                logger.info(f"Deleted file from storage: {storage_path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to delete file {storage_path}: {str(e)}")
        return False


storage_service = StorageService()

"""MinIO object storage service"""

import io
from typing import BinaryIO, Optional
from datetime import timedelta

from minio import Minio
from minio.error import S3Error
import structlog

from app.core.config import settings
from app.core.exceptions import StorageError, ArtifactNotFoundError


logger = structlog.get_logger()


class StorageService:
    """Service for managing MinIO object storage operations"""
    
    def __init__(self):
        """Initialize MinIO client"""
        # Parse endpoint to remove http:// or https://
        endpoint = settings.s3_endpoint_url.replace("http://", "").replace("https://", "")
        
        self.client = Minio(
            endpoint,
            access_key=settings.s3_access_key_id,
            secret_key=settings.s3_secret_access_key,
            secure=settings.s3_use_ssl
        )
        self.bucket_name = settings.s3_bucket_name
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the configured bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info("Created MinIO bucket", bucket_name=self.bucket_name)
        except S3Error as e:
            logger.error("Failed to create bucket", error=str(e))
            raise StorageError(f"Failed to ensure bucket exists: {str(e)}")
    
    async def upload_file(
        self,
        file_path: str,
        file_obj: BinaryIO,
        file_size: int,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to MinIO storage
        
        Args:
            file_path: Path within bucket to store file
            file_obj: File object to upload
            file_size: Size of file in bytes
            content_type: MIME type of file
            metadata: Optional metadata to attach to object
            
        Returns:
            Storage path of uploaded file
            
        Raises:
            StorageError: If upload fails
        """
        try:
            # Reset file position
            file_obj.seek(0)
            
            # Prepare metadata
            object_metadata = metadata or {}
            
            # Upload to MinIO
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file_obj,
                length=file_size,
                content_type=content_type,
                metadata=object_metadata
            )
            
            logger.info(
                "File uploaded to storage",
                bucket=self.bucket_name,
                path=file_path,
                size=file_size,
                etag=result.etag
            )
            
            return file_path
            
        except S3Error as e:
            logger.error(
                "Failed to upload file to storage",
                error=str(e),
                path=file_path
            )
            raise StorageError(f"Failed to upload file: {str(e)}")
        except Exception as e:
            logger.error(
                "Unexpected error during file upload",
                error=str(e),
                path=file_path
            )
            raise StorageError(f"Unexpected error during upload: {str(e)}")
    
    async def download_file(self, file_path: str) -> BinaryIO:
        """
        Download file from MinIO storage
        
        Args:
            file_path: Path of file in bucket
            
        Returns:
            File object containing downloaded data
            
        Raises:
            ArtifactNotFoundError: If file not found
            StorageError: If download fails
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            
            # Read data into BytesIO
            file_data = io.BytesIO(response.read())
            file_data.seek(0)
            
            logger.info(
                "File downloaded from storage",
                bucket=self.bucket_name,
                path=file_path
            )
            
            return file_data
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ArtifactNotFoundError(file_path)
            logger.error(
                "Failed to download file from storage",
                error=str(e),
                path=file_path
            )
            raise StorageError(f"Failed to download file: {str(e)}")
        except Exception as e:
            logger.error(
                "Unexpected error during file download",
                error=str(e),
                path=file_path
            )
            raise StorageError(f"Unexpected error during download: {str(e)}")
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    async def delete_file(self, file_path: str) -> None:
        """
        Delete file from MinIO storage
        
        Args:
            file_path: Path of file to delete
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            
            logger.info(
                "File deleted from storage",
                bucket=self.bucket_name,
                path=file_path
            )
            
        except S3Error as e:
            logger.error(
                "Failed to delete file from storage",
                error=str(e),
                path=file_path
            )
            raise StorageError(f"Failed to delete file: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            file_path: Path of file to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            return True
        except S3Error:
            return False
    
    async def get_presigned_url(
        self,
        file_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate pre-signed URL for temporary file access
        
        Args:
            file_path: Path of file in bucket
            expires: URL expiration duration
            
        Returns:
            Pre-signed URL
            
        Raises:
            StorageError: If URL generation fails
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=expires
            )
            
            logger.info(
                "Generated pre-signed URL",
                bucket=self.bucket_name,
                path=file_path,
                expires_in=expires.total_seconds()
            )
            
            return url
            
        except S3Error as e:
            logger.error(
                "Failed to generate pre-signed URL",
                error=str(e),
                path=file_path
            )
            raise StorageError(f"Failed to generate pre-signed URL: {str(e)}")

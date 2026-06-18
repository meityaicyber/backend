import io
from minio import Minio
from minio.error import S3Error
from app.config import settings

def get_minio_client() -> Minio:
    # Ensure minio_url doesn't have http:// or https:// for minio client, it expects endpoint
    endpoint = settings.MINIO_URL.replace("http://", "").replace("https://", "")
    
    # We assume HTTP since we are in docker compose, adjust secure=False
    secure = settings.MINIO_URL.startswith("https://")
    
    client = Minio(
        endpoint,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=secure,
    )
    return client

def ensure_bucket_exists():
    client = get_minio_client()
    try:
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
    except S3Error as e:
        print(f"Error checking/creating bucket: {e}")

def upload_file(object_name: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    """Uploads bytes to MinIO and returns the object name."""
    client = get_minio_client()
    
    # ensure bucket exists (it should be created by minio-init, but good to be safe)
    ensure_bucket_exists()

    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
    return object_name

def get_file_stream(object_name: str):
    """Returns a stream of the file from MinIO. The caller must close it."""
    client = get_minio_client()
    try:
        response = client.get_object(settings.MINIO_BUCKET, object_name)
        return response
    except S3Error as e:
        raise Exception(f"Failed to get object from MinIO: {e}")

def delete_file(object_name: str) -> bool:
    """Deletes an object from MinIO."""
    client = get_minio_client()
    try:
        client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error as e:
        print(f"Error deleting object from MinIO: {e}")
        return False

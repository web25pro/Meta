"""AWS S3 client configuration for file storage"""
from typing import Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global S3 client
_s3_client: Optional[boto3.client] = None


def init_s3() -> None:
    """Initialize S3 client"""
    global _s3_client
    
    s3_config = Config(
        signature_version='s3v4',
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
    
    client_kwargs = {
        'service_name': 's3',
        'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        'region_name': settings.AWS_REGION,
        'config': s3_config,
    }
    
    # Support for MinIO or custom S3-compatible endpoints
    if settings.S3_ENDPOINT_URL:
        client_kwargs['endpoint_url'] = settings.S3_ENDPOINT_URL
    
    _s3_client = boto3.client(**client_kwargs)
    logger.info("S3 client initialized", extra={"bucket": settings.S3_BUCKET_NAME})


def get_s3_client() -> boto3.client:
    """
    Get S3 client instance.
    
    Returns:
        boto3.client: S3 client
        
    Raises:
        RuntimeError: If S3 is not initialized
    """
    if _s3_client is None:
        raise RuntimeError("S3 client not initialized. Call init_s3() first.")
    return _s3_client


def generate_presigned_url(
    key: str,
    expiration: int = 900,
    http_method: str = "GET"
) -> str:
    """
    Generate presigned URL for S3 object access.
    
    Args:
        key: S3 object key
        expiration: URL expiration time in seconds (default: 15 minutes)
        http_method: HTTP method (GET for download, PUT for upload)
        
    Returns:
        str: Presigned URL
        
    Raises:
        ClientError: If URL generation fails
    """
    client = get_s3_client()
    
    try:
        if http_method == "GET":
            url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expiration
            )
        elif http_method == "PUT":
            url = client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expiration
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {http_method}")
        
        return url
    except ClientError as e:
        logger.error("Failed to generate presigned URL", extra={
            "key": key,
            "error": str(e)
        })
        raise

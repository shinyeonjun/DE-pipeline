def upload_bytes(
    bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream"
) -> None:
    try:
        from google.cloud import storage
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-storage is required for GCS uploads. "
            "Install it or disable GCS by removing GCS_BUCKET."
        ) from exc

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(data, content_type=content_type)

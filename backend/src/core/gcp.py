"""
Google Cloud Platform credential loader
"""
import os
import json
from google.oauth2 import service_account


def load_gcp_credentials() -> service_account.Credentials:
    """
    Load GCP service account credentials from Docker secret

    Returns:
        service_account.Credentials: GCP credentials object

    Raises:
        FileNotFoundError: If service account key file not found
    """
    secret_path = "/app/secrets/gcp-sa-key.json"

    if not os.path.exists(secret_path):
        raise FileNotFoundError(
            f"GCP service account key not found at {secret_path}. "
            "Please mount secret in docker-compose.yml. "
            "See docs/setup-google-cloud.md for instructions."
        )

    if os.path.isdir(secret_path):
        raise IsADirectoryError(
            f"GCP service account key path is a directory, not a file: {secret_path}. "
            "Check docker-compose.yml volume mount - it should mount the JSON file directly, not the directory."
        )

    with open(secret_path, 'r') as f:
        credentials_info = json.load(f)

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info
    )

    return credentials

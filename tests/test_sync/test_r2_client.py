import gzip
import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_boto3_client():
    with patch("backend.sync.r2_client.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def r2_client(mock_boto3_client):
    from backend.sync.r2_client import R2Client
    return R2Client(
        endpoint="https://example.r2.cloudflarestorage.com",
        access_key_id="test-key",
        secret_access_key="test-secret",
        bucket="test-bucket",
    )


def test_upload_gzip_compressed(r2_client, mock_boto3_client):
    data = {"key": "value"}
    r2_client.upload("test/file.json.gz", data)
    call_args = mock_boto3_client.put_object.call_args
    body = call_args[1]["Body"] if "Body" in call_args[1] else call_args[0][0]
    decompressed = json.loads(gzip.decompress(body))
    assert decompressed == data


def test_download_decompresses(r2_client, mock_boto3_client):
    original = {"hello": "world"}
    compressed = gzip.compress(json.dumps(original).encode("utf-8"))
    mock_boto3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=compressed))
    }
    result = r2_client.download("test/file.json.gz")
    assert result == original


def test_delete_object(r2_client, mock_boto3_client):
    r2_client.delete("documents/abc.json.gz")
    mock_boto3_client.delete_object.assert_called_once_with(
        Bucket="test-bucket", Key="documents/abc.json.gz"
    )


def test_list_objects_with_prefix(r2_client, mock_boto3_client):
    mock_boto3_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "documents/a.json.gz"},
            {"Key": "documents/b.json.gz"},
        ]
    }
    result = r2_client.list_objects("documents/")
    assert result == ["documents/a.json.gz", "documents/b.json.gz"]


def test_list_objects_empty(r2_client, mock_boto3_client):
    mock_boto3_client.list_objects_v2.return_value = {}
    result = r2_client.list_objects("documents/")
    assert result == []


def test_test_connection_success(r2_client, mock_boto3_client):
    mock_boto3_client.head_bucket.return_value = {}
    assert r2_client.test_connection() is True


def test_test_connection_failure(r2_client, mock_boto3_client):
    mock_boto3_client.head_bucket.side_effect = Exception("Access Denied")
    assert r2_client.test_connection() is False

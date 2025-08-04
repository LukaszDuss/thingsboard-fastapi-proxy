"""
Unit tests for upload endpoints with mocked ThingsBoard responses.

These tests verify endpoint behavior, request validation, and response formatting
without requiring actual ThingsBoard connection.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import Response

from app.core.thingsboard import AuthError


class TestTelemetryUploadEndpoint:
    """Test cases for telemetry upload endpoint."""

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_upload_telemetry_success(self, mock_post, test_client, mock_device_id, sample_telemetry_data):
        """Test successful telemetry upload."""
        # Mock successful ThingsBoard response
        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            json=sample_telemetry_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["device_id"] == mock_device_id
        assert "temperature" in data["keys_uploaded"]
        assert "humidity" in data["keys_uploaded"]
        assert data["total_data_points"] == 3  # 2 temperature + 1 humidity

        # Verify ThingsBoard client was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert f"/api/plugins/telemetry/DEVICE/{mock_device_id}/timeseries/any" in call_args[0][0]

    def test_upload_telemetry_empty_data(self, test_client, mock_device_id):
        """Test telemetry upload with empty data."""
        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            json={}
        )

        assert response.status_code == 400
        assert "No telemetry data provided" in response.json()["detail"]

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_upload_telemetry_auth_error(self, mock_post, test_client, mock_device_id, sample_telemetry_data):
        """Test telemetry upload with authentication error."""
        mock_post.side_effect = AuthError("Authentication failed")

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            json=sample_telemetry_data
        )

        assert response.status_code == 502
        assert "Authentication failed" in response.json()["detail"]

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_upload_telemetry_upstream_error(self, mock_post, test_client, mock_device_id, sample_telemetry_data):
        """Test telemetry upload with upstream ThingsBoard error."""
        mock_post.side_effect = Exception("Network error")

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            json=sample_telemetry_data
        )

        assert response.status_code == 502
        assert "Upstream ThingsBoard error" in response.json()["detail"]

    def test_upload_telemetry_invalid_json(self, test_client, mock_device_id):
        """Test telemetry upload with invalid JSON structure."""
        # Invalid data structure - values should be arrays
        invalid_data = {
            "temperature": {"ts": 1609459200000, "value": 25.6}  # Should be array
        }

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            json=invalid_data
        )

        assert response.status_code == 422  # Validation error


class TestServerAttributesUploadEndpoint:
    """Test cases for server attributes upload endpoint."""

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_upload_server_attributes_success(self, mock_post, test_client, mock_device_id, sample_attributes):
        """Test successful server attributes upload."""
        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/attributes/server",
            json=sample_attributes
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["device_id"] == mock_device_id
        assert data["scope"] == "SERVER_SCOPE"
        assert data["count"] == len(sample_attributes)

        # Verify correct endpoint was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert f"/api/plugins/telemetry/DEVICE/{mock_device_id}/attributes/SERVER_SCOPE" in call_args[0][0]

    def test_upload_server_attributes_empty_data(self, test_client, mock_device_id):
        """Test server attributes upload with empty data."""
        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/attributes/server",
            json={}
        )

        assert response.status_code == 400
        assert "No attributes provided" in response.json()["detail"]


class TestSharedAttributesUploadEndpoint:
    """Test cases for shared attributes upload endpoint."""

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_upload_shared_attributes_success(self, mock_post, test_client, mock_device_id):
        """Test successful shared attributes upload."""
        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        shared_attributes = {
            "targetTemperature": 22.0,
            "operationMode": "AUTO",
            "alertThresholds": {
                "temperature": {"min": 10, "max": 35}
            }
        }

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/attributes/shared",
            json=shared_attributes
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["scope"] == "SHARED_SCOPE"
        assert data["count"] == len(shared_attributes)

        # Verify correct endpoint was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert f"/api/plugins/telemetry/DEVICE/{mock_device_id}/attributes/SHARED_SCOPE" in call_args[0][0]


class TestBulkTelemetryUploadEndpoint:
    """Test cases for bulk telemetry upload endpoint."""

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_bulk_upload_success(self, mock_post, test_client, sample_bulk_telemetry):
        """Test successful bulk telemetry upload."""
        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = test_client.post(
            "/api/v1/tb/telemetry/bulk",
            json=sample_bulk_telemetry
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["summary"]["total_devices"] == 2
        assert data["summary"]["successful_devices"] == 2
        assert data["summary"]["failed_devices"] == 0
        assert data["summary"]["total_data_points"] == 3  # 2 from device1 + 1 from device2

        # Verify both devices were processed
        assert len(data["results"]) == 2
        assert all(result["status"] == "success" for result in data["results"].values())

        # Verify ThingsBoard client was called twice (once per device)
        assert mock_post.call_count == 2

    @patch('app.api.v1.routes.tb_proxy.thingsboard_client.post')
    def test_bulk_upload_partial_failure(self, mock_post, test_client, sample_bulk_telemetry):
        """Test bulk upload with some devices failing."""
        # First call succeeds, second fails
        mock_post.side_effect = [
            AsyncMock(spec=Response),  # Success for first device
            Exception("Network error")  # Failure for second device
        ]
        mock_post.return_value.raise_for_status.return_value = None

        response = test_client.post(
            "/api/v1/tb/telemetry/bulk",
            json=sample_bulk_telemetry
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["summary"]["successful_devices"] == 1
        assert data["summary"]["failed_devices"] == 1

        # Check individual results
        results = data["results"]
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        failure_count = sum(1 for r in results.values() if r["status"] == "failed")
        assert success_count == 1
        assert failure_count == 1

    def test_bulk_upload_empty_data(self, test_client):
        """Test bulk upload with empty data."""
        response = test_client.post(
            "/api/v1/tb/telemetry/bulk",
            json={}
        )

        assert response.status_code == 400
        assert "No device data provided" in response.json()["detail"]


class TestEndpointInputValidation:
    """Test input validation across all upload endpoints."""

    def test_invalid_device_id_format(self, test_client):
        """Test behavior with invalid device ID format."""
        invalid_device_id = "not-a-uuid"
        
        response = test_client.post(
            f"/api/v1/tb/devices/{invalid_device_id}/telemetry",
            json={"temperature": [{"ts": 1609459200000, "value": 25.6}]}
        )
        
        # The endpoint doesn't validate UUID format, so this should pass validation
        # and potentially fail at ThingsBoard level
        assert response.status_code in [200, 502]  # Either success or upstream error

    def test_malformed_json_request(self, test_client, mock_device_id):
        """Test handling of malformed JSON in request body."""
        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, test_client, mock_device_id):
        """Test handling of missing required fields in telemetry data."""
        invalid_data = {
            "temperature": [
                {"ts": 1609459200000},  # Missing value
                {"value": 25.6}  # Missing ts
            ]
        }

        response = test_client.post(
            f"/api/v1/tb/devices/{mock_device_id}/telemetry",
            json=invalid_data
        )

        assert response.status_code == 422  # Validation error 
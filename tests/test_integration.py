"""
Integration tests for TB-API-SKD with actual ThingsBoard connection.

These tests require a running ThingsBoard instance and will test:
- Authentication and token management
- Device listing and discovery
- Upload functionality with real devices
- Error handling with actual upstream responses

NOTE: These tests should be run against a test/development ThingsBoard instance,
not production, as they may create test data.
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any

from app.core.thingsboard import thingsboard_client, AuthError
from app.core.config import settings


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestThingsBoardConnection:
    """Test basic ThingsBoard connectivity and authentication."""

    async def test_authentication(self, authenticated_tb_client):
        """Test that we can successfully authenticate with ThingsBoard."""
        # Make a simple request to verify authentication works
        response = await authenticated_tb_client.get("/api/auth/user")
        assert response.status_code == 200
        
        user_info = response.json()
        assert "email" in user_info
        assert user_info["email"] == settings.TB_USERNAME

    async def test_token_refresh_mechanism(self, authenticated_tb_client):
        """Test that token refresh works correctly."""
        # Force a token refresh by making multiple requests
        for _ in range(3):
            response = await authenticated_tb_client.get("/api/auth/user")
            assert response.status_code == 200
            await asyncio.sleep(0.1)  # Small delay between requests

    async def test_connection_settings(self):
        """Verify connection settings are correctly configured."""
        # Validate that settings are properly configured (not defaults)
        host_str = str(settings.TB_HOST).rstrip('/')
        assert host_str != "http://localhost", "TB_HOST should be configured to actual ThingsBoard instance"
        assert host_str.startswith(('http://', 'https://')), "TB_HOST must include protocol"
        
        assert settings.TB_USERNAME, "TB_USERNAME must be configured"
        assert "@" in settings.TB_USERNAME, "TB_USERNAME should be email format"
        
        assert settings.TB_PASSWORD, "TB_PASSWORD must be configured"
        # Don't log the password for security


class TestDeviceDiscovery:
    """Test device listing and discovery functionality."""

    async def test_list_devices(self, authenticated_tb_client):
        """Test listing devices from the tenant."""
        response = await authenticated_tb_client.get("/api/tenant/devices?page=0&pageSize=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "totalElements" in data
        assert isinstance(data["data"], list)
        
        print(f"Found {data['totalElements']} devices in tenant")
        
        return data["data"]  # Return devices for use in other tests

    async def test_list_assets(self, authenticated_tb_client):
        """Test listing assets from the tenant."""
        response = await authenticated_tb_client.get("/api/tenant/assets?page=0&pageSize=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        
        print(f"Found {data['totalElements']} assets in tenant")


class TestEndpointIntegration:
    """Test our SDK endpoints against real ThingsBoard."""



    async def test_sdk_health_endpoint(self, async_client):
        """Test that our SDK health endpoint works."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"

    async def test_sdk_list_devices(self, async_client):
        """Test our SDK device listing endpoint."""
        response = await async_client.get("/api/v1/tb/devices?page=0&pageSize=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    async def test_sdk_telemetry_keys(self, async_client, real_device_id):
        """Test our SDK telemetry keys endpoint with real device."""
        response = await async_client.get(f"/api/v1/tb/devices/{real_device_id}/keys")
        assert response.status_code == 200
        
        keys = response.json()
        assert isinstance(keys, list)
        print(f"Device has telemetry keys: {keys}")

    async def test_upload_telemetry_integration(self, async_client, real_device_id):
        """Test uploading telemetry data to a real device."""
        current_time = int(time.time() * 1000)  # Current timestamp in milliseconds
        
        telemetry_data = {
            "test_temperature": [
                {"ts": current_time, "value": 23.5}
            ],
            "test_integration": [
                {"ts": current_time, "value": "SDK_TEST"}
            ]
        }
        
        response = await async_client.post(
            f"/api/v1/tb/devices/{real_device_id}/telemetry",
            json=telemetry_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["device_id"] == real_device_id
        assert "test_temperature" in data["keys_uploaded"]
        assert "test_integration" in data["keys_uploaded"]
        assert data["total_data_points"] == 2

    async def test_upload_server_attributes_integration(self, async_client, real_device_id):
        """Test uploading server attributes to a real device."""
        attributes = {
            "test_serial": "SDK-TEST-001",
            "test_version": "1.0.0-integration",
            "test_timestamp": int(time.time()),
            "integration_test": True
        }
        
        response = await async_client.post(
            f"/api/v1/tb/devices/{real_device_id}/attributes/server",
            json=attributes
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["scope"] == "SERVER_SCOPE"
        assert data["count"] == len(attributes)

    async def test_upload_shared_attributes_integration(self, async_client, real_device_id):
        """Test uploading shared attributes to a real device."""
        attributes = {
            "test_target_temp": 22.0,
            "test_mode": "INTEGRATION_TEST",
            "test_thresholds": {
                "min": 10.0,
                "max": 35.0
            }
        }
        
        response = await async_client.post(
            f"/api/v1/tb/devices/{real_device_id}/attributes/shared",
            json=attributes
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["scope"] == "SHARED_SCOPE"
        assert data["count"] == len(attributes)

    async def test_bulk_telemetry_integration(self, async_client, real_device_id):
        """Test bulk telemetry upload with real device."""
        current_time = int(time.time() * 1000)
        
        bulk_data = {
            real_device_id: {
                "bulk_test_temp": [{"ts": current_time, "value": 25.0}],
                "bulk_test_status": [{"ts": current_time, "value": "ACTIVE"}]
            }
        }
        
        response = await async_client.post(
            "/api/v1/tb/telemetry/bulk",
            json=bulk_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["summary"]["total_devices"] == 1
        assert data["summary"]["successful_devices"] == 1
        assert data["summary"]["failed_devices"] == 0


class TestErrorHandling:
    """Test error handling with real ThingsBoard responses."""

    async def test_invalid_device_id(self, async_client):
        """Test uploading to non-existent device."""
        fake_device_id = "00000000-0000-0000-0000-000000000000"
        
        response = await async_client.post(
            f"/api/v1/tb/devices/{fake_device_id}/telemetry",
            json={"temperature": [{"ts": int(time.time() * 1000), "value": 25.0}]}
        )
        
        # This should fail at ThingsBoard level
        assert response.status_code == 502  # Upstream error

    async def test_malformed_telemetry_data(self, async_client, real_device_id):
        """Test uploading malformed telemetry data."""
        # Missing required 'ts' field
        invalid_data = {
            "temperature": [{"value": 25.0}]  # Missing timestamp
        }
        
        response = await async_client.post(
            f"/api/v1/tb/devices/{real_device_id}/telemetry",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error


class TestPerformance:
    """Basic performance tests for integration scenarios."""

    async def test_large_telemetry_upload(self, async_client, real_device_id):
        """Test uploading a larger batch of telemetry data."""
        current_time = int(time.time() * 1000)
        
        # Create 100 data points
        large_data = {
            "performance_test": [
                {"ts": current_time + i * 1000, "value": i * 0.1}
                for i in range(100)
            ]
        }
        
        start_time = time.time()
        response = await async_client.post(
            f"/api/v1/tb/devices/{real_device_id}/telemetry",
            json=large_data
        )
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_data_points"] == 100
        
        upload_time = end_time - start_time
        print(f"Uploaded 100 data points in {upload_time:.2f} seconds")
        
        # Should complete within 10 seconds for 100 points
        assert upload_time < 10.0

    @pytest.mark.skip(reason="Requires multiple test devices - enable if available")
    async def test_bulk_upload_performance(self, async_client, real_device_id):
        """Test bulk upload performance with multiple devices."""
        current_time = int(time.time() * 1000)
        
        # This would require multiple devices - skip for now
        bulk_data = {
            real_device_id: {
                "perf_test": [{"ts": current_time, "value": 1.0}]
            }
        }
        
        response = await async_client.post(
            "/api/v1/tb/telemetry/bulk",
            json=bulk_data
        )
        
        assert response.status_code == 200


# Helper function to run integration tests conditionally
def pytest_configure(config):
    """Configure pytest to add integration test marker."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires live ThingsBoard)"
    ) 
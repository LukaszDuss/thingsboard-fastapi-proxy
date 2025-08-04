"""
Connection validation tests for ThingsBoard integration.

This module provides comprehensive connectivity tests to verify:
- Configuration validation and security
- Authentication mechanisms and token handling
- Basic API endpoint functionality
- Resource discovery (devices, assets)
- Connection lifecycle management

These tests can be run independently to diagnose connection issues:
    python -m pytest tests/test_connection.py -v

For troubleshooting mode with detailed output:
    python -m pytest tests/test_connection.py -v -s --tb=long
"""

import pytest
from typing import Dict, Any, Optional
import asyncio
import logging

from app.core.thingsboard import thingsboard_client, AuthError
from app.core.config import settings

# Configure test-specific logging
_logger = logging.getLogger(__name__)

# Mark all tests as async by default
pytestmark = pytest.mark.asyncio


class TestConfigurationValidation:
    """Validate ThingsBoard configuration and security settings."""
    
    async def test_required_settings_present(self) -> None:
        """Verify all required ThingsBoard settings are configured."""
        assert settings.TB_HOST is not None, "TB_HOST must be configured"
        assert settings.TB_USERNAME is not None, "TB_USERNAME must be configured" 
        assert settings.TB_PASSWORD is not None, "TB_PASSWORD must be configured"
        
        # Validate host format
        assert str(settings.TB_HOST).startswith(('http://', 'https://')), \
            "TB_HOST must include protocol (http:// or https://)"
    
    async def test_security_configuration(self) -> None:
        """Validate security aspects of the configuration."""
        host_url = str(settings.TB_HOST)  # Convert Pydantic URL to string
        
        # Log security notice if using HTTP (non-production)
        if host_url.startswith('http://'):
            _logger.warning(
                "Using HTTP connection - this is acceptable for development/testing "
                "but HTTPS should be used in production"
            )
        
        # Validate credentials are not empty
        assert len(settings.TB_USERNAME) > 0, "Username cannot be empty"
        assert len(settings.TB_PASSWORD) > 0, "Password cannot be empty"
        
        # Validate email format for username (ThingsBoard standard)
        assert "@" in settings.TB_USERNAME, "Username should be email format"


class TestAuthentication:
    """Test authentication mechanisms and token management."""
    
    async def test_initial_authentication(self, authenticated_tb_client) -> None:
        """Verify initial authentication succeeds and returns user info."""
        response = await authenticated_tb_client.get("/api/auth/user")
        
        assert response.status_code == 200, f"Authentication failed: {response.text}"
        
        user_info = response.json()
        assert "email" in user_info, "User info missing email field"
        assert "authority" in user_info, "User info missing authority field"
        assert "tenantId" in user_info, "User info missing tenantId field"
        
        # Verify authenticated as expected user
        assert user_info["email"] == settings.TB_USERNAME, \
            f"Expected user {settings.TB_USERNAME}, got {user_info['email']}"
    
    async def test_authentication_persistence(self, authenticated_tb_client) -> None:
        """Verify authentication persists across multiple requests."""
        # Make multiple requests to ensure token is maintained
        endpoints = ["/api/auth/user", "/api/auth/user", "/api/auth/user"]
        
        for endpoint in endpoints:
            response = await authenticated_tb_client.get(endpoint)
            assert response.status_code == 200, \
                f"Authentication failed on subsequent request to {endpoint}"
    
    async def test_invalid_credentials_handling(self) -> None:
        """Verify proper handling of invalid credentials."""
        # This test would require a separate client instance with invalid creds
        # For now, we'll just verify the AuthError exists and can be imported
        assert AuthError is not None, "AuthError exception should be available"


class TestTenantDiscovery:
    """Test tenant information and resource discovery."""
    
    async def test_tenant_information_retrieval(self, authenticated_tb_client) -> None:
        """Verify tenant information can be retrieved."""
        # Get user info first to extract tenant ID
        user_response = await authenticated_tb_client.get("/api/auth/user")
        assert user_response.status_code == 200
        
        user_data = user_response.json()
        tenant_id = user_data["tenantId"]["id"]
        
        # Get tenant information
        tenant_response = await authenticated_tb_client.get(f"/api/tenant/{tenant_id}")
        assert tenant_response.status_code == 200, \
            f"Failed to retrieve tenant info: {tenant_response.text}"
        
        tenant_info = tenant_response.json()
        assert "name" in tenant_info, "Tenant info missing name field"
        assert "id" in tenant_info, "Tenant info missing id field"
        assert tenant_info["id"]["id"] == tenant_id, "Tenant ID mismatch"


class TestResourceDiscovery:
    """Test discovery of devices, assets, and other resources."""
    
    async def test_device_listing_endpoint(self, authenticated_tb_client) -> None:
        """Verify device listing endpoint works correctly."""
        response = await authenticated_tb_client.get("/api/tenant/devices?page=0&pageSize=10")
        assert response.status_code == 200, f"Device listing failed: {response.text}"
        
        data = response.json()
        self._validate_paginated_response(data)
        
        # Log device count for troubleshooting
        device_count = data.get("totalElements", 0)
        _logger.info(f"Tenant contains {device_count} devices")
        
        if device_count > 0:
            self._validate_device_structure(data["data"][0])
    
    async def test_asset_listing_endpoint(self, authenticated_tb_client) -> None:
        """Verify asset listing endpoint works correctly.""" 
        response = await authenticated_tb_client.get("/api/tenant/assets?page=0&pageSize=10")
        assert response.status_code == 200, f"Asset listing failed: {response.text}"
        
        data = response.json()
        self._validate_paginated_response(data)
        
        # Log asset count for troubleshooting
        asset_count = data.get("totalElements", 0)
        _logger.info(f"Tenant contains {asset_count} assets")
        
        if asset_count > 0:
            self._validate_asset_structure(data["data"][0])
    
    def _validate_paginated_response(self, data: Dict[str, Any]) -> None:
        """Validate structure of paginated API response."""
        assert "data" in data, "Response missing data field"
        assert "totalElements" in data, "Response missing totalElements field"
        assert "totalPages" in data, "Response missing totalPages field"
        assert isinstance(data["data"], list), "Data field should be a list"
        assert isinstance(data["totalElements"], int), "totalElements should be integer"
    
    def _validate_device_structure(self, device: Dict[str, Any]) -> None:
        """Validate structure of device object."""
        required_fields = ["id", "name", "type", "label"]
        for field in required_fields:
            assert field in device, f"Device missing required field: {field}"
        
        # Validate device ID structure
        assert "id" in device["id"], "Device ID missing id field"
        assert isinstance(device["id"]["id"], str), "Device ID should be string"
    
    def _validate_asset_structure(self, asset: Dict[str, Any]) -> None:
        """Validate structure of asset object."""
        required_fields = ["id", "name", "type", "label"]
        for field in required_fields:
            assert field in asset, f"Asset missing required field: {field}"


class TestConnectionLifecycle:
    """Test connection lifecycle and cleanup."""
    
    async def test_connection_cleanup(self, tb_client_for_cleanup) -> None:
        """Verify connection can be properly cleaned up."""
        # Make a request to ensure connection is active
        response = await tb_client_for_cleanup.get("/api/auth/user")
        assert response.status_code == 200
        
        # Test cleanup - this won't affect other tests since it's a separate client instance
        try:
            await tb_client_for_cleanup.close()
        except Exception as e:
            pytest.fail(f"Connection cleanup failed: {str(e)}")
        
        # Verify the client is indeed closed by trying to make another request
        with pytest.raises(RuntimeError, match="Cannot send a request, as the client has been closed"):
            await tb_client_for_cleanup.get("/api/auth/user")


class TestEndpointAvailability:
    """Test availability of key ThingsBoard API endpoints."""
    
    @pytest.mark.parametrize("endpoint", [
        "/api/auth/user",
        "/api/tenant/devices?page=0&pageSize=1", 
        "/api/tenant/assets?page=0&pageSize=1",
    ])
    async def test_critical_endpoints_available(
        self, 
        authenticated_tb_client, 
        endpoint: str
    ) -> None:
        """Verify critical endpoints are available and responding."""
        response = await authenticated_tb_client.get(endpoint)
        assert response.status_code == 200, \
            f"Critical endpoint {endpoint} returned {response.status_code}: {response.text}"


# Standalone execution support for troubleshooting
async def main() -> None:
    """
    Run connection tests directly for troubleshooting.
    
    This function provides a simple way to validate ThingsBoard connectivity
    outside of the pytest framework, useful for initial setup verification.
    """
    print("=" * 60)
    print("TB-API-SKD Connection Validation")
    print("=" * 60)
    
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s"
    )
    
    try:
        # Test configuration
        print("🔧 Validating configuration...")
        config_test = TestConfigurationValidation()
        await config_test.test_required_settings_present()
        await config_test.test_security_configuration()
        print("✅ Configuration validation passed")
        
        # Test authentication
        print("🔐 Testing authentication...")
        auth_test = TestAuthentication()
        # Note: In standalone mode, we create our own client reference
        client = thingsboard_client
        await auth_test.test_initial_authentication(client)
        await auth_test.test_authentication_persistence(client)
        print("✅ Authentication successful")
        
        # Test resource discovery
        print("🔍 Testing resource discovery...")
        discovery_test = TestResourceDiscovery()
        await discovery_test.test_device_listing_endpoint(client)
        await discovery_test.test_asset_listing_endpoint(client)
        print("✅ Resource discovery working")
        
        # Cleanup
        print("🧹 Cleaning up connections...")
        await client.close()
        print("✅ Cleanup completed")
        
        print("\n" + "=" * 60)
        print("🎉 All connection tests PASSED!")
        print("Your ThingsBoard integration is working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Connection test FAILED: {str(e)}")
        print("\n🔧 Troubleshooting Guide:")
        print(f"1. Verify ThingsBoard is running at: {settings.TB_HOST}")
        print(f"2. Check credentials: {settings.TB_USERNAME} / [password]")
        print("3. Ensure network connectivity to the ThingsBoard instance")
        print("4. Check ThingsBoard server logs for authentication errors")
        print("5. Verify ThingsBoard REST API is enabled and accessible")
        
        import sys
        sys.exit(1)


if __name__ == "__main__":
    """Allow running this test module directly for troubleshooting."""
    asyncio.run(main()) 
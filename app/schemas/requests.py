"""
Request schemas for API endpoints.

Comprehensive Pydantic models for request validation with detailed examples
and field descriptions following OpenAPI best practices.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TelemetryDataPoint(BaseModel):
    """
    Represents a single telemetry data point with timestamp and value.
    
    Used for uploading time-series data to ThingsBoard devices.
    Timestamps should be in milliseconds since Unix epoch.
    """
    ts: int = Field(
        ..., 
        description="Timestamp in milliseconds since Unix epoch",
        example=1640995200000,
        ge=0
    )
    value: Union[str, int, float, bool] = Field(
        ..., 
        description="Telemetry value - can be numeric, boolean, or string",
        example=25.6
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"ts": 1640995200000, "value": 25.6},
                {"ts": 1640995200000, "value": "ON"},
                {"ts": 1640995200000, "value": True},
                {"ts": 1640995200000, "value": "Running"}
            ]
        }
    }


class TelemetryUploadRequest(BaseModel):
    """
    Request model for uploading telemetry data to a device.
    
    Maps telemetry key names to arrays of timestamped values.
    Each key can have multiple data points with different timestamps.
    """
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "temperature": [
                    {"ts": 1640995200000, "value": 25.6},
                    {"ts": 1640995260000, "value": 26.1},
                    {"ts": 1640995320000, "value": 25.8}
                ],
                "humidity": [
                    {"ts": 1640995200000, "value": 60.2},
                    {"ts": 1640995260000, "value": 61.5}
                ],
                "status": [
                    {"ts": 1640995200000, "value": "ACTIVE"}
                ]
            }
        }
    }
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_telemetry_data(cls, v):
        """Ensure all values are lists of TelemetryDataPoint objects."""
        if not isinstance(v, list):
            raise ValueError("Telemetry values must be arrays of data points")
        return v


class AttributesUploadRequest(BaseModel):
    """
    Request model for uploading attributes to a device.
    
    Simple key-value pairs representing device properties, metadata,
    or configuration values. Attributes are persistent and don't have timestamps.
    """
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "examples": [
                {
                    "serialNumber": "SN001234",
                    "firmwareVersion": "1.2.3",
                    "model": "TempSensor-Pro",
                    "location": "Building A, Floor 2",
                    "calibrationDate": "2024-01-15",
                    "maintenanceSchedule": "quarterly"
                },
                {
                    "targetTemperature": 22.0,
                    "operationMode": "AUTO",
                    "alertEnabled": True,
                    "thresholds": {
                        "temperature": {"min": 10, "max": 35},
                        "humidity": {"min": 30, "max": 80}
                    }
                }
            ]
        }
    }


class TelemetryKeysRequest(BaseModel):
    """Request model for specifying which telemetry keys to retrieve."""
    keys: List[str] = Field(
        ..., 
        description="List of telemetry keys to retrieve",
        min_length=1,
        example=["temperature", "humidity", "pressure"]
    )
    limit: Optional[int] = Field(
        default=100, 
        description="Maximum number of data points per key",
        ge=1, 
        le=1000,
        example=500
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keys": ["temperature", "humidity"],
                    "limit": 100
                },
                {
                    "keys": ["pressure", "windSpeed", "windDirection"],
                    "limit": 500
                },
                {
                    "keys": ["voltage", "current", "power"],
                    "limit": 1000
                }
            ]
        }
    }


class TelemetryHistoryRequest(BaseModel):
    """
    Request model for historical telemetry data with flexible time filtering.
    
    Supports time range queries, data limits, and aggregation intervals.
    If time range is not specified, defaults to last 24 hours.
    """
    keys: List[str] = Field(
        ..., 
        description="List of telemetry keys to retrieve",
        min_length=1,
        example=["temperature", "humidity"]
    )
    start_ts: Optional[int] = Field(
        default=None, 
        description="Start timestamp in milliseconds (optional, defaults to 24 hours ago)",
        ge=0,
        example=1640908800000
    )
    end_ts: Optional[int] = Field(
        default=None, 
        description="End timestamp in milliseconds (optional, defaults to now)",
        ge=0,
        example=1640995200000
    )
    limit: Optional[int] = Field(
        default=100, 
        description="Maximum data points per key",
        ge=1, 
        le=1000,
        example=200
    )
    interval: Optional[int] = Field(
        default=None, 
        description="Aggregation interval in milliseconds (optional)",
        ge=1000,
        example=300000
    )
    
    @field_validator('end_ts')
    @classmethod
    def validate_time_range(cls, v, info):
        """Ensure end_ts is after start_ts if both are provided."""
        if v is not None and info.data.get('start_ts') is not None:
            if v <= info.data['start_ts']:
                raise ValueError('end_ts must be greater than start_ts')
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keys": ["temperature", "humidity"],
                    "start_ts": 1640908800000,
                    "end_ts": 1640995200000,
                    "limit": 200
                },
                {
                    "keys": ["pressure", "windSpeed"],
                    "start_ts": 1640908800000,
                    "end_ts": 1640995200000,
                    "limit": 500,
                    "interval": 300000
                },
                {
                    "keys": ["voltage", "current"],
                    "limit": 1000
                }
            ]
        }
    }


class BulkTelemetryRequest(BaseModel):
    """
    Request model for bulk telemetry upload to multiple devices.
    
    Maps device UUIDs to their respective telemetry data.
    Useful for batch processing scenarios.
    """
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "550e8400-e29b-41d4-a716-446655440000": {
                    "temperature": [
                        {"ts": 1640995200000, "value": 25.6}
                    ],
                    "humidity": [
                        {"ts": 1640995200000, "value": 60.2}
                    ]
                },
                "550e8400-e29b-41d4-a716-446655440001": {
                    "pressure": [
                        {"ts": 1640995200000, "value": 1013.25}
                    ],
                    "windSpeed": [
                        {"ts": 1640995200000, "value": 12.5}
                    ]
                }
            }
        }
    }


class DeviceQueryParams(BaseModel):
    """Query parameters for device listing endpoint."""
    page: int = Field(
        default=0,
        description="Zero-based page index",
        ge=0,
        example=0
    )
    page_size: int = Field(
        default=100,
        description="Number of items per page (max 1000)",
        ge=1,
        le=1000,
        example=100
    )
    text_search: Optional[str] = Field(
        default=None,
        description="Optional device name filter",
        max_length=255,
        example="Temperature Sensor"
    )
    device_type: Optional[str] = Field(
        default=None,
        description="Optional device type filter (device profile name)",
        max_length=255,
        example="TemperatureSensor"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 0,
                    "page_size": 50,
                    "text_search": "Building A",
                    "device_type": "TemperatureSensor"
                },
                {
                    "page": 1,
                    "page_size": 100
                }
            ]
        }
    }


class AssetQueryParams(BaseModel):
    """Query parameters for asset listing endpoint."""
    page: int = Field(
        default=0,
        description="Zero-based page index",
        ge=0,
        example=0
    )
    page_size: int = Field(
        default=100,
        description="Number of items per page (max 1000)",
        ge=1,
        le=1000,
        example=100
    )
    text_search: Optional[str] = Field(
        default=None,
        description="Optional asset name filter",
        max_length=255,
        example="Building"
    )
    asset_type: Optional[str] = Field(
        default=None,
        description="Optional asset type filter (asset profile name)",
        max_length=255,
        example="BuildingAsset"
    )


class EntityGraphParams(BaseModel):
    """Query parameters for entity relationship graph endpoint."""
    root_type: str = Field(
        default="DEVICE",
        description="Entity type of the root node",
        example="DEVICE"
    )
    max_depth: int = Field(
        default=2,
        description="Maximum relationship traversal depth",
        ge=0,
        le=10,
        example=3
    )
    direction: str = Field(
        default="BOTH",
        description="Relationship direction to follow",
        pattern="^(FROM|TO|BOTH)$",
        example="BOTH"
    )
    types: Optional[str] = Field(
        default=None,
        description="Comma-separated list of entity types to include",
        example="DEVICE,ASSET"
    )
    hard_node_limit: int = Field(
        default=500,
        description="Maximum number of nodes to return",
        ge=1,
        le=1000,
        example=500
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "root_type": "DEVICE",
                    "max_depth": 2,
                    "direction": "BOTH",
                    "types": "DEVICE,ASSET",
                    "hard_node_limit": 100
                },
                {
                    "root_type": "ASSET",
                    "max_depth": 3,
                    "direction": "FROM",
                    "hard_node_limit": 500
                }
            ]
        }
    }
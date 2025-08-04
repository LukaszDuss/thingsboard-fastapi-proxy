from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
import csv
import io
import logging
import time

from app.core.thingsboard import thingsboard_client, AuthError
from app.core.auth import AuthenticatedUser, ValidAPIKey
from app.schemas.requests import (
    TelemetryDataPoint, 
    TelemetryUploadRequest,
    AttributesUploadRequest, 
    TelemetryHistoryRequest,
    BulkTelemetryRequest
)
from app.schemas.responses import (
    TelemetryUploadResponse,
    AttributesUploadResponse,
    TelemetryQueryResponse,
    TelemetryLatestResponse,
    BulkUploadResponse,
    DeviceListResponse,
    ErrorResponse
)
from collections import deque
from typing import Literal, Set, List

router = APIRouter(prefix="/tb", tags=["thingsboard"])
logger = logging.getLogger(__name__)

# valid entity types we expose
EntityType = Literal["DEVICE", "ASSET", "ASSET_PROFILE", "DEVICE_PROFILE"]

MAX_TB_LIMIT = 1000  # ThingsBoard will not return more than 1000 datapoints per key per call


# ---------------------------------------------------------------------------
# Pydantic Models for Telemetry Requests
# ---------------------------------------------------------------------------

class TelemetryKeysRequest(BaseModel):
    """
    Request model for specifying which telemetry keys to retrieve.
    
    Example:
        {
            "keys": ["temperature", "humidity", "pressure"],
            "limit": 100
        }
    """
    keys: List[str] = Field(..., description="List of telemetry keys to retrieve", min_items=1)
    limit: Optional[int] = Field(default=100, description="Maximum number of data points per key", ge=1, le=1000)


class TelemetryHistoryRequest(BaseModel):
    """
    Request model for historical telemetry data with flexible time filtering.
    
    Example:
        {
            "keys": ["temperature", "humidity"],
            "start_ts": 1609459200000,
            "end_ts": 1609545600000,
            "limit": 500,
            "interval": 3600000
        }
    """
    keys: List[str] = Field(..., description="List of telemetry keys to retrieve", min_items=1)
    start_ts: Optional[int] = Field(default=None, description="Start timestamp in milliseconds (optional)")
    end_ts: Optional[int] = Field(default=None, description="End timestamp in milliseconds (optional)")
    limit: Optional[int] = Field(default=100, description="Maximum data points per key", ge=1, le=1000)
    interval: Optional[int] = Field(default=None, description="Aggregation interval in milliseconds (optional)")


# ---------------------------------------------------------------------------
# Pydantic Models for Upload Requests
# ---------------------------------------------------------------------------

class TelemetryDataPoint(BaseModel):
    """
    Represents a single telemetry data point with timestamp and value.
    
    Examples:
        - {"ts": 1609459200000, "value": 25.6}  # Temperature reading
        - {"ts": 1609459200000, "value": "ON"}   # Switch state
    """
    ts: int = Field(..., description="Timestamp in milliseconds since epoch")
    value: Union[str, int, float, bool] = Field(..., description="Telemetry value")


class TelemetryUploadRequest(BaseModel):
    """
    Request model for uploading telemetry data to a device.
    Maps telemetry key names to arrays of timestamped values.
    
    Example:
        {
            "temperature": [
                {"ts": 1609459200000, "value": 25.6},
                {"ts": 1609459260000, "value": 26.1}
            ],
            "humidity": [
                {"ts": 1609459200000, "value": 60.2}
            ]
        }
    """
    model_config = {"extra": "allow"}  # Allow additional telemetry keys
    
    def __getitem__(self, key: str) -> List[TelemetryDataPoint]:
        """Allow dict-like access to telemetry keys."""
        return getattr(self, key, [])


class AttributesUploadRequest(BaseModel):
    """
    Request model for uploading attributes to a device.
    Simple key-value pairs representing device properties/metadata.
    
    Example:
        {
            "serialNumber": "SN001234",
            "firmwareVersion": "1.2.3",
            "model": "TempSensor-Pro",
            "location": "Building A, Floor 2"
        }
    """
    model_config = {"extra": "allow"}  # Allow any attribute keys
    
    def dict_extra(self) -> Dict[str, Any]:
        """Return all attributes as a dictionary."""
        return {k: v for k, v in self.__dict__.items()}


class BulkTelemetryRequest(BaseModel):
    """
    Request model for bulk telemetry upload to multiple devices.
    
    Example:
        {
            "device1_uuid": {
                "temperature": [{"ts": 1609459200000, "value": 25.6}]
            },
            "device2_uuid": {
                "pressure": [{"ts": 1609459200000, "value": 1013.25}]
            }
        }
    """
    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Read-only endpoints (require authentication but not write permissions)
# ---------------------------------------------------------------------------

@router.get("/devices/{device_id}/keys")
async def list_telemetry_keys(
    device_id: str,
    authenticated: ValidAPIKey
):
    """Return list of time-series keys available for a given device."""
    try:
        resp = await thingsboard_client.get(f"/api/plugins/telemetry/DEVICE/{device_id}/keys/timeseries")
        resp.raise_for_status()
        logger.info(f"Listed telemetry keys for device {device_id}")
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error listing keys for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc
    return resp.json()


@router.get("/devices")
async def list_devices(
    authenticated: ValidAPIKey,
    page: int = 0,
    page_size: int = 100,
    text_search: str | None = None,
    device_type: str | None = None
):
    """Return paginated list of devices for current tenant.

    Mirrors ThingsBoard endpoint `/api/tenant/devices`.
    Query params:
      * `page` – zero-based page index.
      * `page_size` – number of items per page (max 1000 as per TB default).
      * `text_search` – optional name filter.
      * `device_type` – optional device type filter (e.g., "TemperatureSensor", "Gateway").
    """
    params: dict[str, str | int] = {"page": page, "pageSize": page_size}
    if text_search:
        params["textSearch"] = text_search
    if device_type:
        params["type"] = device_type

    try:
        resp = await thingsboard_client.get("/api/tenant/devices", params=params)
        resp.raise_for_status()
        logger.info(f"Listed devices: page={page}, size={page_size}, type={device_type}")
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error listing devices: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error listing devices: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc

    return resp.json()


@router.get("/device-types")
async def list_device_types(
    authenticated: ValidAPIKey,
    page: int = 0,
    page_size: int = 100
):
    """Return paginated list of device types (device profiles) for current tenant.
    
    This endpoint helps discover available device types that can be used
    for filtering in the `/devices` endpoint.
    
    **Example Response:**
    ```json
    {
        "data": [
            {
                "id": {"id": "uuid", "entityType": "DEVICE_PROFILE"},
                "name": "TemperatureSensor",
                "type": "DEFAULT",
                "description": "Temperature sensor device profile"
            }
        ],
        "totalPages": 1,
        "totalElements": 5,
        "hasNext": false
    }
    ```
    """
    params: dict[str, str | int] = {"page": page, "pageSize": page_size}
    
    try:
        resp = await thingsboard_client.get("/api/deviceProfiles", params=params)
        resp.raise_for_status()
        logger.info(f"Listed device types: page={page}, size={page_size}")
        return resp.json()
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error listing device types: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error listing device types: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


@router.get("/assets")
async def list_assets(
    authenticated: ValidAPIKey,
    page: int = 0,
    page_size: int = 100,
    text_search: str | None = None,
    asset_type: str | None = None
):
    """Return paginated list of assets for current tenant.
    Mirrors ThingsBoard `/api/tenant/assets`.
    Optional `asset_type` filters by asset profile name.
    """
    params: dict[str, str | int] = {"page": page, "pageSize": page_size}
    if text_search:
        params["textSearch"] = text_search
    if asset_type:
        params["type"] = asset_type

    try:
        resp = await thingsboard_client.get("/api/tenant/assets", params=params)
        resp.raise_for_status()
        logger.info(f"Listed assets: page={page}, size={page_size}, type={asset_type}")
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error listing assets: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error listing assets: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc

    return resp.json()


@router.get("/asset-types")
async def list_asset_types(
    authenticated: ValidAPIKey,
    page: int = 0,
    page_size: int = 100
):
    """Return paginated list of asset types (asset profiles) for current tenant.
    
    This endpoint helps discover available asset types that can be used
    for filtering in the `/assets` endpoint.
    
    **Example Response:**
    ```json
    {
        "data": [
            {
                "id": {"id": "uuid", "entityType": "ASSET_PROFILE"},
                "name": "Building",
                "description": "Building asset profile",
                "default": false
            },
            {
                "id": {"id": "uuid", "entityType": "ASSET_PROFILE"},
                "name": "Factory",
                "description": "Manufacturing facility profile", 
                "default": false
            }
        ],
        "totalPages": 1,
        "totalElements": 3,
        "hasNext": false
    }
    ```
    
    **Use Case:**
    Use this endpoint to discover what asset types are available in your ThingsBoard tenant,
    then use those names in the `asset_type` parameter of the `/assets` endpoint.
    """
    params: dict[str, str | int] = {"page": page, "pageSize": page_size}
    
    try:
        resp = await thingsboard_client.get("/api/assetProfiles", params=params)
        resp.raise_for_status()
        logger.info(f"Listed asset types: page={page}, size={page_size}")
        return resp.json()
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error listing asset types: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error listing asset types: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


@router.get("/graph/{root_id}")
async def entity_graph(
    root_id: str,
    authenticated: ValidAPIKey,
    root_type: EntityType = "DEVICE",
    max_depth: int = 2,
    direction: Literal["FROM", "TO", "BOTH"] = "BOTH",
    types: str | None = None,
    hard_node_limit: int = 500
):
    """Breadth-first relation crawl starting from *root_id*.

    Returns nodes + edges suitable for UI graph rendering.
    """
    if max_depth < 0:
        raise HTTPException(400, detail="max_depth must be >= 0")

    allowed_types: Set[str] | None = None
    if types:
        allowed_types = {t.strip().upper() for t in types.split(",") if t}

    # BFS
    queue: deque[tuple[str, str, int]] = deque()
    queue.append((root_id, root_type, 0))

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    visited: Set[str] = set()

    while queue and len(nodes) < hard_node_limit:
        entity_id, entity_type, depth = queue.popleft()
        if entity_id in visited:
            continue
        visited.add(entity_id)

        # fetch name for the node (single call per entity)
        try:
            info_resp = await thingsboard_client.get(f"/api/entityInfo/{entity_id}")
            info_resp.raise_for_status()
            info = info_resp.json()
            entity_name = info.get("name", "unknown")
        except Exception:  # pylint: disable=broad-except
            entity_name = "unknown"

        nodes[entity_id] = {
            "id": entity_id,
            "type": entity_type,
            "name": entity_name,
            "depth": depth,
        }

        if depth >= max_depth:
            continue

        # fetch relations from this node
        params = {
            "fromId": entity_id,
            "fromType": entity_type,
            "direction": direction,
        }
        try:
            rel_resp = await thingsboard_client.get(
                "/api/relations/info", params=params
            )
            rel_resp.raise_for_status()
            relations = rel_resp.json()
        except AuthError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:  # pylint: disable=broad-except
            raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc

        for rel in relations:
            to_id = rel["toId"].get("id")
            to_type = rel["toId"].get("entityType")
            edge_type = rel.get("type")
            if not to_id or not to_type:
                continue

            edges.append({
                "from": entity_id,
                "to": to_id,
                "relation_type": edge_type,
            })

            # only enqueue if limit not reached
            if len(nodes) + len(queue) >= hard_node_limit:
                continue
            queue.append((to_id, to_type, depth + 1))

    # filter nodes if requested
    if allowed_types is not None:
        nodes = {nid: n for nid, n in nodes.items() if n["type"] in allowed_types}
        edges = [e for e in edges if e["from"] in nodes and e["to"] in nodes]

    return {"root": root_id, "nodes": list(nodes.values()), "edges": edges, "depth": max_depth}


@router.get("/devices/{device_id}/telemetry")
async def get_device_telemetry(
    device_id: str,
    keys: str,
    start_ts: int,
    end_ts: int,
    authenticated: ValidAPIKey,
    format: Literal["json", "csv", "jsonl", "xlsx"] = "json"
):
    """Fetch *all* telemetry datapoints between `start_ts` and `end_ts`.

    ThingsBoard caps each call at 1 000 points; this handler paginates
    until the full interval is read.  The merged result can be returned
    as:

    * `json`  – identical structure to TB but unlimited length.
    * `csv`   – streamed, columns `ts,key,value`.
    * `jsonl` – newline-delimited JSON (`{"ts":…, "key":…, "value":…}` per line).
    * `xlsx`  – Excel workbook with one sheet per key (requires `pandas`).
    """

    key_list: List[str] = [k.strip() for k in keys.split(",") if k]
    if not key_list:
        raise HTTPException(400, detail="keys query parameter required")

    aggregated: dict[str, list[dict]] = {k: [] for k in key_list}

    for key in key_list:
        next_start = start_ts
        while True:
            params = {
                "keys": key,
                "startTs": next_start,
                "endTs": end_ts,
                "limit": MAX_TB_LIMIT,
            }
            try:
                resp = await thingsboard_client.get(
                    f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
                    params=params,
                )
                resp.raise_for_status()
            except AuthError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            except Exception:  # pylint: disable=broad-except
                raise HTTPException(status_code=502, detail="Upstream ThingsBoard error")

            chunk = resp.json().get(key, [])
            if not chunk:
                break
            aggregated[key].extend(chunk)
            if len(chunk) < MAX_TB_LIMIT:
                break  # last page
            next_start = chunk[-1]["ts"] + 1  # type: ignore[index]

    # ---------- Serialization ----------
    if format == "json":
        return JSONResponse(content=aggregated)

    if format == "csv":
        def csv_generator():
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["ts", "key", "value"])
            for k, datapoints in aggregated.items():
                for dp in datapoints:
                    writer.writerow([dp["ts"], k, dp["value"]])
            buffer.seek(0)
            yield buffer.getvalue()

        return StreamingResponse(
            csv_generator(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={device_id}_telemetry.csv"},
        )

    if format == "jsonl":
        def jsonl_generator():
            for k, datapoints in aggregated.items():
                for dp in datapoints:
                    yield f"{{\"ts\":{dp['ts']},\"key\":\"{k}\",\"value\":{dp['value']} }}\n"

        return StreamingResponse(jsonl_generator(), media_type="application/json-lines")

    if format == "xlsx":
        try:
            import pandas as pd  # type: ignore
        except ImportError:  # pragma: no cover
            raise HTTPException(500, detail="xlsx format requires pandas dependency")

        # build DataFrames per key
        xls_buffer = io.BytesIO()
        with pd.ExcelWriter(xls_buffer, engine="xlsxwriter") as writer:  # type: ignore
            for k, datapoints in aggregated.items():
                df = pd.DataFrame(datapoints)
                if not df.empty:
                    df.rename(columns={"ts": "timestamp"}, inplace=True)
                df.to_excel(writer, index=False, sheet_name=k[:31])

        xls_buffer.seek(0)
        return StreamingResponse(
            xls_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={device_id}_telemetry.xlsx"},
        )

        raise HTTPException(400, detail="Unsupported format")


@router.get("/devices/{device_id}/telemetry/latest")
async def get_latest_telemetry(
    device_id: str,
    keys: str,
    authenticated: ValidAPIKey
):
    """
    Get the latest telemetry values for specified keys from a device.
    
    This endpoint returns only the most recent value for each specified telemetry key,
    making it ideal for dashboard displays and current status monitoring.
    
    **Parameters:**
    - `device_id`: UUID of the target device
    - `keys`: Comma-separated list of telemetry keys (e.g., "temperature,humidity,pressure")
    
    **Example Request:**
    ```
    GET /api/v1/tb/devices/550e8400-e29b-41d4-a716-446655440000/telemetry/latest?keys=temperature,humidity
    ```
    
    **Example Response:**
    ```json
    {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": 1640995200000,
        "data": {
            "temperature": {"ts": 1640995200000, "value": 23.5},
            "humidity": {"ts": 1640995180000, "value": 65.2}
        }
    }
    ```
    """
    key_list: List[str] = [k.strip() for k in keys.split(",") if k.strip()]
    if not key_list:
        raise HTTPException(400, detail="At least one telemetry key must be specified")
    
    try:
        # Get latest values for all keys in one request
        params = {"keys": ",".join(key_list)}
        resp = await thingsboard_client.get(
            f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
            params=params
        )
        resp.raise_for_status()
        
        data = resp.json()
        logger.info(f"Retrieved latest telemetry for device {device_id}, keys: {key_list}")
        
        # Extract latest values and find the most recent timestamp
        latest_data = {}
        latest_timestamp = 0
        
        for key in key_list:
            key_data = data.get(key, [])
            if key_data:
                latest_value = key_data[0]  # ThingsBoard returns latest first
                latest_data[key] = latest_value
                latest_timestamp = max(latest_timestamp, latest_value["ts"])
            else:
                latest_data[key] = None
        
        return {
            "device_id": device_id,
            "timestamp": latest_timestamp,
            "keys_requested": key_list,
            "data": latest_data
        }
        
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:
        logger.error(f"Error retrieving latest telemetry for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


@router.post("/devices/{device_id}/telemetry/query")
async def query_device_telemetry(
    device_id: str,
    query: TelemetryHistoryRequest,
    authenticated: ValidAPIKey
):
    """
    Query historical telemetry data for specified keys with flexible filtering.
    
    This endpoint provides more flexible querying options compared to the basic telemetry endpoint:
    - Optional time range (defaults to last 24 hours if not specified)
    - Configurable limit per key
    - Support for aggregation intervals
    - JSON request body for complex queries
    
    **Example Request:**
    ```json
    {
        "keys": ["temperature", "humidity", "pressure"],
        "start_ts": 1640908800000,
        "end_ts": 1640995200000,
        "limit": 200,
        "interval": 300000
    }
    ```
    
    **Example Response:**
    ```json
    {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "query": {
            "keys": ["temperature", "humidity"],
            "start_ts": 1640908800000,
            "end_ts": 1640995200000,
            "limit": 200
        },
        "data": {
            "temperature": [
                {"ts": 1640995200000, "value": 23.5},
                {"ts": 1640995100000, "value": 23.3}
            ],
            "humidity": [
                {"ts": 1640995200000, "value": 65.2},
                {"ts": 1640995100000, "value": 64.8}
            ]
        },
        "metadata": {
            "total_points": 156,
            "keys_found": ["temperature", "humidity"],
            "time_range": {
                "start": 1640908800000,
                "end": 1640995200000,
                "duration_hours": 24
            }
        }
    }
    ```
    """
    if not query.keys:
        raise HTTPException(400, detail="At least one telemetry key must be specified")
    
    # Set default time range if not provided (last 24 hours)
    import time
    current_time_ms = int(time.time() * 1000)
    start_ts = query.start_ts if query.start_ts is not None else current_time_ms - (24 * 60 * 60 * 1000)
    end_ts = query.end_ts if query.end_ts is not None else current_time_ms
    
    if start_ts >= end_ts:
        raise HTTPException(400, detail="start_ts must be less than end_ts")
    
    aggregated_data = {}
    total_points = 0
    keys_found = []
    
    try:
        for key in query.keys:
            key_data = []
            next_start = start_ts
            
            # Paginate through ThingsBoard's limit
            while next_start < end_ts:
                params = {
                    "keys": key,
                    "startTs": next_start,
                    "endTs": end_ts,
                    "limit": min(query.limit or 100, MAX_TB_LIMIT)
                }
                
                # Add aggregation interval if specified
                if query.interval:
                    params["interval"] = query.interval
                    params["agg"] = "AVG"  # Default aggregation method
                
                resp = await thingsboard_client.get(
                    f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
                    params=params
                )
                resp.raise_for_status()
                
                chunk = resp.json().get(key, [])
                if not chunk:
                    break
                    
                key_data.extend(chunk)
                total_points += len(chunk)
                
                # Break if we've reached the requested limit
                if len(key_data) >= (query.limit or 100):
                    key_data = key_data[:query.limit or 100]
                    break
                
                # Break if we got less than the maximum, indicating no more data
                if len(chunk) < MAX_TB_LIMIT:
                    break
                    
                # Update next start timestamp
                next_start = chunk[-1]["ts"] + 1
            
            if key_data:
                aggregated_data[key] = key_data
                keys_found.append(key)
        
        # Calculate duration in hours
        duration_hours = round((end_ts - start_ts) / (1000 * 60 * 60), 2)
        
        logger.info(f"Queried telemetry for device {device_id}: {len(keys_found)} keys, {total_points} total points")
        
        return {
            "device_id": device_id,
            "query": {
                "keys": query.keys,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "limit": query.limit,
                "interval": query.interval
            },
            "data": aggregated_data,
            "metadata": {
                "total_points": total_points,
                "keys_found": keys_found,
                "keys_missing": [k for k in query.keys if k not in keys_found],
                "time_range": {
                    "start": start_ts,
                    "end": end_ts,
                    "duration_hours": duration_hours
                }
            }
        }
        
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:
        logger.error(f"Error querying telemetry for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


# ---------------------------------------------------------------------------
# Upload Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/devices/{device_id}/telemetry",
    response_model=TelemetryUploadResponse,
    status_code=201,
    tags=["telemetry", "devices"],
    summary="Upload Telemetry Data",
    description="""
    Upload time-series telemetry data to a specific ThingsBoard device.
    
    This endpoint accepts multiple telemetry keys with timestamped data points,
    allowing efficient batch upload of sensor readings and device measurements.
    
    **Authentication Required**: This endpoint requires authentication with write permissions.
    
    **Rate Limiting**: Subject to the standard API rate limits.
    
    **ThingsBoard Integration**: 
    - Data is forwarded directly to ThingsBoard's telemetry API
    - Device must exist and be accessible to the authenticated tenant
    - Supports all ThingsBoard telemetry data types (numeric, boolean, string)
    
    **Data Validation**:
    - Timestamps must be positive integers (Unix milliseconds)
    - Telemetry keys must be non-empty strings
    - Values can be numbers, booleans, or strings
    - Maximum 1000 data points per request recommended
    
    **Use Cases**:
    - IoT sensor data collection
    - Device status updates  
    - Historical data backfill
    - Real-time monitoring data
    """,
    responses={
        201: {
            "description": "Telemetry data uploaded successfully",
            "model": TelemetryUploadResponse
        },
        400: {
            "description": "Invalid request data",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": 400,
                        "message": "No telemetry data provided",
                        "error_code": "VALIDATION_ERROR",
                        "timestamp": 1640995200000
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed",
            "model": ErrorResponse
        },
        403: {
            "description": "Insufficient permissions for write operations",
            "model": ErrorResponse
        },
        404: {
            "description": "Device not found",
            "model": ErrorResponse
        },
        502: {
            "description": "ThingsBoard backend error",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": 502,
                        "message": "ThingsBoard authentication failed",
                        "error_code": "UPSTREAM_ERROR",
                        "timestamp": 1640995200000
                    }
                }
            }
        }
    }
)
async def upload_device_telemetry(
    current_user: AuthenticatedUser,
    device_id: str = Path(
        ...,
        description="UUID of the target device",
        example="550e8400-e29b-41d4-a716-446655440000",
        regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    ),
    telemetry_data: Dict[str, List[TelemetryDataPoint]] = Body(
        ...,
        description="Telemetry data mapped by key names to timestamped value arrays",
        example={
            "temperature": [
                {"ts": 1640995200000, "value": 25.6},
                {"ts": 1640995260000, "value": 26.1}
            ],
            "humidity": [
                {"ts": 1640995200000, "value": 60.2}
            ]
        }
    )
) -> TelemetryUploadResponse:
    """
    Upload telemetry data to a specific device.
    
    Accepts a dictionary where keys are telemetry names (e.g., "temperature", "humidity")
    and values are arrays of timestamped data points.
    """
    if not telemetry_data:
        raise HTTPException(400, detail="No telemetry data provided")
    
    # Convert Pydantic models to ThingsBoard format
    tb_payload = {}
    for key, datapoints in telemetry_data.items():
        tb_payload[key] = [{"ts": dp.ts, "value": dp.value} for dp in datapoints]
    
    try:
        resp = await thingsboard_client.post(
            f"/api/plugins/telemetry/DEVICE/{device_id}/timeseries/any",
            json=tb_payload
        )
        resp.raise_for_status()
        
        # Count total data points uploaded
        total_points = sum(len(points) for points in telemetry_data.values())
        
        logger.info(
            f"Successfully uploaded {total_points} telemetry points for device {device_id}",
            extra={
                "device_id": device_id,
                "keys": list(telemetry_data.keys()),
                "total_points": total_points,
                "user": current_user.username if hasattr(current_user, 'username') else 'api_key'
            }
        )
        
        return TelemetryUploadResponse(
            status="success",
            timestamp=int(time.time() * 1000),
            device_id=device_id,
            keys_uploaded=list(telemetry_data.keys()),
            total_data_points=total_points,
            message=f"Successfully uploaded {total_points} data points for {len(telemetry_data)} telemetry keys"
        )
        
    except AuthError as exc:
        logger.error(f"ThingsBoard auth error for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="ThingsBoard authentication failed") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error uploading telemetry for device {device_id}: {exc}")
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


@router.post("/devices/{device_id}/attributes/server")
async def upload_device_server_attributes(
    device_id: str,
    attributes: Dict[str, Any],
    current_user: AuthenticatedUser
):
    """
    Upload server-side attributes to a device.
    
    Server-side attributes are managed by the server application and are typically
    used for device configuration, metadata, or computed values.
    
    **Example Request:**
    ```json
    {
        "serialNumber": "SN001234",
        "firmwareVersion": "1.2.3",
        "lastMaintenanceDate": "2024-01-15",
        "calibrationOffset": 0.5
    }
    ```
    
    **Use Cases:**
    - Device configuration parameters
    - Serial numbers and hardware info
    - Computed or derived values
    - Administrative metadata
    """
    if not attributes:
        raise HTTPException(400, detail="No attributes provided")
    
    try:
        resp = await thingsboard_client.post(
            f"/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE",
            json=attributes
        )
        resp.raise_for_status()
        
        return {
            "status": "success",
            "device_id": device_id,
            "scope": "SERVER_SCOPE",
            "attributes_uploaded": list(attributes.keys()),
            "count": len(attributes),
            "message": f"Successfully uploaded {len(attributes)} server-side attributes"
        }
        
    except AuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


@router.post("/devices/{device_id}/attributes/shared")
async def upload_device_shared_attributes(
    device_id: str,
    attributes: Dict[str, Any],
    current_user: AuthenticatedUser
):
    """
    Upload shared attributes to a device.
    
    Shared attributes are visible to both server and device, often used for
    device configuration that the device itself can read and act upon.
    
    **Example Request:**
    ```json
    {
        "targetTemperature": 22.0,
        "operationMode": "AUTO",
        "alertThresholds": {
            "temperature": {"min": 10, "max": 35},
            "humidity": {"min": 30, "max": 80}
        }
    }
    ```
    
    **Use Cases:**
    - Device configuration sent from server to device
    - Setpoints and operational parameters  
    - Thresholds and limits
    - Feature flags and operational modes
    """
    if not attributes:
        raise HTTPException(400, detail="No attributes provided")
    
    try:
        resp = await thingsboard_client.post(
            f"/api/plugins/telemetry/DEVICE/{device_id}/attributes/SHARED_SCOPE",
            json=attributes
        )
        resp.raise_for_status()
        
        return {
            "status": "success",
            "device_id": device_id,
            "scope": "SHARED_SCOPE", 
            "attributes_uploaded": list(attributes.keys()),
            "count": len(attributes),
            "message": f"Successfully uploaded {len(attributes)} shared attributes"
        }
        
    except AuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail="Upstream ThingsBoard error") from exc


@router.post("/telemetry/bulk")
async def bulk_upload_telemetry(
    data: Dict[str, Dict[str, List[TelemetryDataPoint]]],
    current_user: AuthenticatedUser
):
    """
    Upload telemetry data to multiple devices in a single request.
    
    Useful for batch processing scenarios where you need to upload data
    for many devices efficiently.
    
    **Example Request:**
    ```json
    {
        "device1-uuid-here": {
            "temperature": [{"ts": 1609459200000, "value": 25.6}],
            "humidity": [{"ts": 1609459200000, "value": 60.2}]
        },
        "device2-uuid-here": {
            "pressure": [{"ts": 1609459200000, "value": 1013.25}]
        }
    }
    ```
    
    **Response includes:**
    - Success/failure status per device
    - Total counts and statistics
    - Any errors encountered per device
    """
    if not data:
        raise HTTPException(400, detail="No device data provided")
    
    results = {}
    total_devices = len(data)
    total_points = 0
    successful_devices = 0
    failed_devices = 0
    
    for device_id, telemetry_data in data.items():
        try:
            # Convert to ThingsBoard format
            tb_payload = {}
            device_points = 0
            
            for key, datapoints in telemetry_data.items():
                tb_payload[key] = [{"ts": dp.ts, "value": dp.value} for dp in datapoints]
                device_points += len(datapoints)
            
            resp = await thingsboard_client.post(
                f"/api/plugins/telemetry/DEVICE/{device_id}/timeseries/any",
                json=tb_payload
            )
            resp.raise_for_status()
            
            results[device_id] = {
                "status": "success",
                "keys_uploaded": list(telemetry_data.keys()),
                "data_points": device_points
            }
            
            total_points += device_points
            successful_devices += 1
            
        except Exception as exc:  # pylint: disable=broad-except
            results[device_id] = {
                "status": "failed",
                "error": str(exc)
            }
            failed_devices += 1
    
    return {
        "status": "completed",
        "summary": {
            "total_devices": total_devices,
            "successful_devices": successful_devices,
            "failed_devices": failed_devices,
            "total_data_points": total_points
        },
        "results": results,
        "message": f"Bulk upload completed: {successful_devices}/{total_devices} devices successful"
    } 
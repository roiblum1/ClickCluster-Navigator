"""
Pydantic models for OpenShift cluster management.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import ipaddress
from datetime import datetime
from src.utils import ClusterValidator


class ClusterSegment(BaseModel):
    """Model for network segments with CIDR validation."""

    segment: str = Field(..., description="Network segment in CIDR notation")

    @field_validator('segment')
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        """Validate that the segment is a valid CIDR notation."""
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {v}. Error: {str(e)}")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "segment": "192.178.1.0/24"
        }
    })


class ClusterCreate(BaseModel):
    """Model for creating a new cluster."""

    clusterName: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$',
        description="Cluster name (must start with 'ocp4-', lowercase alphanumeric with hyphens)"
    )
    site: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Site identifier where cluster is deployed"
    )
    segments: List[str] = Field(
        ...,
        min_length=1,
        description="List of network segments in CIDR notation"
    )
    domainName: Optional[str] = Field(
        default="example.com",
        description="Domain name for the cluster"
    )

    @field_validator('segments')
    @classmethod
    def validate_segments(cls, v: List[str]) -> List[str]:
        """Validate all network segments."""
        validated_segments = []
        for segment in v:
            try:
                ipaddress.ip_network(segment, strict=False)
                validated_segments.append(segment)
            except ValueError as e:
                raise ValueError(f"Invalid CIDR notation in segment '{segment}': {str(e)}")
        return validated_segments

    @field_validator('clusterName')
    @classmethod
    def validate_cluster_name(cls, v: str) -> str:
        """Additional validation for cluster name."""
        v = v.lower()
        if v.startswith('-') or v.endswith('-'):
            raise ValueError("Cluster name cannot start or end with a hyphen")
        # Use ClusterValidator for prefix validation
        return ClusterValidator.validate_cluster_name(v)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "clusterName": "ocp4-roi",
            "site": "site1",
            "segments": ["192.178.1.0/24", "192.178.2.0/24"],
            "domainName": "example.com"
        }
    })


class ClusterResponse(BaseModel):
    """Model for cluster response with computed fields."""

    id: str = Field(..., description="Unique cluster identifier")
    clusterName: str = Field(..., description="Cluster name")
    site: str = Field(..., description="Site identifier")
    segments: List[str] = Field(..., description="Network segments")
    domainName: str = Field(..., description="Domain name")
    consoleUrl: str = Field(..., description="OpenShift console URL")
    createdAt: datetime = Field(..., description="Creation timestamp")
    source: Optional[str] = Field(default="manual", description="Cluster source: 'vlan-manager' or 'manual'")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "clusterName": "ocp4-roi",
                "site": "site1",
                "segments": ["192.178.1.0/24", "192.178.2.0/24"],
                "domainName": "example.com",
                "consoleUrl": "https://console-openshift-console.apps.ocp4-roi.example.com",
                "createdAt": "2025-11-13T12:00:00Z",
                "source": "vlan-manager"
            }
        }
    )


class ClusterUpdate(BaseModel):
    """Model for updating cluster information."""

    site: Optional[str] = Field(None, min_length=1, max_length=50)
    segments: Optional[List[str]] = Field(None, min_length=1)
    domainName: Optional[str] = Field(None, min_length=1)

    @field_validator('segments')
    @classmethod
    def validate_segments(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate all network segments if provided."""
        if v is None:
            return v
        validated_segments = []
        for segment in v:
            try:
                ipaddress.ip_network(segment, strict=False)
                validated_segments.append(segment)
            except ValueError as e:
                raise ValueError(f"Invalid CIDR notation in segment '{segment}': {str(e)}")
        return validated_segments

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "site": "site2",
            "segments": ["192.178.3.0/24"]
        }
    })


class SiteResponse(BaseModel):
    """Model for site information with cluster count."""

    site: str = Field(..., description="Site identifier")
    clusterCount: int = Field(..., description="Number of clusters in this site")
    clusters: List[ClusterResponse] = Field(..., description="List of clusters in this site")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "site": "site1",
            "clusterCount": 2,
            "clusters": []
        }
    })

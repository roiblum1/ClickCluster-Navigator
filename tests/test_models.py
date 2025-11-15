"""
Unit tests for Pydantic models.
"""
import pytest
from pydantic import ValidationError
from src.models import ClusterCreate, ClusterResponse


class TestClusterCreate:
    """Tests for ClusterCreate model."""

    def test_valid_cluster_creation(self):
        """Test creating a valid cluster."""
        cluster = ClusterCreate(
            clusterName="ocp4-test",
            site="site1",
            segments=["192.168.1.0/24", "10.0.0.0/16"],
            domainName="example.com"
        )
        assert cluster.clusterName == "ocp4-test"
        assert cluster.site == "site1"
        assert len(cluster.segments) == 2

    def test_cluster_name_lowercase_conversion(self):
        """Test that cluster names are converted to lowercase."""
        cluster = ClusterCreate(
            clusterName="OCP4-TEST",
            site="site1",
            segments=["192.168.1.0/24"]
        )
        assert cluster.clusterName == "ocp4-test"

    def test_invalid_cluster_name_format(self):
        """Test that invalid cluster names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClusterCreate(
                clusterName="Invalid_Name!",
                site="site1",
                segments=["192.168.1.0/24"]
            )
        assert "String should match pattern" in str(exc_info.value)

    def test_invalid_cidr_notation(self):
        """Test that invalid CIDR notation is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClusterCreate(
                clusterName="ocp4-test",
                site="site1",
                segments=["192.168.1.0"]  # Missing /24
            )
        assert "Invalid CIDR notation" in str(exc_info.value)

    def test_invalid_ip_address(self):
        """Test that invalid IP addresses are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClusterCreate(
                clusterName="ocp4-test",
                site="site1",
                segments=["999.999.999.999/24"]
            )
        assert "Invalid CIDR notation" in str(exc_info.value)

    def test_empty_segments(self):
        """Test that empty segments list is rejected."""
        with pytest.raises(ValidationError):
            ClusterCreate(
                clusterName="ocp4-test",
                site="site1",
                segments=[]
            )

    def test_cluster_name_too_short(self):
        """Test that cluster names must be at least 3 characters."""
        with pytest.raises(ValidationError):
            ClusterCreate(
                clusterName="ab",
                site="site1",
                segments=["192.168.1.0/24"]
            )

    def test_default_domain_name(self):
        """Test that domain name defaults to example.com."""
        cluster = ClusterCreate(
            clusterName="ocp4-test",
            site="site1",
            segments=["192.168.1.0/24"]
        )
        assert cluster.domainName == "example.com"

    def test_multiple_valid_segments(self):
        """Test cluster with multiple valid segments."""
        cluster = ClusterCreate(
            clusterName="ocp4-test",
            site="site1",
            segments=[
                "192.168.1.0/24",
                "192.168.2.0/24",
                "10.0.0.0/8",
                "172.16.0.0/12"
            ]
        )
        assert len(cluster.segments) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

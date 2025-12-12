"""
LoadBalancer IP resolution service.
Resolves cluster LoadBalancer IP addresses via DNS.
Supports multiple IPs for DNS round-robin load balancing.
"""
from typing import Optional, List
import logging
import time
import dns.resolver
import dns.exception
from src.config import config

logger = logging.getLogger(__name__)


class DNSStatsTracker:
    """Tracks DNS resolution statistics."""
    
    def __init__(self):
        self.request_count = 0
        self.total_time = 0.0
        self.success_count = 0
        self.failure_count = 0
    
    def reset(self):
        """Reset statistics."""
        self.request_count = 0
        self.total_time = 0.0
        self.success_count = 0
        self.failure_count = 0
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        avg_time = self.total_time / self.request_count if self.request_count > 0 else 0.0
        return {
            "request_count": self.request_count,
            "total_time_seconds": round(self.total_time, 3),
            "average_time_seconds": round(avg_time, 3),
            "success_count": self.success_count,
            "failure_count": self.failure_count
        }


# Global DNS stats tracker
_dns_stats = DNSStatsTracker()


class IPResolverService:
    """Service for resolving LoadBalancer IP addresses via DNS."""

    @staticmethod
    def get_dns_stats() -> dict:
        """Get current DNS resolution statistics."""
        return _dns_stats.get_stats()
    
    @staticmethod
    def reset_dns_stats():
        """Reset DNS resolution statistics."""
        _dns_stats.reset()

    @staticmethod
    def resolve_loadbalancer_ip(cluster_name: str, domain_name: Optional[str] = None, track_stats: bool = True) -> Optional[List[str]]:
        """
        Resolve LoadBalancer IP addresses by performing DNS lookup.
        Uses the configured DNS server and resolution path template.
        Returns all A records for DNS round-robin load balancing support.

        Args:
            cluster_name: The cluster name
            domain_name: Optional domain name (defaults to config value)
            track_stats: Whether to track DNS statistics

        Returns:
            List of IP address strings, or None if resolution fails.
            Returns empty list if no IPs found (but DNS query succeeded).
        """
        if domain_name is None:
            domain_name = config.default_domain

        cluster_name_lower = cluster_name.lower().strip()

        # Use the configurable DNS resolution path template
        hostname = config.dns_resolution_path.format(
            cluster_name=cluster_name_lower,
            domain_name=domain_name
        )

        logger.debug(f"Resolving DNS for cluster '{cluster_name}' -> hostname: {hostname}")

        start_time = time.time()
        success = False

        try:
            # Track DNS request
            if track_stats:
                _dns_stats.request_count += 1

            # Create a custom DNS resolver with specific DNS server
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [config.dns_server]
            resolver.timeout = config.dns_timeout
            resolver.lifetime = config.dns_timeout
            logger.debug(f"DNS resolver configured: server={config.dns_server}, timeout={config.dns_timeout}s")

            # Perform DNS lookup for A record
            logger.debug(f"Querying DNS A record for hostname: {hostname}")
            answers = resolver.resolve(hostname, 'A')
            logger.info(f"Query DNS address for hostname: {hostname}")
            
            if answers:
                # Collect all A records for round-robin support
                ip_addresses = [str(answer) for answer in answers]
                success = True
                if track_stats:
                    _dns_stats.success_count += 1
                
                ip_count = len(ip_addresses)
                if ip_count == 1:
                    logger.info(
                        f"✓ DNS Resolved: {hostname} → {ip_addresses[0]} "
                        f"(server: {config.dns_server})"
                    )
                else:
                    logger.info(
                        f"✓ DNS Resolved: {hostname} → {ip_count} IPs "
                        f"({', '.join(ip_addresses)}) "
                        f"(server: {config.dns_server}, round-robin)"
                    )
                return ip_addresses
            else:
                if track_stats:
                    _dns_stats.failure_count += 1
                logger.info(f"✗ DNS Failed: No A records for {hostname}")
                return None

        except dns.resolver.NXDOMAIN:
            if track_stats:
                _dns_stats.failure_count += 1
            logger.info(f"✗ DNS Failed: Name does not exist: {hostname}")
            return None
        except dns.resolver.NoAnswer:
            if track_stats:
                _dns_stats.failure_count += 1
            logger.info(f"✗ DNS Failed: No answer for {hostname}")
            return None
        except dns.resolver.Timeout:
            if track_stats:
                _dns_stats.failure_count += 1
            logger.info(
                f"✗ DNS Failed: Timeout for {hostname} "
                f"(timeout: {config.dns_timeout}s)"
            )
            return None
        except dns.exception.DNSException as e:
            if track_stats:
                _dns_stats.failure_count += 1
            logger.info(f"✗ DNS Failed: {hostname} - {e}")
            return None
        except Exception as e:
            if track_stats:
                _dns_stats.failure_count += 1
            logger.warning(f"✗ DNS Unexpected error resolving {hostname}: {e}")
            return None
        finally:
            # Track DNS resolution time
            if track_stats:
                elapsed_time = time.time() - start_time
                _dns_stats.total_time += elapsed_time

"""
LoadBalancer IP resolution service.
Resolves cluster LoadBalancer IP addresses via DNS.
"""
from typing import Optional
import logging
import dns.resolver
import dns.exception
from src.config import config

logger = logging.getLogger(__name__)


class IPResolverService:
    """Service for resolving LoadBalancer IP addresses via DNS."""

    @staticmethod
    def resolve_loadbalancer_ip(cluster_name: str, domain_name: Optional[str] = None) -> Optional[str]:
        """
        Resolve LoadBalancer IP address by performing DNS lookup.
        Uses the configured DNS server and resolution path template.

        Args:
            cluster_name: The cluster name
            domain_name: Optional domain name (defaults to config value)

        Returns:
            IP address string or None if resolution fails
        """
        if domain_name is None:
            domain_name = config.default_domain

        cluster_name_lower = cluster_name.lower().strip()

        # Use the configurable DNS resolution path template
        hostname = config.dns_resolution_path.format(
            cluster_name=cluster_name_lower,
            domain_name=domain_name
        )

        try:
            # Create a custom DNS resolver with specific DNS server
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [config.dns_server]
            resolver.timeout = config.dns_timeout
            resolver.lifetime = config.dns_timeout

            # Perform DNS lookup for A record
            answers = resolver.resolve(hostname, 'A')

            if answers:
                ip_address = str(answers[0])
                logger.debug(
                    f"Resolved {hostname} to {ip_address} "
                    f"using DNS server {config.dns_server}"
                )
                return ip_address
            else:
                logger.debug(f"No A records found for {hostname}")
                return None

        except dns.resolver.NXDOMAIN:
            logger.debug(f"DNS name does not exist: {hostname}")
            return None
        except dns.resolver.NoAnswer:
            logger.debug(f"No answer from DNS for: {hostname}")
            return None
        except dns.resolver.Timeout:
            logger.debug(
                f"DNS lookup timeout for {hostname} "
                f"(timeout: {config.dns_timeout}s)"
            )
            return None
        except dns.exception.DNSException as e:
            logger.debug(f"DNS error resolving {hostname}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error resolving {hostname}: {e}")
            return None

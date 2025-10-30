#!/usr/bin/env python3
"""Generate docker-compose.yml from .httptests/config.yml"""
import argparse
import os
import sys
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except ImportError as exc:
    print("PyYAML is required. Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load config.yml if it exists, otherwise return empty dict"""
    if not os.path.isfile(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def to_list(value: Any) -> List[Any]:
    """Convert value to list, handling None and single values"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def generate_compose(suite_dir: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate docker-compose structure from config"""
    parent_dir = os.path.abspath(os.path.join(suite_dir, os.pardir))

    # Config mappings
    mock_cfg = config.get("mock", {}) or {}
    nginx_cfg = config.get("nginx", {}) or {}

    network_aliases = to_list(mock_cfg.get("network_aliases") or [])
    
    # Support both 'port' (legacy) and 'http_port' (new)
    http_port = mock_cfg.get("http_port") or mock_cfg.get("port", 80)
    https_port = mock_cfg.get("https_port", 443)
    additional_ports = to_list(mock_cfg.get("additional_ports") or [])
    
    nginx_env = nginx_cfg.get("environment") or {}

    # Validate Dockerfile
    dockerfile_path = os.path.join(parent_dir, "Dockerfile")
    if not os.path.isfile(dockerfile_path):
        raise FileNotFoundError(f"Dockerfile not found at expected location: {dockerfile_path}")

    # Build environment list for mock service
    mock_environment = [
        f"HTTP_PORT={http_port}",
        f"HTTPS_PORT={https_port}",
    ]

    compose: Dict[str, Any] = {
        "version": "3.9",
        "services": {
            "mock": {
                "container_name": "httptests_mock",
                "image": "mendhak/http-https-echo:18",
                "environment": mock_environment,
                "networks": {
                    "default": {
                        "aliases": network_aliases or [],
                    }
                },
            },
            "nginx": {
                "container_name": "httptests_nginx",
                "build": {
                    "context": parent_dir,
                    "dockerfile": "Dockerfile",
                },
                "ports": ["80:80"],
                "networks": ["default"],
                "depends_on": ["mock"],
            },
        },
    }

    # Map nginx environment variables
    if nginx_env:
        # Accept dict or list in YAML
        if isinstance(nginx_env, dict):
            compose["services"]["nginx"]["environment"] = nginx_env
        else:
            compose["services"]["nginx"]["environment"] = to_list(nginx_env)

    # Add port forwarders for additional ports
    # This allows the mock service to be accessible on multiple ports using the same network aliases
    if additional_ports:
        for port in additional_ports:
            service_name = f"mock-forwarder-{port}"
            compose["services"][service_name] = {
                "container_name": f"httptests_forwarder_{port}",
                "image": "alpine/socat:latest",
                "command": f"TCP-LISTEN:{port},fork,reuseaddr TCP:mock:{http_port}",
                "networks": {
                    "default": {
                        "aliases": network_aliases or [],  # Share the same network aliases as mock
                    }
                },
                "depends_on": ["mock"],
            }
            # Update nginx dependencies to include port forwarders
            compose["services"]["nginx"]["depends_on"].append(service_name)

    return compose


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate docker-compose.yml for HTTPTests suite")
    parser.add_argument("--suite", required=True, help="Path to .httptests directory")
    parser.add_argument("--output", required=True, help="Output path for docker-compose.yml")
    args = parser.parse_args()

    suite_dir = os.path.abspath(args.suite)
    if not os.path.isdir(suite_dir):
        print(f"Suite directory not found: {suite_dir}", file=sys.stderr)
        sys.exit(1)

    config_path = os.path.join(suite_dir, "config.yml")
    config = load_config(config_path)

    compose = generate_compose(suite_dir, config)

    # Write output YAML
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        yaml.safe_dump(compose, f, sort_keys=False)

    print(f"Wrote docker compose to: {args.output}")


if __name__ == "__main__":
    main()


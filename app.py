#!/usr/bin/env python3
"""
Docker Nginx Scaling Script

This script checks if Docker is installed and accessible, then runs and scales an Nginx container.
It automatically retries Docker commands with `sudo` if permission to the Docker socket is denied.
"""

import subprocess
import sys
import logging
import os
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _docker_exec(cmd: List[str], retry_with_sudo: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a Docker command, retrying with sudo if permission is denied.

    Args:
        cmd: Full command list, e.g. ['docker', 'run', ...]
        retry_with_sudo: Whether to retry with sudo on permission denied

    Returns:
        CompletedProcess instance
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise FileNotFoundError("Docker command not found. Please install Docker.")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out: {' '.join(cmd)}")

    if result.returncode != 0 and retry_with_sudo:
        # Check for permission denied in stderr
        if "permission denied" in result.stderr.lower():
            logger.warning("Permission denied when accessing Docker socket. Retrying with sudo.")
            try:
                result = subprocess.run(
                    ["sudo"] + cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
            except Exception as e:
                raise RuntimeError(f"Failed to run command with sudo: {e}")

    return result


def check_docker_installed() -> bool:
    """
    Check if Docker is installed and accessible.

    Returns:
        True if Docker is installed and accessible, False otherwise.
    """
    try:
        result = _docker_exec(["docker", "--version"])
        if result.returncode == 0:
            logger.info(f"Docker is installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("Docker is not installed or not accessible.")
            logger.error(f"Error output: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error while checking Docker installation: {e}")
        return False


def run_nginx_container(container_name: str = "nginx-scaling") -> Optional[str]:
    """
    Run a single Nginx container.

    Args:
        container_name: Name for the container

    Returns:
        Container ID if successful, None otherwise
    """
    try:
        logger.info(f"Starting Nginx container: {container_name}")
        result = _docker_exec(
            ["docker", "run", "-d", "--name", container_name, "nginx"]
        )
        if result.returncode == 0:
            container_id = result.stdout.strip()
            logger.info(f"Nginx container started successfully with ID: {container_id}")
            return container_id
        else:
            logger.error(f"Failed to start Nginx container: {result.stderr.strip()}")
            return None
    except Exception as e:
        logger.error(f"Unexpected error while starting Nginx container: {e}")
        return None


def scale_nginx_containers(num_containers: int, base_name: str = "nginx-scaling") -> List[str]:
    """
    Scale Nginx containers to the specified number.

    Args:
        num_containers: Number of containers to run
        base_name: Base name for containers

    Returns:
        List of container IDs
    """
    container_ids: List[str] = []

    # Clean up existing containers with the same base name
    try:
        result = _docker_exec(
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "{{.Names}}",
                "--filter",
                f"name={base_name}",
            ]
        )
        if result.returncode == 0:
            existing_containers = [
                name.strip() for name in result.stdout.strip().split("\n") if name.strip()
            ]
            for container_name in existing_containers:
                logger.info(f"Stopping and removing existing container: {container_name}")
                _docker_exec(["docker", "stop", container_name], retry_with_sudo=False)
                _docker_exec(["docker", "rm", container_name], retry_with_sudo=False)
    except Exception as e:
        logger.warning(f"Could not clean up existing containers: {e}")

    # Start new containers
    for i in range(num_containers):
        container_name = f"{base_name}-{i + 1}"
        container_id = run_nginx_container(container_name)
        if container_id:
            container_ids.append(container_id)
            logger.info(f"Successfully started container {container_name}")
        else:
            logger.error(f"Failed to start container {container_name}")

    return container_ids


def get_running_containers(base_name: str = "nginx-scaling") -> List[str]:
    """
    Get list of running containers with the specified base name.

    Args:
        base_name: Base name to filter containers

    Returns:
        List of running container names
    """
    try:
        result = _docker_exec(
            [
                "docker",
                "ps",
                "--format",
                "{{.Names}}",
                "--filter",
                f"name={base_name}",
            ]
        )
        if result.returncode == 0:
            containers = [
                name.strip() for name in result.stdout.strip().split("\n") if name.strip()
            ]
            return containers
        else:
            logger.error(f"Error getting running containers: {result.stderr.strip()}")
            return []
    except Exception as e:
        logger.error(f"Unexpected error getting running containers: {e}")
        return []


def main() -> None:
    """Main entry point for the script."""
    logger.info("Starting Docker Nginx Scaling Script")

    # Check Docker socket accessibility
    if not os.path.exists("/var/run/docker.sock"):
        logger.error("Docker socket /var/run/docker.sock does not exist.")
        sys.exit(1)
    if not os.access("/var/run/docker.sock", os.R_OK | os.W_OK):
        logger.warning(
            "Current user does not have read/write access to /var/run/docker.sock. "
            "Commands may fail unless run with sudo or the user is added to the docker group."
        )

    # Check if Docker is installed
    if not check_docker_installed():
        logger.error("Docker is required but not installed or accessible. Exiting.")
        sys.exit(1)

    # Define scaling parameters
    num_containers = 3
    base_name = "nginx-scaling"

    # Scale containers
    container_ids = scale_nginx_containers(num_containers, base_name)
    if not container_ids:
        logger.error("No containers were started. Exiting.")
        sys.exit(1)

    # List running containers
    running = get_running_containers(base_name)
    if running:
        logger.info(f"Running containers: {', '.join(running)}")
    else:
        logger.info("No running containers found.")


if __name__ == "__main__":
    main()
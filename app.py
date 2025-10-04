#!/usr/bin/env python3
"""
Docker Nginx Scaling Script

This script checks if Docker is installed, and if so, runs and scales an Nginx container.
"""

import subprocess
import sys
import logging
import time
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_docker_installed() -> bool:
    """
    Check if Docker is installed and accessible.
    
    Returns:
        bool: True if Docker is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['docker', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info(f"Docker is installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("Docker is not installed or not accessible")
            logger.error(f"Error output: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout while checking Docker installation")
        return False
    except FileNotFoundError:
        logger.error("Docker command not found. Please install Docker.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while checking Docker: {e}")
        return False


def run_nginx_container(container_name: str = "nginx-scaling") -> Optional[str]:
    """
    Run a single Nginx container.
    
    Args:
        container_name (str): Name for the container
        
    Returns:
        Optional[str]: Container ID if successful, None otherwise
    """
    try:
        logger.info(f"Starting Nginx container: {container_name}")
        
        # Run Nginx container with default settings
        result = subprocess.run(
            ['docker', 'run', '-d', '--name', container_name, 'nginx'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            container_id = result.stdout.strip()
            logger.info(f"Nginx container started successfully with ID: {container_id}")
            return container_id
        else:
            logger.error(f"Failed to start Nginx container: {result.stderr.strip()}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout while starting Nginx container")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while starting Nginx container: {e}")
        return None


def scale_nginx_containers(num_containers: int, base_name: str = "nginx-scaling") -> List[str]:
    """
    Scale Nginx containers to the specified number.
    
    Args:
        num_containers (int): Number of containers to run
        base_name (str): Base name for containers
        
    Returns:
        List[str]: List of container IDs
    """
    container_ids = []
    
    # First, check if any existing containers with the same base name exist
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', f'name={base_name}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            existing_containers = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
            
            # Stop and remove existing containers
            for container_name in existing_containers:
                logger.info(f"Stopping and removing existing container: {container_name}")
                subprocess.run(['docker', 'stop', container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['docker', 'rm', container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    except Exception as e:
        logger.warning(f"Could not clean up existing containers: {e}")
    
    # Start new containers
    for i in range(num_containers):
        container_name = f"{base_name}-{i+1}"
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
        base_name (str): Base name to filter containers
        
    Returns:
        List[str]: List of running container names
    """
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}', '--filter', f'name={base_name}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            containers = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
            return containers
        else:
            logger.error(f"Error getting running containers: {result.stderr.strip()}")
            return []
            
    except Exception as e:
        logger.error(f"Unexpected error getting running containers: {e}")
        return []


def main():
    """Main entry point for the script."""
    logger.info("Starting Docker Nginx Scaling Script")
    
    # Check if Docker is installed
    if not check_docker_installed():
        logger.error("Docker is required but not installed or accessible. Exiting.")
        sys.exit(1)
    
    # Define scaling parameters
    num_containers = 3  # Default number of containers to run
    
    try:
        logger.info(f"Scaling Nginx containers to {num_containers}")
        
        # Scale the containers
        container_ids = scale_nginx_containers(num_containers)
        
        if not container_ids:
            logger.error("Failed to start any Nginx containers")
            sys.exit(1)
        
        logger.info(f"Successfully started {len(container_ids)} Nginx containers")
        
        # Show running containers
        running_containers = get_running_containers()
        if running_containers:
            logger.info("Running containers:")
            for container in running_containers:
                logger.info(f"  - {container}")
        else:
            logger.warning("No running containers found")
            
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")
        sys.exit(1)
    
    logger.info("Docker Nginx Scaling Script completed successfully")


if __name__ == "__main__":
    main()
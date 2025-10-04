#!/usr/bin/env python3
"""
System Resource Checker
=======================
A robust tool to check computer resources including CPU, memory, disk, and network information.
"""

import logging
import platform
import psutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_resources.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_system_info() -> Dict:
    """Get basic system information."""
    try:
        system_info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'hostname': socket.gethostname(),
            'username': platform.uname().node,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.info("System information retrieved successfully")
        return system_info
    except Exception as e:
        logger.error(f"Error retrieving system information: {e}")
        return {}

def get_cpu_info() -> Dict:
    """Get CPU information and usage statistics."""
    try:
        cpu_info = {
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_times': psutil.cpu_times()._asdict(),
            'cpu_stats': psutil.cpu_stats()._asdict()
        }
        logger.info("CPU information retrieved successfully")
        return cpu_info
    except Exception as e:
        logger.error(f"Error retrieving CPU information: {e}")
        return {}

def get_memory_info() -> Dict:
    """Get memory information."""
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_info = {
            'total_memory': memory.total,
            'available_memory': memory.available,
            'used_memory': memory.used,
            'memory_percent': memory.percent,
            'memory_free': memory.free,
            'memory_cached': memory.cached if hasattr(memory, 'cached') else None,
            'memory_buffers': memory.buffers if hasattr(memory, 'buffers') else None,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent,
            'swap_free': swap.free
        }
        logger.info("Memory information retrieved successfully")
        return memory_info
    except Exception as e:
        logger.error(f"Error retrieving memory information: {e}")
        return {}

def get_disk_info() -> List[Dict]:
    """Get disk usage information for all mounted partitions."""
    try:
        partitions = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partition_info = {
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'filesystem': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                }
                partitions.append(partition_info)
            except PermissionError:
                # This can happen on Windows with certain partitions
                logger.warning(f"Permission denied accessing partition {partition.mountpoint}")
                continue
        logger.info("Disk information retrieved successfully")
        return partitions
    except Exception as e:
        logger.error(f"Error retrieving disk information: {e}")
        return []

def get_network_info() -> Dict:
    """Get network information."""
    try:
        # Get network interfaces
        interfaces = psutil.net_if_addrs()
        
        # Get network statistics
        net_stats = psutil.net_io_counters()
        
        network_info = {
            'interfaces': {},
            'bytes_sent': net_stats.bytes_sent,
            'bytes_recv': net_stats.bytes_recv,
            'packets_sent': net_stats.packets_sent,
            'packets_recv': net_stats.packets_recv,
            'errors_in': net_stats.errin,
            'errors_out': net_stats.errout,
            'drops_in': net_stats.dropin,
            'drops_out': net_stats.dropout
        }
        
        # Process each interface
        for interface_name, interface_addresses in interfaces.items():
            network_info['interfaces'][interface_name] = []
            for address in interface_addresses:
                addr_info = {
                    'family': str(address.family),
                    'address': address.address,
                    'netmask': address.netmask,
                    'broadcast': address.broadcast,
                    'ptp': address.ptp
                }
                network_info['interfaces'][interface_name].append(addr_info)
        
        logger.info("Network information retrieved successfully")
        return network_info
    except Exception as e:
        logger.error(f"Error retrieving network information: {e}")
        return {}

def get_running_processes() -> List[Dict]:
    """Get information about running processes."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent']):
            try:
                process_info = {
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 2),
                    'cpu_percent': proc.info['cpu_percent']
                }
                processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process might have terminated or we don't have permission
                continue
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        
        logger.info("Process information retrieved successfully")
        return processes[:10]  # Return top 10 memory-consuming processes
    except Exception as e:
        logger.error(f"Error retrieving process information: {e}")
        return []

def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human readable format."""
    if bytes_value is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def display_system_info(system_info: Dict):
    """Display system information."""
    print("\n" + "="*60)
    print("SYSTEM INFORMATION")
    print("="*60)
    for key, value in system_info.items():
        if isinstance(value, str) and len(value) > 50:
            # Truncate long strings
            print(f"{key.capitalize():<20}: {value[:50]}...")
        else:
            print(f"{key.capitalize():<20}: {value}")

def display_cpu_info(cpu_info: Dict):
    """Display CPU information."""
    print("\n" + "="*60)
    print("CPU INFORMATION")
    print("="*60)
    for key, value in cpu_info.items():
        if key == 'cpu_times':
            print(f"{key.capitalize():<20}: {value}")
        elif key == 'cpu_stats':
            print(f"{key.capitalize():<20}: {value}")
        else:
            print(f"{key.capitalize():<20}: {value}")

def display_memory_info(memory_info: Dict):
    """Display memory information."""
    print("\n" + "="*60)
    print("MEMORY INFORMATION")
    print("="*60)
    for key, value in memory_info.items():
        if 'memory' in key.lower() or 'swap' in key.lower():
            if isinstance(value, (int, float)):
                print(f"{key.capitalize():<20}: {format_bytes(value)}")
            else:
                print(f"{key.capitalize():<20}: {value}")
        else:
            print(f"{key.capitalize():<20}: {value}")

def display_disk_info(disk_info: List[Dict]):
    """Display disk information."""
    print("\n" + "="*60)
    print("DISK USAGE")
    print("="*60)
    if not disk_info:
        print("No disk information available")
        return
    
    for partition in disk_info:
        print(f"Device: {partition['device']}")
        print(f"  Mountpoint: {partition['mountpoint']}")
        print(f"  Filesystem: {partition['filesystem']}")
        print(f"  Total: {format_bytes(partition['total'])}")
        print(f"  Used: {format_bytes(partition['used'])}")
        print(f"  Free: {format_bytes(partition['free'])}")
        print(f"  Usage: {partition['percent']:.1f}%")
        print()

def display_network_info(network_info: Dict):
    """Display network information."""
    print("\n" + "="*60)
    print("NETWORK INFORMATION")
    print("="*60)
    
    # Network statistics
    print(f"Bytes Sent: {format_bytes(network_info['bytes_sent'])}")
    print(f"Bytes Received: {format_bytes(network_info['bytes_recv'])}")
    print(f"Packets Sent: {network_info['packets_sent']}")
    print(f"Packets Received: {network_info['packets_recv']}")
    print(f"Errors In: {network_info['errors_in']}")
    print(f"Errors Out: {network_info['errors_out']}")
    
    # Interfaces
    print("\nNetwork Interfaces:")
    for interface_name, addresses in network_info['interfaces'].items():
        print(f"  {interface_name}:")
        for addr in addresses:
            print(f"    Family: {addr['family']}")
            print(f"    Address: {addr['address']}")
            if addr['netmask']:
                print(f"    Netmask: {addr['netmask']}")
            if addr['broadcast']:
                print(f"    Broadcast: {addr['broadcast']}")

def display_processes(processes: List[Dict]):
    """Display top processes."""
    print("\n" + "="*60)
    print("TOP PROCESSES BY MEMORY USAGE")
    print("="*60)
    if not processes:
        print("No process information available")
        return
    
    print(f"{'PID':<8} {'NAME':<25} {'USER':<20} {'MEMORY (MB)':<15}")
    print("-" * 70)
    for proc in processes:
        print(f"{proc['pid']:<8} {proc['name'][:24]:<25} {proc['username'][:19]:<20} {proc['memory_mb']:<15}")

def validate_dependencies() -> bool:
    """Validate that required dependencies are available."""
    try:
        import psutil
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print("Please install psutil: pip install psutil")
        return False

def main():
    """Main function to check system resources."""
    logger.info("Starting system resource check...")
    
    # Validate dependencies
    if not validate_dependencies():
        sys.exit(1)
    
    try:
        # Get all system information
        system_info = get_system_info()
        cpu_info = get_cpu_info()
        memory_info = get_memory_info()
        disk_info = get_disk_info()
        network_info = get_network_info()
        processes = get_running_processes()
        
        # Display results
        display_system_info(system_info)
        display_cpu_info(cpu_info)
        display_memory_info(memory_info)
        display_disk_info(disk_info)
        display_network_info(network_info)
        display_processes(processes)
        
        logger.info("System resource check completed successfully")
        
    except KeyboardInterrupt:
        logger.info("System resource check interrupted by user")
        print("\nCheck interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error during system check: {e}")
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
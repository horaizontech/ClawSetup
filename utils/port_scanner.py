import socket
import logging

logger = logging.getLogger("ClawSetup.PortScanner")

def scan_port(port: int) -> bool:
    """Checks if a specific port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def get_available_ports(start_port: int = 18789, end_port: int = 20000, count: int = 3) -> list[int]:
    """Scans ports and returns the first 'count' available ports."""
    logger.info(f"Scanning for {count} available ports between {start_port} and {end_port}.")
    available = []
    for port in range(start_port, end_port + 1):
        if scan_port(port):
            available.append(port)
            if len(available) == count:
                break
    
    logger.info(f"Found available ports: {available}")
    return available

def recommend_best_port() -> int | None:
    """Returns the best available port (first one found)."""
    ports = get_available_ports(count=1)
    if ports:
        logger.info(f"Recommended port: {ports[0]}")
        return ports[0]
    logger.error("No available ports found in range.")
    return None

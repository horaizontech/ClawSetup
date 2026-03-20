import psutil
import logging
from pathlib import Path

logger = logging.getLogger("ClawSetup.DriveSelector")

def get_mounted_drives() -> list[dict]:
    """Lists all mounted drives/volumes with their free space."""
    logger.info("Scanning for mounted drives.")
    drives = []
    for part in psutil.disk_partitions(all=False):
        # Skip read-only or inaccessible drives
        if 'cdrom' in part.opts or part.fstype == '':
            continue
            
        try:
            usage = psutil.disk_usage(part.mountpoint)
            drives.append({
                "device": part.device,
                "mountpoint": Path(part.mountpoint),
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2)
            })
        except PermissionError:
            logger.warning(f"Permission denied when accessing {part.mountpoint}")
            continue
            
    logger.info(f"Found {len(drives)} accessible drives.")
    return drives

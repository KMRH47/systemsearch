import hashlib
import os
import subprocess
from pathlib import Path
from typing import List
from .constants import MEDIA_DIR

class DbManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_db_path(self, path: str) -> Path:
        path_hash = hashlib.md5(path.encode()).hexdigest()
        return self.cache_dir / f"{path_hash}.db"

    def get_mounted_drives(self) -> List[str]:
        mounts = []
        media_dir = Path(MEDIA_DIR)
        if not media_dir.exists():
            return mounts
        try:
            for item in media_dir.iterdir():
                if item.is_dir():
                    mounts.append(str(item))
        except PermissionError:
            pass
        return mounts

    def update_dbs(self, extra_paths: List[str], auto_mounts: bool = True):
        paths = set(extra_paths)
        if auto_mounts:
            paths.update(self.get_mounted_drives())
        
        current_db_files = set()
        for path in paths:
            if not os.path.exists(path):
                continue
            db_path = self._get_db_path(path)
            current_db_files.add(db_path)
            
            cmd = [
                "updatedb",
                "-l", "0",
                "-U", path,
                "-o", str(db_path)
            ]
            try:
                subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                pass

        for db_file in self.cache_dir.glob("*.db"):
            if db_file not in current_db_files:
                try:
                    db_file.unlink()
                except:
                    pass

    def get_db_paths(self) -> List[str]:
        return [str(p) for p in self.cache_dir.glob("*.db")]

"""
Centralized file operations with locking for multi-replica safety.
Provides thread-safe file I/O operations for JSON data.
"""
import fcntl
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FileOperations:
    """Thread-safe file operations with retry logic and file locking."""

    @staticmethod
    def read_json_with_lock(
        file_path: Path,
        max_retries: int = 3,
        retry_delay: float = 0.1
    ) -> Optional[Dict]:
        """
        Read JSON data from file with shared lock (multiple readers allowed).

        Args:
            file_path: Path to the JSON file
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Parsed JSON data as dictionary, or None if file doesn't exist or read fails
        """
        if not file_path.exists():
            return None

        for attempt in range(max_retries):
            try:
                with open(file_path, 'r') as f:
                    # Acquire shared lock (multiple readers can read simultaneously)
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        data = json.load(f)
                        logger.debug(f"Successfully read from {file_path}")
                        return data
                    finally:
                        # Always release the lock
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            except (IOError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Read attempt {attempt + 1} failed for {file_path}, retrying...")
                    time.sleep(retry_delay)
                    continue
                logger.error(f"Failed to read {file_path} after {max_retries} attempts: {e}")
                return None

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {file_path}: {e}")
                return None

            except Exception as e:
                logger.error(f"Unexpected error reading {file_path}: {e}")
                return None

        return None

    @staticmethod
    def write_json_with_lock(
        file_path: Path,
        data: Dict,
        max_retries: int = 5,
        retry_delay: float = 0.2,
        indent: int = 2
    ) -> bool:
        """
        Write JSON data to file with exclusive lock (atomic write).

        Uses temporary file + atomic rename pattern for safety.
        Only one writer can write at a time (exclusive lock).

        Args:
            file_path: Path to the JSON file
            data: Dictionary to write as JSON
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            indent: JSON indentation level

        Returns:
            True if write succeeded, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write to temporary file first
                temp_file = file_path.with_suffix('.tmp')

                with open(temp_file, 'w') as f:
                    # Acquire exclusive lock (no other readers or writers allowed)
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        # Write JSON data
                        json.dump(data, f, indent=indent)
                        f.flush()
                        # Force write to disk (important for multi-replica consistency)
                        os.fsync(f.fileno())
                    finally:
                        # Always release the lock
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                # Atomic rename (safe even with concurrent access from multiple replicas)
                temp_file.replace(file_path)
                logger.debug(f"Successfully wrote to {file_path}")
                return True

            except (IOError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Write attempt {attempt + 1} failed for {file_path}, retrying...")
                    time.sleep(retry_delay)
                    continue
                logger.error(f"Failed to write {file_path} after {max_retries} attempts: {e}")
                return False

            except Exception as e:
                logger.error(f"Unexpected error writing {file_path}: {e}")
                return False

        return False

    @staticmethod
    def ensure_directory(directory: Path) -> bool:
        """
        Ensure directory exists, create if necessary.

        Args:
            directory: Path to directory

        Returns:
            True if directory exists or was created successfully
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            return False

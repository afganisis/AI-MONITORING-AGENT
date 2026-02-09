"""Progress tracker for scan operations."""

from typing import Dict, Any
from datetime import datetime


class ProgressTracker:
    """Track progress of scan operations."""

    def __init__(self):
        """Initialize progress tracker."""
        self._progress: Dict[str, Dict[str, Any]] = {}

    def start_scan(self, scan_id: str, total_drivers: int):
        """Start tracking a scan."""
        self._progress[scan_id] = {
            'scan_id': scan_id,
            'total_drivers': total_drivers,
            'completed_drivers': 0,
            'current_driver': None,
            'current_driver_id': None,
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'progress_percent': 0,
            'message': f'Начало сканирования {total_drivers} водителей...',
            'step': 'initializing',  # Step within current driver scan
            'step_message': 'Инициализация браузера...'
        }

    def update_driver(self, scan_id: str, driver_index: int, driver_id: str):
        """Update current driver being scanned."""
        if scan_id not in self._progress:
            return

        progress = self._progress[scan_id]
        progress['current_driver'] = driver_index + 1
        progress['current_driver_id'] = driver_id
        progress['completed_drivers'] = driver_index
        progress['progress_percent'] = int((driver_index / progress['total_drivers']) * 100) if progress['total_drivers'] > 0 else 0
        progress['message'] = f'Сканирование водителя {driver_index + 1} из {progress["total_drivers"]}...'
        progress['step'] = 'starting'
        progress['step_message'] = 'Инициализация браузера для драйвера...'

    def update_message(self, scan_id: str, message: str):
        """Update progress message (high-level)."""
        if scan_id not in self._progress:
            return

        self._progress[scan_id]['message'] = message

    def update_step(self, scan_id: str, step: str, step_message: str):
        """Update step-level progress (detailed automation steps)."""
        if scan_id not in self._progress:
            return

        self._progress[scan_id]['step'] = step
        self._progress[scan_id]['step_message'] = step_message

    def complete_scan(self, scan_id: str, success: bool = True, message: str = None):
        """Mark scan as completed."""
        if scan_id not in self._progress:
            return

        progress = self._progress[scan_id]
        progress['status'] = 'completed' if success else 'failed'
        progress['progress_percent'] = 100 if success else progress['progress_percent']
        progress['completed_at'] = datetime.now().isoformat()

        if message:
            progress['message'] = message
        elif success:
            progress['message'] = f'Сканирование завершено! Обработано {progress["total_drivers"]} водителей.'
        else:
            progress['message'] = 'Сканирование не удалось.'

    def get_progress(self, scan_id: str) -> Dict[str, Any] | None:
        """Get progress for a scan."""
        return self._progress.get(scan_id)

    def remove_scan(self, scan_id: str):
        """Remove scan from tracker."""
        self._progress.pop(scan_id, None)


# Global instance
progress_tracker = ProgressTracker()

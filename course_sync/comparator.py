import logging
from typing import Dict

from course_sync.change_detectors import CategoryNameChangeDetector, NameChangeDetector, StructuralChangeDetector, TopicNameChangeDetector

log = logging.getLogger(__name__)


class StructureComparator:
    """Responsible for comparing course structures"""

    def __init__(self):
        self.detectors = [
            StructuralChangeDetector(),
            NameChangeDetector(),
            CategoryNameChangeDetector(),
            TopicNameChangeDetector(),
        ]

    def has_changes(self, stored: Dict, new: Dict) -> bool:
        if not new:
            return False

        try:
            return any(detector.detect_changes(stored, new) for detector in self.detectors)
        except Exception as e:
            log.error(f"Error checking for changes: {e}")
            return True

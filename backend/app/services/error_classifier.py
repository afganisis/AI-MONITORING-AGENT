"""Error classification service - converts error messages to error types.

This module contains the ERROR_FILTERS converted from zeroVios.js.
Updated with fix strategies based on Fortex AI REPAIR capabilities.
"""

from dataclasses import dataclass
from typing import Optional, Callable, List
from enum import Enum


class ErrorCategory(str, Enum):
    """Error categories for grouping error types."""
    DATA_INTEGRITY = "data_integrity"
    LOCATION_MOVEMENT = "location_movement"
    STATUS_EVENT = "status_event"
    DIAGNOSTIC = "diagnostic"
    SPEED = "speed"
    AUTHENTICATION = "authentication"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FixStrategy(str, Enum):
    """How the error should be handled/fixed."""
    OBSOLETE = "obsolete"       # Error type no longer exists in Fortex
    INFO_ONLY = "info_only"     # Show as error but don't attempt to fix
    AI_REPAIR = "ai_repair"     # Can be fixed via Fortex AI REPAIR button
    CUSTOM = "custom"           # Requires custom fix logic from PTHORA AI


@dataclass
class ErrorFilter:
    """Represents an error filter for classification."""
    name: str
    key: str
    match: Callable[[str], bool]
    category: ErrorCategory
    severity: ErrorSeverity
    fix_strategy: FixStrategy = FixStrategy.CUSTOM  # Default to custom


# Error filter definitions (converted from zeroVios.js)
# Updated 2026-02-06 based on actual Fortex error types
ERROR_FILTERS: List[ErrorFilter] = [
    # ========================================================================
    # INFO_ONLY - Show as error but don't fix (no fix available)
    # ========================================================================
    ErrorFilter(
        name="SEQUENTIAL ID BREAK WARNING",
        key="sequentialIdBreak",
        match=lambda msg: msg and msg.strip().upper() == "SEQUENTIAL ID BREAK WARNING",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.CRITICAL,
        fix_strategy=FixStrategy.INFO_ONLY
    ),
    ErrorFilter(
        name="ENGINE HOURS HAVE CHANGED AFTER SHUT DOWN WARNING",
        key="engineHoursAfterShutdown",
        match=lambda msg: msg and msg.strip().upper() == "ENGINE HOURS HAVE CHANGED AFTER SHUT DOWN WARNING",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.HIGH,
        fix_strategy=FixStrategy.INFO_ONLY
    ),
    ErrorFilter(
        name="EVENT IS NOT DOWNLOADED",
        key="eventIsNotDownloaded",
        match=lambda msg: msg and msg.strip().upper() == "EVENT IS NOT DOWNLOADED",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.INFO_ONLY
    ),

    # ========================================================================
    # AI_REPAIR - Fixable via Fortex AI REPAIR button click
    # ========================================================================
    ErrorFilter(
        name="NO POWER UP ERROR",
        key="noPowerUpError",
        match=lambda msg: msg and msg.strip().upper() == "NO POWER UP ERROR",
        category=ErrorCategory.DIAGNOSTIC,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.AI_REPAIR
    ),
    ErrorFilter(
        name="TWO IDENTICAL STATUSES ERROR",
        key="twoIdenticalStatusesError",
        match=lambda msg: msg and msg.strip().upper() == "TWO IDENTICAL STATUSES ERROR",
        category=ErrorCategory.STATUS_EVENT,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.AI_REPAIR
    ),
    ErrorFilter(
        name="DRIVING ORIGIN WARNING",
        key="drivingOriginWarning",
        match=lambda msg: msg and msg.strip().upper() == "DRIVING ORIGIN WARNING",
        category=ErrorCategory.LOCATION_MOVEMENT,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.AI_REPAIR
    ),
    ErrorFilter(
        name="MISSING INTERMEDIATE ERROR",
        key="missingIntermediateError",
        match=lambda msg: msg and msg.strip().upper() == "MISSING INTERMEDIATE ERROR",
        category=ErrorCategory.STATUS_EVENT,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.AI_REPAIR
    ),
    ErrorFilter(
        name="NO SHUT DOWN ERROR",
        key="noShutdownError",
        match=lambda msg: msg and msg.strip().upper() == "NO SHUT DOWN ERROR",
        category=ErrorCategory.DIAGNOSTIC,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.AI_REPAIR
    ),

    # ========================================================================
    # CUSTOM - Requires custom PTHORA AI logic
    # ========================================================================
    ErrorFilter(
        name="ODOMETER ERROR",
        key="odometerError",
        match=lambda msg: msg and msg.strip().upper() == "ODOMETER ERROR",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.HIGH,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="LOCATION CHANGED ERROR",
        key="locationChangedError",
        match=lambda msg: msg and msg.strip().upper() == "LOCATION CHANGED ERROR",
        category=ErrorCategory.LOCATION_MOVEMENT,
        severity=ErrorSeverity.HIGH,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="INCORRECT INTERMEDIATE PLACEMENT ERROR",
        key="incorrectIntermediatePlacementError",
        match=lambda msg: msg and msg.strip().upper() == "INCORRECT INTERMEDIATE PLACEMENT ERROR",
        category=ErrorCategory.STATUS_EVENT,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="ENGINE HOURS WARNING",
        key="engineHoursWarning",
        match=lambda msg: msg and msg.strip().upper() == "ENGINE HOURS WARNING",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="EXCESSIVE LOG IN WARNING",
        key="excessiveLogInWarning",
        match=lambda msg: msg and msg.strip().upper() == "EXCESSIVE LOG IN WARNING",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="EXCESSIVE LOG OUT WARNING",
        key="excessiveLogOutWarning",
        match=lambda msg: msg and msg.strip().upper() == "EXCESSIVE LOG OUT WARNING",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="NO DATA IN ODOMETER OR ENGINE HOURS ERROR",
        key="noDataInOdometerOrEngineHours",
        match=lambda msg: msg and msg.strip().upper() == "NO DATA IN ODOMETER OR ENGINE HOURS ERROR",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.CRITICAL,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="LOCATION ERROR",
        key="locationError",
        match=lambda msg: msg and msg.strip().upper() == "LOCATION ERROR",
        category=ErrorCategory.LOCATION_MOVEMENT,
        severity=ErrorSeverity.HIGH,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="LOCATION DID NOT CHANGE WARNING",
        key="locationDidNotChangeWarning",
        match=lambda msg: msg and msg.strip().upper() == "LOCATION DID NOT CHANGE WARNING",
        category=ErrorCategory.LOCATION_MOVEMENT,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="INCORRECT STATUS PLACEMENT ERROR",
        key="incorrectStatusPlacementError",
        match=lambda msg: msg and msg.strip().upper() == "INCORRECT STATUS PLACEMENT ERROR",
        category=ErrorCategory.STATUS_EVENT,
        severity=ErrorSeverity.HIGH,
        fix_strategy=FixStrategy.CUSTOM
    ),
    # Speed errors with startsWith matching
    ErrorFilter(
        name="THE SPEED WAS MUCH HIGHER THAN THE SPEED LIMIT IN",
        key="speedMuchHigherThanLimit",
        match=lambda msg: msg and msg.strip().upper().startswith("THE SPEED WAS MUCH HIGHER THAN THE SPEED LIMIT IN"),
        category=ErrorCategory.SPEED,
        severity=ErrorSeverity.HIGH,
        fix_strategy=FixStrategy.CUSTOM
    ),
    ErrorFilter(
        name="THE SPEED WAS HIGHER THAN THE SPEED",
        key="speedHigherThanLimit",
        match=lambda msg: msg and msg.strip().upper().startswith("THE SPEED WAS HIGHER THAN THE SPEED"),
        category=ErrorCategory.SPEED,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.CUSTOM
    ),

    # ========================================================================
    # OBSOLETE - No longer exist in Fortex (skip these)
    # ========================================================================
    ErrorFilter(
        name="DIAGNOSTIC EVENT",
        key="diagnosticEvent",
        match=lambda msg: msg and msg.strip().upper() == "DIAGNOSTIC EVENT",
        category=ErrorCategory.DIAGNOSTIC,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.OBSOLETE
    ),
    ErrorFilter(
        name="EVENT HAS MANUAL LOCATION",
        key="eventHasManualLocation",
        match=lambda msg: msg and msg.strip().upper() == "EVENT HAS MANUAL LOCATION",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.LOW,
        fix_strategy=FixStrategy.OBSOLETE
    ),
    ErrorFilter(
        name="UNIDENTIFIED DRIVER EVENT",
        key="unidentifiedDriverEvent",
        match=lambda msg: msg and msg.strip().upper() == "UNIDENTIFIED DRIVER EVENT",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        fix_strategy=FixStrategy.OBSOLETE
    ),
]


@dataclass
class ErrorClassification:
    """Result of error classification."""
    key: str
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    fix_strategy: FixStrategy


class ErrorClassifier:
    """Classifies error messages using ERROR_FILTERS."""

    def __init__(self):
        self.filters = ERROR_FILTERS
        # Exclude obsolete filters from active classification
        self.active_filters = [f for f in self.filters if f.fix_strategy != FixStrategy.OBSOLETE]

    def classify(self, error_message: Optional[str]) -> Optional[ErrorClassification]:
        """
        Classify an error message.

        Args:
            error_message: The error message to classify

        Returns:
            ErrorClassification if matched, None otherwise
        """
        if not error_message:
            return None

        # Only use active (non-obsolete) filters
        for filter_def in self.active_filters:
            if filter_def.match(error_message):
                return ErrorClassification(
                    key=filter_def.key,
                    name=filter_def.name,
                    category=filter_def.category,
                    severity=filter_def.severity,
                    fix_strategy=filter_def.fix_strategy
                )

        return None

    def get_filter_by_key(self, key: str) -> Optional[ErrorFilter]:
        """Get error filter by key."""
        for filter_def in self.filters:
            if filter_def.key == key:
                return filter_def
        return None

    def get_all_error_keys(self) -> List[str]:
        """Get list of all active error keys (excluding obsolete)."""
        return [f.key for f in self.active_filters]

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorFilter]:
        """Get all active error filters for a specific category."""
        return [f for f in self.active_filters if f.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorFilter]:
        """Get all active error filters for a specific severity level."""
        return [f for f in self.active_filters if f.severity == severity]

    def get_errors_by_fix_strategy(self, strategy: FixStrategy) -> List[ErrorFilter]:
        """Get all error filters for a specific fix strategy."""
        return [f for f in self.filters if f.fix_strategy == strategy]

    def get_ai_repair_errors(self) -> List[ErrorFilter]:
        """Get all errors that can be fixed via AI REPAIR button."""
        return self.get_errors_by_fix_strategy(FixStrategy.AI_REPAIR)

    def get_info_only_errors(self) -> List[ErrorFilter]:
        """Get all errors that are info only (no fix available)."""
        return self.get_errors_by_fix_strategy(FixStrategy.INFO_ONLY)

    def get_custom_fix_errors(self) -> List[ErrorFilter]:
        """Get all errors that require custom PTHORA AI logic."""
        return self.get_errors_by_fix_strategy(FixStrategy.CUSTOM)

    def is_fixable(self, error_key: str) -> bool:
        """Check if an error type is fixable (AI_REPAIR or CUSTOM)."""
        filter_def = self.get_filter_by_key(error_key)
        if not filter_def:
            return False
        return filter_def.fix_strategy in (FixStrategy.AI_REPAIR, FixStrategy.CUSTOM)


# Global error classifier instance
error_classifier = ErrorClassifier()


# Summary for documentation
"""
ERROR TYPES SUMMARY (Updated 2026-02-06):

OBSOLETE (removed from detection):
- DIAGNOSTIC EVENT
- EVENT HAS MANUAL LOCATION
- UNIDENTIFIED DRIVER EVENT

INFO_ONLY (show but don't fix):
- SEQUENTIAL ID BREAK WARNING
- ENGINE HOURS HAVE CHANGED AFTER SHUT DOWN WARNING
- EVENT IS NOT DOWNLOADED

AI_REPAIR (fixable via Fortex AI REPAIR button):
- NO POWER UP ERROR
- TWO IDENTICAL STATUSES ERROR
- DRIVING ORIGIN WARNING
- MISSING INTERMEDIATE ERROR
- NO SHUT DOWN ERROR

CUSTOM (requires PTHORA AI logic):
- ODOMETER ERROR
- LOCATION CHANGED ERROR
- INCORRECT INTERMEDIATE PLACEMENT ERROR
- ENGINE HOURS WARNING
- EXCESSIVE LOG IN WARNING
- EXCESSIVE LOG OUT WARNING
- NO DATA IN ODOMETER OR ENGINE HOURS ERROR
- LOCATION ERROR
- LOCATION DID NOT CHANGE WARNING
- INCORRECT STATUS PLACEMENT ERROR
- THE SPEED WAS MUCH HIGHER THAN THE SPEED LIMIT IN
- THE SPEED WAS HIGHER THAN THE SPEED
"""

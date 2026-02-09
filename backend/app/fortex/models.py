"""
Pydantic models for Fortex API responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LogCheckError(BaseModel):
    """Individual error from logCheckErrors array"""
    id: Optional[str] = None
    eventCode: Optional[str] = Field(None, alias="eventCode")
    errorTime: Optional[int] = Field(None, alias="errorTime")
    errorMessage: str = Field(None, alias="errorMessage")  # Main error message field
    errorType: Optional[str] = Field(None, alias="errorType")

    # Legacy/alternative field names (for compatibility)
    type: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    error_message: Optional[str] = None
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    log_id: Optional[str] = None
    event_id: Optional[str] = None
    date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # Allow additional fields from API
        populate_by_name = True  # Allow both camelCase and snake_case


class DriverState(BaseModel):
    """Driver state information"""
    account_id: Optional[str] = None
    status: Optional[str] = None

    class Config:
        extra = "allow"


class DriverLog(BaseModel):
    """Driver log entry with errors from smart-analyze endpoint"""
    timezone: Optional[str] = None
    driverId: str = Field(alias="driverId")
    driver_id: Optional[str] = None  # Normalized field
    driver_name: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    driverState: Optional[DriverState] = None
    driverLogs: Optional[List[Dict[str, Any]]] = None
    logCheckErrors: List[LogCheckError] = Field(default_factory=list)
    lastUpdatedAt: Optional[str] = None

    class Config:
        extra = "allow"
        populate_by_name = True

    def __init__(self, **data):
        # Fix driverLogs if it's a dict instead of list
        if 'driverLogs' in data and isinstance(data['driverLogs'], dict):
            # Convert dict to list with single element
            data['driverLogs'] = [data['driverLogs']]

        super().__init__(**data)

        # Normalize driverId to driver_id
        if hasattr(self, 'driverId') and not self.driver_id:
            self.driver_id = self.driverId


class SmartAnalyzeResponse(BaseModel):
    """Response from /monitoring/smart-analyze/:companyId"""
    drivers: List[DriverLog] = Field(default_factory=list)
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    total_errors: int = 0
    cache_timestamp: Optional[str] = None

    class Config:
        extra = "allow"


class CompanySummary(BaseModel):
    """Company summary from monitoring overview"""
    id: str
    name: str
    violations: int = 0
    uncertified: int = 0
    docProblems: int = 0
    total: int = 0
    isError: bool = False

    class Config:
        extra = "allow"


class MonitoringOverview(BaseModel):
    """Response from /monitoring endpoint"""
    totalNumberOfCompany: int = 0
    totalNumberOfError: int = 0
    violations: int = 0
    docProblems: int = 0
    uncertified: int = 0
    companies: List[CompanySummary] = Field(default_factory=list)
    lastUpdatedAt: Optional[str] = None

    class Config:
        extra = "allow"

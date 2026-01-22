Monitoring API Endpoints

  1. GET /monitoring

  Purpose: Retrieves a summary of all companies with their ELD compliance issues (violations, uncertified logs, and document problems).

  Authentication:
  - Authorization Header: y3He9C57ecfmMAsR19 (hardcoded authorization key)
  - x-system-name Header: Required - specifies the tenant/system to query

  Request Example:
  GET /monitoring
  Headers:
    Authorization: y3He9C57ecfmMAsR19
    x-system-name: zero

  Response Format:
{
    "totalNumberOfCompany": 50,
    "totalNumberOfError": 125,
    "violations": 45,
    "docProblems": 30,
    "uncertified": 50,
    "companies": [
      {
        "id": "company-uuid",
        "name": "Company Name",
        "violations": 10,
        "uncertified": 5,
        "docProblems": 8,
        "total": 23,
        "isError": true
      },
      // ... more companies sorted by total errors (descending)
    ],
    "lastUpdatedAt": "2025-10-29T12:00:00Z"
  }
Caching: Results are cached in Redis for 600 seconds (10 minutes)

  Use Cases:
  - Dashboard overview of all companies' compliance status
  - Identify companies needing immediate attention
  - Track total violations across the entire system

  ---
  2. GET /monitoring/smart-analyze/:companyId

  Purpose: Performs deep analysis of a specific company, returning detailed driver-by-driver log check errors and compliance issues for the last 8 days.

  Authentication:
  - Authorization Header: y3He9C57ecfmMAsR19 (hardcoded authorization key)
  - x-system-name Header: Required - specifies the tenant/system to query

  Parameters:
  - companyId (path parameter): UUID of the company to analyze

  Request Example:
  GET /monitoring/smart-analyze/abc123-company-uuid
  Headers:
    Authorization: y3He9C57ecfmMAsR19
    x-system-name: zero

  Response Format:
[
    {
      "timezone": "ET",
      "driverId": "driver-uuid",
      "driverState": {
        "account_id": "driver-uuid",
        "status": "active",
        // ... other driver state fields
      },
      "driverLogs": [
        // Array of daily log summaries
      ],
      "logCheckErrors": [
        {
          "type": "violation",
          "message": "HOS violation details",
          "timestamp": "2025-10-29T10:30:00Z"
          // ... other error details
        }
      ],
      "lastUpdatedAt": "2025-10-29T12:00:00Z"
    },
    // ... one object per driver in the company
  ]
Caching: Results are cached in Redis for 600 seconds (10 minutes)
# ZeroELD Cloud API Documentation

**Base URL:** `https://cloud.zeroeld.us`

**API Type:** PostgREST-based REST API

**Authentication:** Bearer Token (JWT) in `Authorization` header

---

## Table of Contents

1. [Authentication](#authentication)
2. [RPC Endpoints](#rpc-endpoints)
3. [REST Entity Endpoints](#rest-entity-endpoints)
4. [Data Models](#data-models)
5. [Query Syntax](#query-syntax)

---

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Sign In

**Endpoint:** `POST /rest/rpc/sign_in_v2`

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "your_password",
  "parameters": {
    "device_id": "unique_device_identifier",
    "device_name": "macOS 10.15.7 Safari 18.5",
    "location_text": "Address string",
    "ip": "217.29.26.146",
    "location_lat": 42.856753861466665,
    "location_lon": 74.63440487822322
  }
}
```

**Response:** Returns JWT token and user information for authenticated sessions.

---

## RPC Endpoints

These endpoints use POST method and accept JSON request bodies.

### 1. Health Check

**Endpoint:** `POST /rest/rpc/health_check`

**Description:** Check API health status.

**Request Body:** None or empty `{}`

**Response:** Health status

---

### 2. Check App Version

**Endpoint:** `POST /rest/rpc/check_app_version`

**Request Body:**
```json
{
  "company_id": "uuid"
}
```

**Response:**
```json
{
  "app_name": "ZERO ELD",
  "version_android": "1.0.48",
  "version_ios": "1.0.48",
  "force_update_android": true,
  "force_update_ios": true,
  "eld_registration_id": "Q8NC",
  "eld_provider_name": "ZER784",
  "eld_uploads_bucket_name": "uploads-bucket-zero",
  "beta_available": false
}
```

---

### 3. Get Me (Current User)

**Endpoint:** `POST /rest/rpc/get_me`

**Description:** Get current authenticated user information.

**Request Body:** None

**Response:**
```json
{
  "name": "Admin Admin",
  "email": "info@zeroeld.com",
  "username": "info@zeroeld.com",
  "role": "manager",
  "sub_role": null,
  "id": "uuid",
  "company_id": null,
  "driver": null,
  "company": null,
  "driver_state": null,
  "terminal": null,
  "now": "2026-01-01T22:34:50.464176",
  "now_utc": "2026-01-01T22:34:50.464176"
}
```

---

### 4. Get Companies

**Endpoint:** `POST /rest/rpc/get_companies`

**Description:** Get list of companies with pagination and filtering.

**Request Body:**
```json
{
  "p_search_text": "",
  "p_is_active": true,
  "p_limit": 16,
  "p_offset": 0
}
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| p_search_text | string | Search filter text |
| p_is_active | boolean | Filter by active status |
| p_limit | integer | Number of records to return |
| p_offset | integer | Pagination offset |

---

### 5. Get Logs By Day

**Endpoint:** `POST /rest/rpc/get_logs_by_day`

**Description:** Get driver logs for a specific time period.

**Request Body:**
```json
{
  "p_limit": 20,
  "p_offset": 0,
  "p_company_id": "uuid",
  "p_is_active": true,
  "p_order": "asc",
  "p_driver_id": "uuid",
  "p_has_violations": true
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| p_limit | integer | Yes | Number of records to return |
| p_offset | integer | Yes | Pagination offset |
| p_company_id | uuid | Yes | Company identifier |
| p_is_active | boolean | Yes | Filter by active status |
| p_order | string | Yes | Sort order ("asc" or "desc") |
| p_driver_id | uuid | No | Filter by specific driver |
| p_has_violations | boolean | No | Filter to show only logs with violations |

---

### 6. Get Account From Driver ID

**Endpoint:** `POST /rest/rpc/get_account_from_driver_id`

**Description:** Get account information for a specific driver.

**Request Body:**
```json
{
  "p_id": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Driver Name",
  "role": "driver",
  "email": null,
  "active": true,
  "username": "driver_username",
  "driver_id": "uuid",
  "company_id": "uuid",
  "created_at": "2025-10-10T02:51:50.498262",
  "updated_at": "2025-11-10T19:17:29.15424",
  "permissions": null,
  "phone_number": null
}
```

---

### 7. Get Accounts

**Endpoint:** `POST /rest/rpc/get_accounts`

**Description:** Get list of accounts with filtering.

**Request Body:**
```json
{
  "payload": {
    "select": "id,username",
    "company_id": "uuid",
    "order": "username.asc"
  }
}
```

---

## REST Entity Endpoints

These endpoints follow PostgREST conventions with query parameters for filtering, selecting fields, and pagination.

### 1. Company

**Endpoint:** `GET /rest/company`

**Query Parameters:**
```
?id=eq.{uuid}
```

**Response Fields:**
- `id` - UUID
- `company_id` - UUID
- `created_at` - Timestamp
- `updated_at` - Timestamp
- Other company-specific fields

---

### 2. Vehicle

**Endpoint:** `GET /rest/vehicle`

**Query Parameters:**
```
?select=id,name,vin,make,model,year,is_active
&company_id=eq.{uuid}
&is_active=eq.true
&order=name.asc
&offset=0
&limit=400
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Vehicle identifier |
| name | string | Vehicle name/number |
| vin | string | Vehicle Identification Number |
| make | string | Vehicle manufacturer |
| model | string | Vehicle model |
| year | integer | Vehicle year |
| is_active | boolean | Active status |

---

### 3. Driver View

**Endpoint:** `GET /rest/driver_view`

**Query Parameters:**
```
?select=id,first_name,last_name,username,is_active,home_terminal
&company_id=eq.{uuid}
&order=first_name.asc
&id=eq.{uuid}
&offset=0
&limit=400
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Driver identifier |
| first_name | string | Driver's first name |
| last_name | string | Driver's last name |
| username | string | Login username |
| is_active | boolean | Active status |
| home_terminal | uuid | Home terminal reference |

---

### 4. Logs By Driver View

**Endpoint:** `GET /rest/logs_by_driver_view`

**Query Parameters:**
```
?order=last_seen.desc.nullslast
&limit=1000
&and=(is_active.eq.true,company_id.eq.{uuid})
&id=eq.{uuid}
```

**Description:** Aggregated view of driver logs with last activity information.

---

### 5. Vehicles With State View

**Endpoint:** `GET /rest/vehicles_with_state_view`

**Query Parameters:**
```
?company_id=eq.{uuid}
&offset=0
&limit=400
```

**Description:** Vehicles with current state/status information.

---

### 6. Account

**Endpoint:** `GET /rest/account`

**Query Parameters:**
```
?driver_id=eq.{uuid}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Account identifier |
| name | string | Full name |
| role | string | User role (driver, manager, etc.) |
| email | string | Email address |
| active | boolean | Active status |
| username | string | Login username |
| driver_id | uuid | Associated driver ID |
| company_id | uuid | Associated company ID |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update timestamp |
| permissions | object | User permissions |
| phone_number | string | Contact phone |

---

### 7. Terminal

**Endpoint:** `GET /rest/terminal`

**Query Parameters:**
```
?id=eq.{uuid}
```

**Response:**
```json
[{
  "id": "uuid",
  "company_id": "uuid",
  "created_at": "2025-09-17T12:32:17.539056",
  "updated_at": "2025-11-21T18:23:09.663508",
  "street": "2206 Seaver LN",
  "city": "Hoffman Estates",
  "state": "IL",
  "zip": "60169",
  "timezone": "CT",
  "log_start_offset": null,
  "deleted_at": null
}]
```

---

### 8. Driver State

**Endpoint:** `GET /rest/driver_state`

**Query Parameters:**
```
?account_id=eq.{uuid}
```

**Description:** Current state/status of a driver (on duty, off duty, etc.)

---

### 9. Event View

**Endpoint:** `GET /rest/event_view`

**Query Parameters:**
```
?order=created_at.desc,seq_id.desc
&and=(
  account_id.eq.{uuid},
  code.in.(DS_OFF,DS_ON,DS_D,DS_SB,DR_IND_PC,DR_IND_YM),
  status.eq.ACTIVE,
  is_unidentified.eq.false,
  date.lt.2025-12-31,
  company_id.eq.{uuid}
)
&limit=1
&offset=0
```

**Event Codes:**
| Code | Description |
|------|-------------|
| DS_OFF | Duty Status: Off Duty |
| DS_ON | Duty Status: On Duty |
| DS_D | Duty Status: Driving |
| DS_SB | Duty Status: Sleeper Berth |
| DR_IND_PC | Driver Indication: Personal Conveyance |
| DR_IND_YM | Driver Indication: Yard Moves |

---

## Data Models

### User Roles

| Role | Description |
|------|-------------|
| manager | Fleet manager with full access |
| driver | Driver with limited access |

### UUID Format

All identifiers use UUID v4 format:
```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Example: 3e70ad4c-f73c-498e-a48a-62953279e8a7
```

---

## Query Syntax

The API uses PostgREST query syntax:

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| eq | Equals | `id=eq.value` |
| neq | Not equals | `status=neq.inactive` |
| gt | Greater than | `date=gt.2025-01-01` |
| lt | Less than | `date=lt.2025-12-31` |
| gte | Greater than or equal | `count=gte.10` |
| lte | Less than or equal | `count=lte.100` |
| in | In list | `code=in.(A,B,C)` |
| is | Is (for null) | `deleted_at=is.null` |

### Logical Operators

```
?and=(condition1,condition2)
?or=(condition1,condition2)
```

### Ordering

```
?order=field.asc
?order=field.desc
?order=field.desc.nullslast
```

### Pagination

```
?offset=0&limit=400
```

### Field Selection

```
?select=id,name,email
```

---

## Response Headers

| Header | Description |
|--------|-------------|
| Content-Type | `application/json; charset=utf-8` |
| Content-Range | Pagination info (e.g., `0-9/100`) |

---

## Error Handling

Standard HTTP status codes are used:

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## External Services

The application also integrates with:

- **Google Fonts API** - Font loading
- **Google Cloud Storage** - File uploads (`storage.googleapis.com/uploads-bucket-zero`)
- **ipify API** - IP address detection (`api.ipify.org`)

---

## Notes

- All timestamps are in ISO 8601 format
- The API uses HTTP/2 protocol
- CORS is enabled for web client access
- JWT tokens should be refreshed before expiration

# FinGuard_BIL_Hackathon_Team_1
# FinGuard API

A FastAPI-based loan validation platform that uses **Open Policy Agent (OPA)** to evaluate business rules against loan applications. The application also integrates with an external exchange rate service and includes caching, logging, dependency injection, and scalable service architecture.

---

# Features

- FastAPI REST API
- OPA-based rule evaluation
- Pydantic request validation
- Exchange rate lookup service
- In-memory caching with TTL
- Centralized dependency injection
- Structured logging
- Request logging middleware
- OpenAPI / Swagger documentation
- Container-friendly architecture

---

# Architecture

```text
                ┌───────────────┐
                │     Client    │
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │    FastAPI    │
                └───────┬───────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼

 ┌───────────────┐            ┌──────────────────┐
 │ OpaRuleService│            │ExchangeRateService│
 └───────┬───────┘            └─────────┬────────┘
         │                               │
         ▼                               ▼
 ┌───────────────┐              ┌─────────────────┐
 │      OPA      │              │ Frankfurter API │
 └───────────────┘              └─────────────────┘
```

---

# Project Structure

```text
app/
│
├── main.py
│
├── routers/
│   └── rules.py
│
├── models/
│   ├── loan.py
│   └── currency.py
│
├── services/
│   ├── opa_rule_service.py
│   └── exchange_rate.py
│
├── dependencies.py
│
├── policies/
│   └── loan_rules.rego
│
├── lookups/
│   └── country_to_currency.json
│
├── logs/
│   └── app.log
│
└── utils/
    └── logging.py
    └── helper_functions.py
```

---

# Supported Rules

## Rule 1: Minimum Loan Value

Validates that:

```text
loan_value > 25,000 EUR
```

Example response:

```json
{
  "rule_name": "Minimum Loan Value",
  "passed": true,
  "message": "Loan value exceeds minimum threshold"
}
```

---

## Rule 2: Country Currency Validation

Validates that:

```text
Loan currency matches expected country currency.
```

Example:

```json
{
  "country": "Germany",
  "currency": "EUR"
}
```

Passes because Germany maps to EUR.

---

## Rule 3: Asset Coverage Validation

Validates:

```text
asset_value >= 50% of loan_value
```

---

# API Endpoints

## Evaluate Loan Threshold Rule

```http
POST /rules/loan-above-threshold
```

Request:

```json
{
  "country": "Germany",
  "currency": "EUR",
  "loan_value": 50000,
  "asset_value": 30000
}
```

Response:

```json
{
  "passed": true,
  "message": "Loan value exceeds minimum threshold"
}
```

---

## Evaluate Currency Rule

```http
POST /rules/valid-currency
```

Request:

```json
{
  "country": "Germany",
  "currency": "EUR",
  "loan_value": 50000,
  "asset_value": 30000
}
```

---

## Evaluate Asset Coverage Rule

```http
POST /rules/loan-asset-value
```

Request:

```json
{
  "country": "Germany",
  "currency": "EUR",
  "loan_value": 50000,
  "asset_value": 30000
}
```

---

# Data Models

## Currency

```python
class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    JPY = "JPY"
    SEK = "SEK"
    GBP = "GBP"
    PLN = "PLN"
    CHF = "CHF"
    CAD = "CAD"
```

---

## LoanData

```python
class LoanData(BaseModel):

    country: str
    currency: Currency

    loan_value: float
    asset_value: float
```

---

# Exchange Rate Service

The application contains a reusable ExchangeRateService that:

- Retrieves exchange rates from Frankfurter
- Uses TTL-based caching
- Supports retries
- Gracefully handles API failures
- Can return stale cache values during outages

Example:

```python
rate = exchange_rate_service.get_rate(
    Currency.USD,
    Currency.EUR,
)
```

Returns:

```python
ExchangeRate(
    source_currency="USD",
    target_currency="EUR",
    rate=0.85
)
```

---

# Dependency Injection

Services are instantiated once during FastAPI startup.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.opa_rule_service = OpaRuleService()

    app.state.exchange_rate_service = (
        ExchangeRateService()
    )

    yield
```

Dependency:

```python
def get_exchange_rate_service(
    request: Request,
) -> ExchangeRateService:

    return request.app.state.exchange_rate_service
```

---

# Logging

Logs are written to:

```text
logs/app.log
```

Example log entry:

```text
2026-08-05 09:30:02 | INFO | routers.rules |
Evaluating rule loan-above-threshold
```

Features:

- Request logging
- Startup logging
- Service logging
- Exception stack traces

---

# Running OPA

Example Docker Compose:

```yaml
services:

  opa:
    image: openpolicyagent/opa:latest

    command:
      - run
      - --server
      - --addr=0.0.0.0:8181
      - /policies

    volumes:
      - ./policies:/policies:ro
      - ./lookups:/lookups:ro

    ports:
      - "8181:8181"
```

---

# Running the Application

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

# Scalability Considerations

## Current Design

Suitable for:

- Single loan validations
- Small batch evaluations
- Low to moderate request volumes

---

## Future Improvements

### Redis Cache

Replace:

```python
TTLCache
```

with:

```text
Redis
```

for multi-pod deployments.

---

### Asynchronous HTTP

Replace:

```python
requests
```

with:

```python
httpx.AsyncClient
```

for improved throughput.

---

### OPA Scaling

Deploy multiple OPA replicas behind a load balancer.

```text
FastAPI
    |
    +---- OPA Pod 1
    +---- OPA Pod 2
    +---- OPA Pod 3
```

---

### Bulk Processing

For very large datasets:

```text
Upload
  ↓
Queue
  ↓
Worker
  ↓
OPA
  ↓
Results Store
```

instead of processing everything synchronously.

---

# Future Enhancements

- Redis distributed caching
- Distributed locking
- Prometheus metrics
- OpenTelemetry tracing
- JWT authentication
- Role-based access control
- Background job processing
- Kubernetes deployment
- CI/CD pipeline integration

---

# Technology Stack

- FastAPI
- Pydantic
- Open Policy Agent (OPA)
- Python 3.11+
- Requests / HTTPX
- CacheTools
- Docker
- Uvicorn

---

# License

Internal use only.

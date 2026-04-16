# SANJAYA Platform Security & Observability Implementation Guide

## Overview
This document describes the implementation of platform security and observability features for the SANJAYA system.

---

## 1. Platform Security

### 1.1 Authentication & Authorization

#### JWT (JSON Web Token)
- **Implementation**: `sanjaya/security.py`
- **Features**:
  - Token generation with user claims (user_id, role, mfa_verified)
  - Token verification and validation
  - Token refresh mechanism
  - Configurable expiration (default: 24 hours)

**Usage**:
```python
from sanjaya.security import generate_token, verify_token, UserRole

# Generate token
token = generate_token(user_id="user123", role=UserRole.ANALYST, mfa_verified=True)

# Verify token
payload = verify_token(token)
if payload:
    print(f"Valid token for user: {payload['user_id']}")
```

#### Role-Based Access Control (RBAC)
- **Roles**: ADMIN, MANAGER, ANALYST, USER, VIEWER
- **Permissions**: Dynamically assigned based on role
- **Implementation**: Role decorators for endpoint protection

**Permission Matrix**:
```
ADMIN    → read, write, delete, manage_users, manage_roles
MANAGER  → read, write, delete, manage_analysts
ANALYST  → read, write, create_reports
USER     → read, write
VIEWER   → read
```

**Usage**:
```python
from sanjaya.security import require_role, UserRole

@app.get("/admin/users")
@require_role(UserRole.ADMIN, UserRole.MANAGER)
async def list_users(user_role: UserRole = Depends(get_current_user_role)):
    return {"users": [...]}
```

### 1.2 Multi-Factor Authentication (MFA)

- **Method**: OTP (One-Time Password) via email
- **OTP Length**: 6 digits
- **Validity**: 5 minutes (300 seconds)
- **Implementation**: `sanjaya/security.py::MFAService`

**Flow**:
1. User initiates login
2. System generates 6-digit OTP
3. OTP sent to user's registered email
4. User enters OTP
5. System verifies OTP and issues JWT token

**Usage**:
```python
from sanjaya.security import MFAService

# Generate OTP
otp = MFAService.generate_otp()  # Returns: "123456"

# Send OTP
MFAService.send_otp_via_email(email="user@example.com", otp=otp)

# Verify OTP
is_valid = MFAService.verify_otp(stored_otp=otp, provided_otp="123456")
```

### 1.3 OAuth2 - Google Login

- **Provider**: Google OAuth 2.0
- **Configuration**:
  - `GOOGLE_CLIENT_ID`: Your Google OAuth app ID
  - `GOOGLE_CLIENT_SECRET`: Your Google OAuth secret
  - `GOOGLE_REDIRECT_URI`: Callback URL (http://localhost:8000/auth/google/callback)

**TODO**: Implement using `authlib` or `python-jose`

### 1.4 PII Encryption

- **Method**: Fernet (symmetric encryption)
- **Key Management**: `ENCRYPTION_KEY` environment variable
- **Database Storage**: All PII encrypted before storage

**Sensitive Fields**:
- Email addresses
- Phone numbers
- Full names
- API keys (NEVER store unencrypted)
- Financial information

**Usage**:
```python
from sanjaya.security import encrypt_pii, decrypt_pii

# Store PII
encrypted_email = encrypt_pii("user@example.com")
db.save(email=encrypted_email)

# Retrieve PII
encrypted_data = db.get_email()
plain_email = decrypt_pii(encrypted_data)
```

**Security Negations**:
- ❌ PII must NOT be exposed in Frontend API calls
- ❌ Encryption keys must NOT be hardcoded
- ❌ Passwords must be hashed (use bcrypt)
- ✅ All PII is encrypted in database
- ✅ API responses sanitized to exclude sensitive fields
- ✅ HTTPS only for all API calls

---

## 2. Observability Stack

### 2.1 Logging - Loki

**What is Loki?**
- Horizontally scalable log aggregator similar to Prometheus
- Creates indexes on labels instead of full text
- Efficient log storage and querying
- Easy integration with Grafana

**Setup**:
```bash
cd d:\S\SANJAYA
docker-compose -f docker-compose.observability.yml up loki
```

**JSON Logging Configuration**:
```python
from sanjaya.observability import setup_json_logging

logger = setup_json_logging("sanjaya-api")
logger.info("Application started", extra={
    "trace_id": "abc123",
    "span_id": "def456",
    "service": "sanjaya-api",
})
```

**Log Fields**:
- `timestamp`: ISO 8601 format
- `level`: INFO, WARNING, ERROR, DEBUG
- `service`: sanjaya-api, sanjaya-worker, etc.
- `trace_id`: Distributed trace identifier
- `span_id`: Request span identifier
- `message`: Log message

### 2.2 Logging - Elasticsearch + Kibana (Alternative)

**What is Elasticsearch?**
- Full-text search engine for logs
- Powerful querying capabilities
- Long-term log storage
- Integration with Kibana for visualization

**Setup**:
```bash
docker-compose -f docker-compose.observability.yml up elasticsearch kibana
```

**Access Kibana**: http://localhost:5601

### 2.3 Request Tracing - Jaeger

**What is Jaeger?**
- Distributed tracing platform
- Traces requests across all microservices
- Identifies bottlenecks and latency issues
- End-to-end request visibility

**Trace Components**:
- **Trace ID**: Unique identifier for entire request flow
- **Span ID**: Individual operation within a trace
- **Service**: Which microservice the span belongs to

**Setup**:
```bash
docker-compose -f docker-compose.observability.yml up jaeger
```

**Access Jaeger UI**: http://localhost:16686

**Usage**:
```python
from sanjaya.observability import RequestTracer

tracer = RequestTracer()
trace_context = tracer.start_trace()

# Pass trace context to downstream services
headers = {
    "X-Trace-ID": trace_context["trace_id"],
    "X-Span-ID": trace_context["span_id"],
}
```

### 2.4 Metrics - Prometheus + Grafana

**What is Prometheus?**
- Time-series database for metrics
- Scrapes metrics from applications
- Powerful query language (PromQL)
- Alerting capabilities

**What is Grafana?**
- Visualization platform for metrics
- Real-time dashboards
- Pre-configured with Prometheus, Loki, Elasticsearch
- Alerting dashboards

**Default Credentials**:
- Username: admin
- Password: admin

**Access**: http://localhost:3000

**Pre-configured Datasources**:
1. Loki (Logs)
2. Prometheus (Metrics)
3. Elasticsearch (Alternative logs)
4. Jaeger (Traces)

### 2.5 Async Job Monitoring

**What is Async Job Monitoring?**
- Tracks background job execution
- Workers (Celery, RQ, etc.)
- Long-running processes

**Usage**:
```python
from sanjaya.observability import AsyncJobMonitor, StructuredLogger, setup_json_logging

logger = StructuredLogger(setup_json_logging("sanjaya-worker"))
monitor = AsyncJobMonitor(logger)

# Start job
job_id = "job-12345"
monitor.start_job(job_id, job_type="risk_prediction", shipment_id="ship-001")

try:
    result = perform_prediction(...)
    monitor.complete_job(job_id, result=result)
except Exception as e:
    monitor.fail_job(job_id, error=str(e))
```

**Monitored Events**:
- Job start / completion / failure
- Job duration
- Error messages
- Result status

---

## 3. Quick Start - Observability Stack

### Start All Services
```bash
cd d:\S\SANJAYA
docker-compose -f docker-compose.observability.yml up -d
```

### Access Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Jaeger**: http://localhost:16686
- **Kibana**: http://localhost:5601 (if using Elasticsearch)
- **Prometheus**: http://localhost:9090

### View Logs in Grafana
1. Go to Grafana → Explore
2. Select Loki datasource
3. Query logs: `{service="sanjaya-api"}`

### View Traces in Jaeger
1. Go to Jaeger UI
2. Select service: "sanjaya-api"
3. Filter by trace ID or view all traces

---

## 4. Environment Variables

### Security
```
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
JWT_EXPIRATION_HOURS=24
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Observability
```
LOKI_URL=http://localhost:3100
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
ELASTICSEARCH_URL=http://localhost:9200
KIBANA_URL=http://localhost:5601
LOG_LEVEL=INFO
LOG_OUTPUT_PATH=logs/
```

---

## 5. Security Best Practices

1. **Never commit secrets** to git (use `.env` with placeholders)
2. **Rotate JWT secrets** regularly
3. **Use HTTPS only** in production
4. **Enable CORS properly** - don't use `*`
5. **Validate all inputs** to prevent injection attacks
6. **Rate limit** endpoints to prevent brute force
7. **Log security events** (failed logins, permission denials)
8. **Monitor for anomalies** in metrics and traces

---

## 6. Troubleshooting

### Issue: Loki not storing logs
**Solution**: Check Loki config at `docker/loki-config.yml`, ensure permissions on `/loki` directory

### Issue: Grafana can't connect to Loki
**Solution**: Verify Loki is running: `docker ps | grep loki`, check network: `docker-compose logs loki`

### Issue: Jaeger traces not appearing
**Solution**: Ensure tracer client is configured, check `JAEGER_AGENT_HOST` and `JAEGER_AGENT_PORT`

### Issue: High memory usage
**Solution**: Lower Prometheus retention: `--storage.tsdb.retention.size=10GB`

---

## 7. Next Steps

1. Implement Google OAuth callback handler
2. Integrate password hashing (bcrypt)
3. Create authentication middleware for FastAPI
4. Set up rate limiting (slowapi)
5. Configure prod-grade encryption key rotation
6. Create alerting rules in Prometheus
7. Build custom Grafana dashboards
8. Deploy observability stack to EC2

---

**Last Updated**: 2026-04-16
**Version**: 1.0

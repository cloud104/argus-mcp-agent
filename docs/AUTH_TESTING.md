# Testing Authentication System

## OAuth2 + JWT Authentication with PostgreSQL

The OAuth2 + JWT authentication system has been fully implemented with **PostgreSQL** database support for multi-pod Kubernetes environments.

### Implemented Components

1. **Backend Auth Module (`app/auth/`)**:
   - `security.py`: JWT token creation/validation and password hashing (bcrypt)
   - `models.py`: Pydantic models (User, UserInDB, Token, UserCreate, etc.)
   - `database.py`: **PostgreSQL async database** with connection pooling (asyncpg)
   - `dependencies.py`: FastAPI dependencies (get_current_user, require_role)
   - `routes.py`: Authentication endpoints (login, refresh, me, change-password, user management)

2. **Protected API Endpoints (`app/api/routes.py`)**:
   - All analysis endpoints now require authentication
   - `/initial-analysis`, `/deep-dive`, `/explain-log-line`, `/chat` protected

3. **MCP Server Authentication (`tools/`)**:
   - `auth.py`: JWT validation utilities for MCP server
   - `server.py`: Authentication middleware protecting `/mcp/*` endpoints

4. **Configuration**:
   - JWT variables added to `.env` and `.env.example`
   - PostgreSQL configuration added to all environments
   - Dependencies added to `requirements.txt`: `python-jose[cryptography]`, `passlib`, `asyncpg`, `psycopg2-binary`
   - Default admin user created on first startup (username: admin, password: admin123)

5. **Infrastructure**:
   - Docker Compose updated with PostgreSQL 16 service
   - Kubernetes deployment for PostgreSQL (`k8s/dev/postgres-deployment.yaml`)
   - Persistent storage for PostgreSQL data
   - Health checks and connection pooling

### Testing the Authentication System

#### Prerequisites

**Option 1: Docker Compose (Recommended)**

```bash
# Start all services including PostgreSQL
docker-compose up

# Services will start in this order:
# 1. PostgreSQL (port 5432)
# 2. ChromaDB (port 8001)
# 3. MCP Server (port 8002) - after PostgreSQL is ready
# 4. Main App (port 8000) - after MCP Server is healthy
```

**Option 2: Local Development**

```bash
# 1. Start PostgreSQL locally
docker run -d \
  --name argus-postgres \
  -e POSTGRES_USER=argus \
  -e POSTGRES_PASSWORD=argus123 \
  -e POSTGRES_DB=argus_auth \
  -p 5432:5432 \
  postgres:16-alpine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Update .env to use localhost
# POSTGRES_HOST=localhost

# 4. Start servers in separate terminals:

# Terminal 1 - MCP Server
python tools/server.py

# Terminal 2 - Main App
python main.py
```

**Option 3: Kubernetes**

```bash
# Apply all configurations
kubectl apply -f k8s/dev/

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app=argus-postgres -n argus-dev
kubectl wait --for=condition=ready pod -l app=argus-mcp-server -n argus-dev
kubectl wait --for=condition=ready pod -l app=argus-app -n argus-dev

# Port forward to access locally
kubectl port-forward -n argus-dev svc/argus-app 8000:8000
```

#### Test 1: Login and Get Tokens

```bash
# Login with default admin credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Expected response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }

# Save the access_token for next tests
export TOKEN="<access_token_here>"
```

#### Test 2: Access Protected Endpoint (Authenticated)

```bash
# Get current user info
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
# {
#   "username": "admin",
#   "email": "admin@argus.local",
#   "full_name": "Default Administrator",
#   "role": "admin",
#   "disabled": false
# }
```

#### Test 3: Access Protected Endpoint (Unauthenticated - Should Fail)

```bash
# Try to access analysis endpoint without token
curl -X POST http://localhost:8000/initial-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "msg": "Analyze logs",
    "index": "logs_protheus",
    "window": "2h",
    "session_id": "test123"
  }'

# Expected response: 401 Unauthorized
# {
#   "detail": "Not authenticated"
# }
```

#### Test 4: Access Protected Endpoint (Authenticated)

```bash
# Access analysis endpoint with token
curl -X POST http://localhost:8000/initial-analysis \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "msg": "Analyze logs",
    "index": "logs_protheus",
    "window": "2h",
    "session_id": "test123"
  }'

# Expected: Normal response from the analysis endpoint
```

#### Test 5: MCP Server Authentication

```bash
# Try to access MCP endpoint without token (should fail)
curl -X GET http://localhost:8002/mcp/ \
  -H "Content-Type: application/json"

# Expected response: 401 Unauthorized
# {
#   "detail": "Invalid or missing authentication token"
# }

# Access MCP endpoint with token (should work)
curl -X GET http://localhost:8002/mcp/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: MCP server capabilities/tools list
```

#### Test 6: Refresh Token

```bash
# Use refresh token to get new access token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token_from_login>"
  }'

# Expected: New access and refresh tokens
```

#### Test 7: Create New User (Admin Only)

```bash
# Create a developer user
curl -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "dev1",
    "email": "dev1@example.com",
    "password": "devpassword123",
    "full_name": "Developer One",
    "role": "developer"
  }'

# Expected: User created successfully
```

#### Test 8: Change Password

```bash
# Change current user's password
curl -X POST http://localhost:8000/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "old_password": "admin123",
    "new_password": "newSecurePassword123!"
  }'

# Expected: Password changed successfully
```

#### Test 9: Health Checks (Public - No Auth Required)

```bash
# App health checks
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/startup

# MCP server health checks
curl http://localhost:8002/health/live
curl http://localhost:8002/health/ready
curl http://localhost:8002/health/startup

# All should return 200 OK without authentication
```

### User Roles

The system supports three roles:

1. **admin**: Full access to all endpoints + user management
2. **developer**: Access to analysis endpoints (no user management)
3. **viewer**: Read-only access (can view but not create/modify)

### Default Users

On first startup, the system creates a default admin user:
- Username: `admin`
- Password: `admin123`
- Email: `admin@argus.local`

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

### Security Configuration

JWT Configuration in `.env`:
- `JWT_SECRET_KEY`: Secret key for signing tokens (change in production!)
- `JWT_ALGORITHM`: HS256 (default)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: 30 minutes (default)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: 7 days (default)

### Database

User data is stored in **PostgreSQL** with the following configuration:

**Development (Docker Compose):**
- Host: `argus-postgres` (container name)
- Port: `5432`
- Database: `argus_auth`
- User: `argus`
- Password: `argus123`

**Kubernetes:**
- Host: `argus-postgres.argus-dev.svc.cluster.local`
- Persistent storage: 2Gi PVC
- Health checks and automatic restarts

**Connection Pooling:**
- Min connections: 2
- Max connections: 10
- Automatic reconnection on failure

### Why PostgreSQL Instead of SQLite?

**SQLite limitations in Kubernetes:**
- ❌ Each pod has its own file system → different user databases per pod
- ❌ No shared state between replicas
- ❌ Data loss on pod restart (unless using PVC, but still isolated)

**PostgreSQL advantages:**
- ✅ Centralized database accessible by all pods
- ✅ Horizontal scaling with multiple app replicas
- ✅ ACID transactions and data consistency
- ✅ Production-ready for cloud-native deployments

### Next Steps

**Completed:**
- ✅ Phase 1: Auth Backend with PostgreSQL
- ✅ Phase 2: Protected App API endpoints
- ✅ Phase 3: Protected MCP Server endpoints
- ✅ Infrastructure: Docker Compose + Kubernetes deployments

**Remaining:**
- ⏳ Phase 4: Frontend authentication (Angular auth service, login component, interceptor)
- ⏳ Phase 5: Kubernetes Ingress configuration with TLS
- ⏳ Phase 6: Additional security (CORS, rate limiting, logging)
- ⏳ Phase 7: Automated tests and API documentation

### Troubleshooting

**Issue**: 401 Unauthorized even with valid token
- Check that `JWT_SECRET_KEY` is the same in both app and MCP server
- Verify token hasn't expired (default: 30 minutes)
- Check Authorization header format: `Bearer <token>`
- Ensure both services can reach PostgreSQL

**Issue**: Database connection errors
- **Docker Compose**: Check that `argus-postgres` container is running and healthy
- **Kubernetes**: Verify PostgreSQL pod is ready: `kubectl get pods -n argus-dev`
- **Local dev**: Ensure PostgreSQL is accessible on `localhost:5432`
- Check credentials in `.env` or Kubernetes secrets

**Issue**: Import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that `python-jose[cryptography]`, `passlib`, `asyncpg`, and `psycopg2-binary` are installed
- For Docker: Rebuild images with `docker-compose build`

**Issue**: "Table does not exist" errors
- The app automatically creates tables on first startup
- Check app logs for initialization errors
- Manually verify database: `docker exec -it argus-postgres psql -U argus -d argus_auth -c '\dt'`

**Issue**: Multiple admin users created
- This happens if PostgreSQL data is wiped between restarts
- Use persistent volumes in production to preserve data
- Docker Compose and Kubernetes configs already include persistent storage

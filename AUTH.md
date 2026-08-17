# Authentication & Authorization Guide

This document outlines how to add authentication and authorization to the K8s Toy API in a production-ready manner.

## Current State

- **Health endpoint** (`/api/v1/healthz`) - No auth required (needed for k8s probes)
- **All other endpoints** - Currently unauthenticated

## When to Add Auth

Consider adding authentication when:
- The API is exposed outside a trusted network
- Multiple users/services need different access levels
- You need audit trails of who did what
- Compliance requires authentication

## Authentication Options

### 1. API Keys (Simplest)

**Best for:** Service-to-service communication, simple scenarios

**Pros:**
- Simple to implement
- No external dependencies
- Works well for machine-to-machine auth

**Cons:**
- No built-in expiration
- Hard to rotate without downtime
- No user identity/claims
- Must manage key storage securely

**Implementation:**

```python
# app.py additions
from fastapi import Header, HTTPException, Depends
from typing import Annotated
import secrets

# Store API keys (in production: use a database or secret manager)
VALID_API_KEYS = {
    "service-a": "key-abc123...",  # Hash these!
    "service-b": "key-def456...",
}

async def verify_api_key(x_api_key: Annotated[str, Header()]) -> str:
    """Verify API key and return the service identity."""
    if x_api_key not in VALID_API_KEYS.values():
        raise HTTPException(status_code=401, detail="Invalid API key")
    # Return the service name for the key
    for service, key in VALID_API_KEYS.items():
        if secrets.compare_digest(key, x_api_key):
            return service
    raise HTTPException(status_code=401, detail="Invalid API key")

# Apply to protected endpoints
@app.get("/items")
async def list_items(
    service: Annotated[str, Depends(verify_api_key)]
) -> list[Item]:
    # service contains the authenticated caller identity
    ...
```

**Kubernetes setup:**
```yaml
# api-keys-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
type: Opaque
stringData:
  service-a: "key-abc123..."
  service-b: "key-def456..."
```

### 2. JWT Tokens (Recommended for most cases)

**Best for:** User authentication, microservices, OAuth2/OIDC flows

**Pros:**
- Self-contained (no DB lookup per request)
- Supports expiration and refresh tokens
- Can carry user claims (roles, permissions)
- Industry standard (RFC 7519)
- Works with OAuth2/OIDC providers

**Cons:**
- Can't revoke tokens before expiry (without a blocklist)
- Tokens can grow large with many claims
- Need secure key management

**Implementation:**

Dependencies:
```toml
# pyproject.toml
dependencies = [
    ...
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
]
```

Code:
```python
# app.py additions
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # From k8s Secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    username: str
    roles: list[str] = []

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> TokenData:
    """Verify JWT token and return token data."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        roles: list[str] = payload.get("roles", [])
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return TokenData(username=username, roles=roles)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Optional: role-based access control
def require_role(required_role: str):
    async def role_checker(token_data: Annotated[TokenData, Depends(verify_token)]):
        if required_role not in token_data.roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token_data
    return role_checker

# Apply to endpoints
@app.get("/items")
async def list_items(
    token_data: Annotated[TokenData, Depends(verify_token)]
) -> list[Item]:
    # token_data.username contains authenticated user
    ...

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: str,
    token_data: Annotated[TokenData, Depends(require_role("admin"))]
) -> dict[str, str]:
    # Only users with "admin" role can delete
    ...

# Login endpoint to issue tokens
@app.post("/login")
async def login(username: str, password: str):
    # Verify credentials against database
    # In production: use proper password hashing
    user = await verify_user_credentials(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": username, "roles": user.roles},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

**Kubernetes setup:**
```yaml
# jwt-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: jwt-secret
type: Opaque
stringData:
  JWT_SECRET_KEY: "your-secret-key-min-32-chars"  # Generate with: openssl rand -hex 32

---
# deployment.yaml (add to env section)
env:
  - name: JWT_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: jwt-secret
        key: JWT_SECRET_KEY
```

### 3. OAuth2 / OIDC with External Provider (Production-grade)

**Best for:** Enterprise apps, SSO, delegated authentication

**Pros:**
- Offload user management to identity provider
- Support for MFA, password policies
- SSO across multiple apps
- Industry standard (Google, GitHub, Okta, Auth0, Keycloak)

**Cons:**
- External dependency
- More complex setup
- Network calls to verify tokens (unless using JWT)

**Common Providers:**
- **Keycloak** - Self-hosted, open source, full-featured
- **Auth0** - Managed service, easy setup
- **Okta** - Enterprise-focused
- **Google/GitHub** - For public apps
- **AWS Cognito** - If on AWS

**Implementation with FastAPI OAuth2:**

Dependencies:
```toml
dependencies = [
    ...
    "authlib>=1.3",
    "python-jose[cryptography]>=3.3",
]
```

Code:
```python
# app.py additions
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

# OAuth2 configuration
oauth = OAuth()
oauth.register(
    name='keycloak',
    client_id=os.getenv('OAUTH_CLIENT_ID'),
    client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
    server_metadata_url=os.getenv('OAUTH_DISCOVERY_URL'),  # e.g., Keycloak's .well-known/openid-configuration
    client_kwargs={'scope': 'openid email profile'}
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SESSION_SECRET_KEY')
)

# Verify tokens from the OAuth provider
async def verify_oauth_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """Verify OAuth2/OIDC token."""
    token = credentials.credentials

    # Option 1: JWT validation (if provider uses JWTs)
    # Fetch JWKS from provider's .well-known/jwks.json
    # Validate signature, expiry, audience, issuer

    # Option 2: Introspection endpoint
    # Call provider's token introspection endpoint
    # More reliable but requires network call

    try:
        # Example with JWT validation
        payload = jwt.decode(
            token,
            jwks_client.get_signing_key_from_jwt(token).key,
            algorithms=["RS256"],
            audience=os.getenv('OAUTH_CLIENT_ID'),
            issuer=os.getenv('OAUTH_ISSUER')
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/items")
async def list_items(
    user: Annotated[dict, Depends(verify_oauth_token)]
) -> list[Item]:
    # user contains claims from the token (sub, email, roles, etc.)
    ...
```

**Kubernetes setup with Keycloak:**
```yaml
# oauth-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: oauth-secret
type: Opaque
stringData:
  OAUTH_CLIENT_ID: "toy-api"
  OAUTH_CLIENT_SECRET: "client-secret-from-keycloak"
  OAUTH_DISCOVERY_URL: "https://keycloak.example.com/realms/myrealm/.well-known/openid-configuration"
  OAUTH_ISSUER: "https://keycloak.example.com/realms/myrealm"
  SESSION_SECRET_KEY: "session-secret-min-32-chars"
```

### 4. mTLS (Mutual TLS)

**Best for:** Service mesh, high-security environments, zero-trust networks

**Pros:**
- Certificate-based auth (no passwords)
- Built into TLS layer
- Strong cryptographic guarantees
- Works well with service meshes (Istio, Linkerd)

**Cons:**
- Complex certificate management
- Requires PKI infrastructure
- Harder to debug

**Implementation:**

Typically handled at the service mesh or ingress level, not in application code. The service mesh terminates mTLS and passes the verified client identity as a header.

```python
# app.py - if using a service mesh
async def verify_mtls_identity(
    x_client_cert_dn: Annotated[str | None, Header()] = None
) -> str:
    """Extract client identity from mTLS cert (injected by service mesh)."""
    if not x_client_cert_dn:
        raise HTTPException(status_code=401, detail="No client certificate")
    # Parse the DN to extract CN or other identity fields
    return x_client_cert_dn

@app.get("/items")
async def list_items(
    client_identity: Annotated[str, Depends(verify_mtls_identity)]
) -> list[Item]:
    ...
```

**Service mesh handles the actual mTLS:**
- Istio, Linkerd, or Consul Connect
- Automatically rotates certificates
- Enforces mTLS between services

## Recommended Architecture

### Development/Internal Tools
- Start with no auth or simple API keys
- Focus on functionality first

### Production SaaS
- JWT with your own auth system, or
- OAuth2/OIDC with Auth0/Keycloak
- Consider adding rate limiting (SlowAPI, Redis-based)

### Enterprise/B2B
- OAuth2/OIDC with enterprise SSO (Okta, Azure AD)
- Support SAML if required
- Audit logging of all authenticated actions

### Microservices (service-to-service)
- mTLS via service mesh (best), or
- API keys with rotation, or
- Service accounts with short-lived JWT tokens

## Implementation Checklist

When adding auth to this API:

1. **Choose auth method** based on use case
2. **Add dependencies** to pyproject.toml
3. **Create Kubernetes Secrets** for keys/credentials
4. **Update app.py:**
   - Add auth verification function
   - Apply `Depends()` to protected endpoints
   - Keep `/healthz` unauthenticated
   - Add login/token endpoint if using JWT
5. **Update deployment.yaml** to inject secrets as env vars
6. **Add tests** for:
   - Authenticated requests (valid token)
   - Unauthenticated requests (401)
   - Invalid tokens (401)
   - Insufficient permissions (403)
   - Health endpoint still works without auth
7. **Update README** with auth instructions
8. **Add metrics** for auth failures
9. **Consider rate limiting** to prevent brute force

## Security Best Practices

1. **Never commit secrets** - use k8s Secrets or external secret managers (Vault, AWS Secrets Manager, GCP Secret Manager)
2. **Use HTTPS** in production - terminate TLS at ingress or load balancer
3. **Short token expiry** - 15-30 minutes for access tokens, use refresh tokens
4. **Hash API keys** - never store in plaintext
5. **Rotate secrets regularly** - especially after personnel changes
6. **Audit logs** - log auth failures and suspicious activity
7. **Rate limiting** - prevent brute force attacks
8. **CORS configuration** - restrict origins if serving web clients
9. **Secure transport** - always use TLS/HTTPS
10. **Secret scanning** - use tools like git-secrets, truffleHog

## Testing Auth

```bash
# With API key
curl -H "X-API-Key: key-abc123..." http://localhost:8000/api/v1/items

# With JWT
TOKEN=$(curl -X POST http://localhost:8000/login \
  -d "username=admin&password=secret" | jq -r .access_token)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/items

# Health check (no auth)
curl http://localhost:8000/api/v1/healthz
```

## Further Reading

- [FastAPI Security docs](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)

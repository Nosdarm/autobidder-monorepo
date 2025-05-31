import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if using a fixture that provides a session
from jose import jwt
from typing import Dict

# Assuming your FastAPI app instance is accessible for TestClient
# This might be defined in conftest.py or you might need to import it from app.main
from app.main import app # Adjust if your app instance is elsewhere
from app.config import settings # For JWT secret and algorithm
from app.models.user import AccountType as UserAccountTypeEnum, User as UserModel
from app.models.profile import Profile # Added import for Profile model
from app.schemas.user import UserOut as UserOutSchema # For response validation
from app.schemas.auth import TokenResponse # For login response validation

# If conftest.py provides a client fixture, it might be named 'client' or 'test_client'
# For now, let's instantiate one directly or assume it's provided by conftest.py

# Helper function to clear users from a mock DB or reset state if needed
# This would depend on how the DB is mocked/managed by fixtures.
# For this example, we'll assume tests are isolated or fixtures handle cleanup.

@pytest.fixture(scope="module")
def client() -> TestClient:
    # If conftest.py doesn't provide a client, this is a basic way to get one.
    # Ideally, conftest.py handles overriding dependencies like get_db for tests.
    return TestClient(app)

# Fixture to generate unique user data
@pytest.fixture
def unique_user_email(request) -> str:
    return f"testuser_{request.node.name}@example.com"

@pytest.fixture
def individual_user_payload(unique_user_email: str) -> Dict[str, str]:
    return {
        "email": unique_user_email,
        "password": "testpassword123",
        "account_type": UserAccountTypeEnum.INDIVIDUAL.value
    }

@pytest.fixture
def agency_user_payload(unique_user_email: str) -> Dict[str, str]:
    return {
        "email": unique_user_email,
        "password": "testpassword123",
        "account_type": UserAccountTypeEnum.AGENCY.value
    }

def test_register_individual_user(client: TestClient, individual_user_payload: Dict[str, str], db: Session): # Assuming db fixture from conftest.py
    response = client.post("/auth/register", json=individual_user_payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == individual_user_payload["email"]
    assert data["role"] == "user" # Default for individual
    assert data["account_type"] == UserAccountTypeEnum.INDIVIDUAL.value
    assert "id" in data

    # Verify in DB (this part needs a real or well-mocked DB session from a fixture)
    user_in_db = db.query(UserModel).filter(UserModel.email == individual_user_payload["email"]).first()
    assert user_in_db is not None
    assert user_in_db.role == "user"
    assert user_in_db.account_type == UserAccountTypeEnum.INDIVIDUAL
    assert user_in_db.is_verified is False # Assuming default is False

    # Verify default profile creation
    profile_in_db = db.query(Profile).filter(Profile.user_id == user_in_db.id).first()
    assert profile_in_db is not None
    assert profile_in_db.name == "Default Profile"
    assert profile_in_db.profile_type == "personal"
    assert profile_in_db.user_id == user_in_db.id

def test_register_agency_user(client: TestClient, agency_user_payload: Dict[str, str], db: Session):
    response = client.post("/auth/register", json=agency_user_payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == agency_user_payload["email"]
    assert data["role"] == "super_admin" # Default for agency
    assert data["account_type"] == UserAccountTypeEnum.AGENCY.value
    assert "id" in data

    # Verify in DB
    user_in_db = db.query(UserModel).filter(UserModel.email == agency_user_payload["email"]).first()
    assert user_in_db is not None
    assert user_in_db.role == "super_admin"
    assert user_in_db.account_type == UserAccountTypeEnum.AGENCY
    assert user_in_db.is_verified is False

    # Verify default profile creation
    profile_in_db = db.query(Profile).filter(Profile.user_id == user_in_db.id).first()
    assert profile_in_db is not None
    assert profile_in_db.name == "Default Profile"
    # For agency users, the profile type should also be "personal" as per current implementation
    # If agency users should have an "agency" profile by default, the service logic needs adjustment.
    # Based on current service code, it's always "personal".
    assert profile_in_db.profile_type == "personal" 
    assert profile_in_db.user_id == user_in_db.id

def test_register_existing_email(client: TestClient, individual_user_payload: Dict[str, str], db: Session):
    # First registration
    client.post("/auth/register", json=individual_user_payload)
    
    # Attempt to register again with the same email
    response = client.post("/auth/register", json=individual_user_payload)
    assert response.status_code == 400, response.text
    assert "Email already registered" in response.json().get("detail", "")

def test_login_and_jwt_content_individual(client: TestClient, individual_user_payload: Dict[str, str], db: Session):
    # Register user first
    client.post("/auth/register", json=individual_user_payload)
    
    # Login
    login_payload = {"email": individual_user_payload["email"], "password": individual_user_payload["password"]}
    response = client.post("/auth/login", data=login_payload) # Form data for login
    assert response.status_code == 200, response.text
    
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Verify TokenResponse schema fields
    assert token_data["role"] == "user"
    assert token_data["account_type"] == UserAccountTypeEnum.INDIVIDUAL.value
    assert token_data["user"]["email"] == individual_user_payload["email"]
    assert token_data["user"]["role"] == "user"
    assert token_data["user"]["account_type"] == UserAccountTypeEnum.INDIVIDUAL.value

    # Decode JWT
    decoded_token = jwt.decode(token_data["access_token"], settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded_token["sub"] == individual_user_payload["email"]
    assert decoded_token["role"] == "user"
    assert decoded_token["account_type"] == UserAccountTypeEnum.INDIVIDUAL.value

def test_login_and_jwt_content_agency(client: TestClient, agency_user_payload: Dict[str, str], db: Session):
    # Register user first
    client.post("/auth/register", json=agency_user_payload)
    
    # Login
    login_payload = {"email": agency_user_payload["email"], "password": agency_user_payload["password"]}
    response = client.post("/auth/login", data=login_payload) # Form data for login
    assert response.status_code == 200, response.text
    
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Verify TokenResponse schema fields
    assert token_data["role"] == "super_admin"
    assert token_data["account_type"] == UserAccountTypeEnum.AGENCY.value
    assert token_data["user"]["email"] == agency_user_payload["email"]
    assert token_data["user"]["role"] == "super_admin"
    assert token_data["user"]["account_type"] == UserAccountTypeEnum.AGENCY.value
    
    # Decode JWT
    decoded_token = jwt.decode(token_data["access_token"], settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded_token["sub"] == agency_user_payload["email"]
    assert decoded_token["role"] == "super_admin"
    assert decoded_token["account_type"] == UserAccountTypeEnum.AGENCY.value

# Note: These tests assume a 'db: Session' fixture is provided by conftest.py
# that gives a SQLAlchemy session to interact with a test database.
# The actual interaction (e.g., db.query) might need adjustment based on
# whether the test DB is async or sync, and how conftest.py sets it up.
# If the test DB is async, then DB assertions would need `await` and async session.
# For now, written with sync session for simplicity of example.
# The `client` fixture is also defined locally but ideally comes from conftest.py
# and is configured to override dependencies for the test environment.
# Specifically, `get_db` needs to be overridden to point to a test DB.
# The login endpoint uses form data, so `client.post` uses `data=` not `json=`.
# Registration uses JSON, so `json=`.
# The current User model has `id = Column(Integer, ...)`, so ID comparisons are against int.
# If `conftest.py` is not set up for overriding `get_db` to use a test database
# and clearing it between tests, these tests will interact with the real dev DB
# and might fail due to existing data or leave test data behind.
# This is a simplified initial structure. More robust DB handling is key.

import pytest
from uuid import uuid4, UUID
from typing import List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.services import asset_service
from app.schemas.asset import AssetCategoryCreate, AssetCategoryRead
from app.models.asset import AssetCategory
from app.core.database import Base, engine # For creating tables if not managed by Alembic in test setup

# For now, we'll assume a testing database is set up and tables are created.
# If not, a fixture to create tables would be needed:
# @pytest.fixture(scope="session", autouse=True)
# def create_test_tables():
#     Base.metadata.create_all(bind=engine)
#     yield
#     Base.metadata.drop_all(bind=engine)


# --- Test Data ---
def create_random_category_data() -> AssetCategoryCreate:
    return AssetCategoryCreate(name=f"Category {uuid4()}", description="Test category description")

# --- Service Layer Tests (Unit Tests) ---

def test_create_asset_category_success(db_session: Session):
    category_in = create_random_category_data()
    created_category = asset_service.create_asset_category(db=db_session, category_in=category_in)
    
    assert created_category is not None
    assert created_category.id is not None
    assert created_category.name == category_in.name
    assert created_category.description == category_in.description
    
    db_category = db_session.query(AssetCategory).filter(AssetCategory.id == created_category.id).first()
    assert db_category is not None
    assert db_category.name == category_in.name

def test_create_asset_category_duplicate_name(db_session: Session):
    category_in = create_random_category_data()
    asset_service.create_asset_category(db=db_session, category_in=category_in) # Create first one
    
    with pytest.raises(ValueError) as excinfo: # Service converts IntegrityError to ValueError
        asset_service.create_asset_category(db=db_session, category_in=category_in)
    assert f"Asset category with name '{category_in.name}' already exists" in str(excinfo.value)

def test_get_asset_category_success(db_session: Session):
    category_in = create_random_category_data()
    created_category_model = asset_service.create_asset_category(db=db_session, category_in=category_in)
    
    retrieved_category = asset_service.get_asset_category(db=db_session, category_id=created_category_model.id)
    
    assert retrieved_category is not None
    assert retrieved_category.id == created_category_model.id
    assert retrieved_category.name == category_in.name

def test_get_asset_category_not_found(db_session: Session):
    non_existent_id = uuid4()
    retrieved_category = asset_service.get_asset_category(db=db_session, category_id=non_existent_id)
    assert retrieved_category is None

def test_get_asset_category_by_name_success(db_session: Session):
    category_in = create_random_category_data()
    created_category_model = asset_service.create_asset_category(db=db_session, category_in=category_in)
    
    retrieved_category = asset_service.get_asset_category_by_name(db=db_session, category_name=category_in.name)
    
    assert retrieved_category is not None
    assert retrieved_category.id == created_category_model.id
    assert retrieved_category.name == category_in.name

def test_get_asset_category_by_name_not_found(db_session: Session):
    non_existent_name = f"NonExistentCategory {uuid4()}"
    retrieved_category = asset_service.get_asset_category_by_name(db=db_session, category_name=non_existent_name)
    assert retrieved_category is None

def test_get_all_asset_categories_empty(db_session: Session):
    # Ensure no categories exist initially for this test or clean up
    db_session.query(AssetCategory).delete()
    db_session.commit()
    
    categories = asset_service.get_all_asset_categories(db=db_session)
    assert isinstance(categories, list)
    assert len(categories) == 0

def test_get_all_asset_categories_with_data(db_session: Session):
    db_session.query(AssetCategory).delete() # Clear existing
    db_session.commit()

    cat1_data = create_random_category_data()
    cat2_data = create_random_category_data()
    asset_service.create_asset_category(db=db_session, category_in=cat1_data)
    asset_service.create_asset_category(db=db_session, category_in=cat2_data)
    
    categories = asset_service.get_all_asset_categories(db=db_session)
    assert len(categories) == 2
    # Add more specific assertions if needed, e.g., check names

def test_get_all_asset_categories_pagination(db_session: Session):
    db_session.query(AssetCategory).delete() # Clear existing
    db_session.commit()

    created_categories = []
    for _ in range(5): # Create 5 categories
        cat_data = create_random_category_data()
        created_categories.append(asset_service.create_asset_category(db=db_session, category_in=cat_data))
    
    # Test skip
    categories_skip_2 = asset_service.get_all_asset_categories(db=db_session, skip=2, limit=5)
    assert len(categories_skip_2) == 3
    
    # Test limit
    categories_limit_2 = asset_service.get_all_asset_categories(db=db_session, skip=0, limit=2)
    assert len(categories_limit_2) == 2
    
    # Test skip and limit
    categories_skip_1_limit_2 = asset_service.get_all_asset_categories(db=db_session, skip=1, limit=2)
    assert len(categories_skip_1_limit_2) == 2
    # Ensure the correct items are returned, e.g. by comparing IDs or names if order is guaranteed
    assert categories_skip_1_limit_2[0].id == created_categories[1].id
    assert categories_skip_1_limit_2[1].id == created_categories[2].id


# --- Router Layer Tests (Integration Tests) ---

def test_api_create_asset_category_success(client: TestClient, db_session: Session): # db_session for cleanup/verification if needed
    category_in_data = create_random_category_data()
    response = client.post("/assets/categories/", json=category_in_data.model_dump())
    
    assert response.status_code == 201
    created_category_data = response.json()
    assert created_category_data["name"] == category_in_data.name
    assert created_category_data["description"] == category_in_data.description
    assert "id" in created_category_data
    
    # Verify in DB
    db_category = db_session.query(AssetCategory).filter(AssetCategory.id == created_category_data["id"]).first()
    assert db_category is not None
    assert db_category.name == category_in_data.name

def test_api_create_asset_category_invalid_input_missing_name(client: TestClient):
    invalid_data = {"description": "Test category"} # Missing 'name'
    response = client.post("/assets/categories/", json=invalid_data)
    assert response.status_code == 422 # FastAPI validation error

def test_api_create_asset_category_duplicate_name(client: TestClient, db_session: Session):
    category_in_data = create_random_category_data()
    # Create the first category directly via service or API
    asset_service.create_asset_category(db=db_session, category_in=category_in_data)
    
    # Attempt to create again via API
    response = client.post("/assets/categories/", json=category_in_data.model_dump())
    assert response.status_code == 400
    assert f"Asset category with name '{category_in_data.name}' already exists" in response.json()["detail"]

def test_api_get_single_asset_category_success(client: TestClient, db_session: Session):
    category_in = create_random_category_data()
    created_category_model = asset_service.create_asset_category(db=db_session, category_in=category_in)
    
    response = client.get(f"/assets/categories/{created_category_model.id}")
    assert response.status_code == 200
    retrieved_data = response.json()
    assert retrieved_data["id"] == str(created_category_model.id)
    assert retrieved_data["name"] == category_in.name

def test_api_get_single_asset_category_not_found(client: TestClient):
    non_existent_id = uuid4()
    response = client.get(f"/assets/categories/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Asset category not found"

def test_api_get_all_asset_categories_empty(client: TestClient, db_session: Session):
    db_session.query(AssetCategory).delete()
    db_session.commit()
    
    response = client.get("/assets/categories/")
    assert response.status_code == 200
    assert response.json() == []

def test_api_get_all_asset_categories_with_data(client: TestClient, db_session: Session):
    db_session.query(AssetCategory).delete()
    db_session.commit()
    cat1_data = create_random_category_data()
    cat2_data = create_random_category_data()
    asset_service.create_asset_category(db=db_session, category_in=cat1_data)
    asset_service.create_asset_category(db=db_session, category_in=cat2_data)

    response = client.get("/assets/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Add more specific checks if needed, e.g. ensure names are present

def test_api_get_all_asset_categories_pagination(client: TestClient, db_session: Session):
    db_session.query(AssetCategory).delete()
    db_session.commit()
    created_ids = []
    for _ in range(5):
        cat_data = create_random_category_data()
        created_category = asset_service.create_asset_category(db=db_session, category_in=cat_data)
        created_ids.append(str(created_category.id))

    # Test skip
    response_skip = client.get("/assets/categories/?skip=2&limit=5")
    assert response_skip.status_code == 200
    data_skip = response_skip.json()
    assert len(data_skip) == 3
    assert data_skip[0]["id"] == created_ids[2] # Assuming default ordering by creation time / ID

    # Test limit
    response_limit = client.get("/assets/categories/?skip=0&limit=2")
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert len(data_limit) == 2
    assert data_limit[0]["id"] == created_ids[0]

    # Test skip and limit
    response_skip_limit = client.get("/assets/categories/?skip=1&limit=2")
    assert response_skip_limit.status_code == 200
    data_skip_limit = response_skip_limit.json()
    assert len(data_skip_limit) == 2
    assert data_skip_limit[0]["id"] == created_ids[1]
    assert data_skip_limit[1]["id"] == created_ids[2]

# TODO: Consider adding a fixture to clean up categories after each test or group of tests
# to ensure test isolation, if not already handled by transaction rollback in db_session fixture.
# Example:
# @pytest.fixture(autouse=True)
# def cleanup_categories(db_session: Session):
#     yield
#     db_session.query(AssetCategory).delete()
#     db_session.commit()

# Note: The TestClient (client fixture) typically handles its own DB session management
# often by using a transactional session that's rolled back after each test, or by
# creating a fresh test database. If using `db_session` alongside `client` in API tests,
# ensure they are part of the same transaction or that `db_session` is used for setup/verification
# in a way that's compatible with `client`'s DB operations.
# For service tests, `db_session` should ideally be a transactional session.
# If `Base.metadata.create_all` is used, it should target a test-specific database.
# The current asset_service.py uses `db.commit()` in create_asset_category.
# This means db_session fixture must handle transactions properly (e.g., rollback after test).
# If it doesn't, tests creating data can interfere.
# A common pattern for db_session fixture:
# @pytest.fixture
# def db_session():
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = Session(bind=connection)
#     yield session
#     session.close()
#     transaction.rollback()
#     connection.close()
# This ensures each test runs in an isolated transaction.
# The `create_test_tables` fixture should also use a test database.
# The `client` fixture from FastAPI's TestClient often uses a similar mechanism or `Starlette-TestClient`.
# It's crucial that these are configured correctly in a `conftest.py`.
# For these tests, I'm assuming such a setup is in place.

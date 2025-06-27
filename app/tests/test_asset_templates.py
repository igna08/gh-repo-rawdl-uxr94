import pytest
from uuid import uuid4, UUID
from typing import List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import asset_service
from app.schemas.asset import AssetTemplateCreate, AssetTemplateRead, AssetCategoryCreate
from app.models.asset import AssetTemplate, AssetCategory
# Assuming User model might be needed for current_user_id in service calls, if not, can be removed.
# from app.models.user import User 

# Dummy User ID for service calls that require created_by_id or user context
# In a real app, this user should exist or be mocked appropriately.
DUMMY_USER_ID = uuid4()

# --- Helper Functions ---

def create_db_category(db: Session, name: str = None, description: str = None) -> AssetCategory:
    """Helper to create and save an AssetCategory directly to the DB."""
    cat_name = name or f"Test Category {uuid4()}"
    category = AssetCategory(name=cat_name, description=description or "Test category description")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

def create_random_template_data(category_id: UUID) -> AssetTemplateCreate:
    """Helper to generate AssetTemplateCreate schema with random data."""
    return AssetTemplateCreate(
        name=f"Template {uuid4()}",
        description="Test template description",
        manufacturer=f"Manufacturer {uuid4()}",
        model_number=f"Model-{uuid4()}",
        category_id=category_id
    )

# --- Service Layer Tests (Unit Tests) ---

def test_create_asset_template_success(db_session: Session):
    category = create_db_category(db_session)
    template_in = create_random_template_data(category_id=category.id)
    
    # The service function create_asset_template expects current_user_id
    created_template = asset_service.create_asset_template(db=db_session, template_in=template_in, current_user_id=DUMMY_USER_ID)
    
    assert created_template is not None
    assert created_template.id is not None
    assert created_template.name == template_in.name
    assert created_template.category_id == category.id
    
    db_template = db_session.query(AssetTemplate).filter(AssetTemplate.id == created_template.id).first()
    assert db_template is not None
    assert db_template.name == template_in.name

def test_create_asset_template_non_existent_category(db_session: Session):
    non_existent_category_id = uuid4()
    template_in = create_random_template_data(category_id=non_existent_category_id)
    
    with pytest.raises(ValueError) as excinfo:
        asset_service.create_asset_template(db=db_session, template_in=template_in, current_user_id=DUMMY_USER_ID)
    assert f"Asset category with id {non_existent_category_id} not found" in str(excinfo.value)

def test_get_asset_template_success(db_session: Session):
    category = create_db_category(db_session)
    template_in = create_random_template_data(category_id=category.id)
    created_template_model = asset_service.create_asset_template(db=db_session, template_in=template_in, current_user_id=DUMMY_USER_ID)
    
    retrieved_template = asset_service.get_asset_template(db=db_session, template_id=created_template_model.id)
    
    assert retrieved_template is not None
    assert retrieved_template.id == created_template_model.id
    assert retrieved_template.name == template_in.name

def test_get_asset_template_not_found(db_session: Session):
    non_existent_id = uuid4()
    retrieved_template = asset_service.get_asset_template(db=db_session, template_id=non_existent_id)
    assert retrieved_template is None

def test_get_all_asset_templates_empty(db_session: Session):
    db_session.query(AssetTemplate).delete() # Clear existing
    db_session.commit()
    templates = asset_service.get_all_asset_templates(db=db_session)
    assert isinstance(templates, list)
    assert len(templates) == 0

def test_get_all_asset_templates_with_data(db_session: Session):
    db_session.query(AssetTemplate).delete() # Clear existing
    db_session.query(AssetCategory).delete()
    db_session.commit()
    
    category = create_db_category(db_session)
    template1_in = create_random_template_data(category_id=category.id)
    template2_in = create_random_template_data(category_id=category.id)
    asset_service.create_asset_template(db=db_session, template_in=template1_in, current_user_id=DUMMY_USER_ID)
    asset_service.create_asset_template(db=db_session, template_in=template2_in, current_user_id=DUMMY_USER_ID)
    
    templates = asset_service.get_all_asset_templates(db=db_session)
    assert len(templates) == 2

def test_get_all_asset_templates_pagination(db_session: Session):
    db_session.query(AssetTemplate).delete() # Clear existing
    db_session.query(AssetCategory).delete()
    db_session.commit()

    category = create_db_category(db_session)
    created_templates = []
    for _ in range(5):
        template_data = create_random_template_data(category_id=category.id)
        created_templates.append(asset_service.create_asset_template(db=db_session, template_in=template_data, current_user_id=DUMMY_USER_ID))
    
    templates_skip_2 = asset_service.get_all_asset_templates(db=db_session, skip=2, limit=5)
    assert len(templates_skip_2) == 3
    templates_limit_2 = asset_service.get_all_asset_templates(db=db_session, skip=0, limit=2)
    assert len(templates_limit_2) == 2
    templates_skip_1_limit_2 = asset_service.get_all_asset_templates(db=db_session, skip=1, limit=2)
    assert len(templates_skip_1_limit_2) == 2
    assert templates_skip_1_limit_2[0].id == created_templates[1].id
    assert templates_skip_1_limit_2[1].id == created_templates[2].id

def test_get_asset_templates_by_category_success(db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.query(AssetCategory).delete()
    db_session.commit()

    category1 = create_db_category(db_session, name="Category One")
    category2 = create_db_category(db_session, name="Category Two")

    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category1.id), current_user_id=DUMMY_USER_ID)
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category1.id), current_user_id=DUMMY_USER_ID)
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category2.id), current_user_id=DUMMY_USER_ID)

    templates_cat1 = asset_service.get_asset_templates_by_category(db=db_session, category_id=category1.id)
    assert len(templates_cat1) == 2
    for tpl in templates_cat1:
        assert tpl.category_id == category1.id

    templates_cat2 = asset_service.get_asset_templates_by_category(db=db_session, category_id=category2.id)
    assert len(templates_cat2) == 1

def test_get_asset_templates_by_category_non_existent_category(db_session: Session):
    non_existent_cat_id = uuid4()
    templates = asset_service.get_asset_templates_by_category(db=db_session, category_id=non_existent_cat_id)
    assert len(templates) == 0

def test_get_asset_templates_by_category_pagination(db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.query(AssetCategory).delete()
    db_session.commit()

    category = create_db_category(db_session)
    created_templates_in_category = []
    for _ in range(5):
        tpl_data = create_random_template_data(category_id=category.id)
        created_templates_in_category.append(asset_service.create_asset_template(db=db_session, template_in=tpl_data, current_user_id=DUMMY_USER_ID))

    # Create some templates in another category to ensure filtering works
    other_category = create_db_category(db_session, name="Other Test Category")
    for _ in range(3):
        asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=other_category.id), current_user_id=DUMMY_USER_ID)

    templates_skip_2 = asset_service.get_asset_templates_by_category(db=db_session, category_id=category.id, skip=2, limit=5)
    assert len(templates_skip_2) == 3
    templates_limit_2 = asset_service.get_asset_templates_by_category(db=db_session, category_id=category.id, skip=0, limit=2)
    assert len(templates_limit_2) == 2
    templates_skip_1_limit_2 = asset_service.get_asset_templates_by_category(db=db_session, category_id=category.id, skip=1, limit=2)
    assert len(templates_skip_1_limit_2) == 2
    assert templates_skip_1_limit_2[0].id == created_templates_in_category[1].id
    assert templates_skip_1_limit_2[1].id == created_templates_in_category[2].id


# --- Router Layer Tests (Integration Tests) ---

def test_api_create_asset_template_success(client: TestClient, db_session: Session):
    category = create_db_category(db_session)
    template_in_data = create_random_template_data(category_id=category.id)
    
    response = client.post("/assets/templates/", json=template_in_data.model_dump(mode='json')) # Use mode='json' for UUIDs
    
    assert response.status_code == 201, response.text
    created_template_data = response.json()
    assert created_template_data["name"] == template_in_data.name
    assert created_template_data["category_id"] == str(category.id)
    assert "id" in created_template_data
    
    db_template = db_session.query(AssetTemplate).filter(AssetTemplate.id == created_template_data["id"]).first()
    assert db_template is not None
    assert db_template.name == template_in_data.name

def test_api_create_asset_template_invalid_input_missing_name(client: TestClient):
    category_id = uuid4() # Dummy ID, won't be reached if validation fails first
    invalid_data = {"description": "Test template", "category_id": str(category_id)}
    response = client.post("/assets/templates/", json=invalid_data)
    assert response.status_code == 422 # FastAPI validation error

def test_api_create_asset_template_invalid_category_id_format(client: TestClient):
    template_data = {
        "name": "Invalid Cat ID Template",
        "description": "Test",
        "category_id": "this-is-not-a-uuid"
    }
    response = client.post("/assets/templates/", json=template_data)
    assert response.status_code == 422 # Pydantic validation for UUID format

def test_api_create_asset_template_non_existent_category(client: TestClient):
    non_existent_category_id = uuid4()
    template_in_data = create_random_template_data(category_id=non_existent_category_id)
    
    response = client.post("/assets/templates/", json=template_in_data.model_dump(mode='json'))
    assert response.status_code == 400
    assert f"Asset category with id {non_existent_category_id} not found" in response.json()["detail"]

def test_api_get_single_asset_template_success(client: TestClient, db_session: Session):
    category = create_db_category(db_session)
    template_model = asset_service.create_asset_template(
        db=db_session, 
        template_in=create_random_template_data(category_id=category.id),
        current_user_id=DUMMY_USER_ID
    )
    
    response = client.get(f"/assets/templates/{template_model.id}")
    assert response.status_code == 200
    retrieved_data = response.json()
    assert retrieved_data["id"] == str(template_model.id)
    assert retrieved_data["name"] == template_model.name
    assert retrieved_data["category_id"] == str(category.id)

def test_api_get_single_asset_template_not_found(client: TestClient):
    non_existent_id = uuid4()
    response = client.get(f"/assets/templates/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Asset template not found"

def test_api_get_all_asset_templates_empty(client: TestClient, db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.commit()
    response = client.get("/assets/templates/")
    assert response.status_code == 200
    assert response.json() == []

def test_api_get_all_asset_templates_with_data(client: TestClient, db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.query(AssetCategory).delete()
    db_session.commit()
    category = create_db_category(db_session)
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category.id), current_user_id=DUMMY_USER_ID)
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category.id), current_user_id=DUMMY_USER_ID)

    response = client.get("/assets/templates/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_api_get_all_asset_templates_pagination(client: TestClient, db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.query(AssetCategory).delete()
    db_session.commit()
    category = create_db_category(db_session)
    created_ids = []
    for _ in range(5):
        tpl = asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category.id), current_user_id=DUMMY_USER_ID)
        created_ids.append(str(tpl.id))

    response_skip = client.get("/assets/templates/?skip=2&limit=5")
    assert response_skip.status_code == 200
    data_skip = response_skip.json()
    assert len(data_skip) == 3
    assert data_skip[0]["id"] == created_ids[2]

    response_limit = client.get("/assets/templates/?skip=0&limit=2")
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert len(data_limit) == 2
    assert data_limit[0]["id"] == created_ids[0]

def test_api_get_asset_templates_by_category_success(client: TestClient, db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.query(AssetCategory).delete()
    db_session.commit()
    category1 = create_db_category(db_session, name="Cat One For Templates")
    category2 = create_db_category(db_session, name="Cat Two For Templates")
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category1.id), current_user_id=DUMMY_USER_ID)
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category1.id), current_user_id=DUMMY_USER_ID)
    asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category2.id), current_user_id=DUMMY_USER_ID)

    response = client.get(f"/assets/templates/by_category/{category1.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for item in data:
        assert item["category_id"] == str(category1.id)

def test_api_get_asset_templates_by_category_empty(client: TestClient, db_session: Session):
    category = create_db_category(db_session, name="Empty Category For Templates") # No templates in this category
    response = client.get(f"/assets/templates/by_category/{category.id}")
    assert response.status_code == 200
    assert response.json() == []

def test_api_get_asset_templates_by_category_non_existent_category(client: TestClient):
    non_existent_cat_id = uuid4()
    response = client.get(f"/assets/templates/by_category/{non_existent_cat_id}")
    assert response.status_code == 200 # Service returns empty list, router returns 200
    assert response.json() == []
    # Note: The router endpoint for templates by category doesn't explicitly check if category exists and return 404.
    # It relies on the service which returns an empty list if category_id doesn't match any templates.
    # This behavior is acceptable, but could be changed to a 404 if strict category existence check is desired at router level.

def test_api_get_asset_templates_by_category_pagination(client: TestClient, db_session: Session):
    db_session.query(AssetTemplate).delete()
    db_session.query(AssetCategory).delete()
    db_session.commit()
    category = create_db_category(db_session)
    created_ids_in_cat = []
    for _ in range(5):
        tpl = asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=category.id), current_user_id=DUMMY_USER_ID)
        created_ids_in_cat.append(str(tpl.id))
    
    # Other category templates
    other_cat = create_db_category(db_session, name="Other Cat For Pagination Test")
    for _ in range(3):
        asset_service.create_asset_template(db=db_session, template_in=create_random_template_data(category_id=other_cat.id), current_user_id=DUMMY_USER_ID)

    response_skip = client.get(f"/assets/templates/by_category/{category.id}?skip=2&limit=5")
    assert response_skip.status_code == 200
    data_skip = response_skip.json()
    assert len(data_skip) == 3
    assert data_skip[0]["id"] == created_ids_in_cat[2]

    response_limit = client.get(f"/assets/templates/by_category/{category.id}?skip=0&limit=2")
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert len(data_limit) == 2
    assert data_limit[0]["id"] == created_ids_in_cat[0]

# Remember to have a conftest.py that provides 'client' and 'db_session' fixtures.
# db_session should manage transactions for test isolation.
# Example conftest.py content for db_session:
# @pytest.fixture(scope="function")
# def db_session(engine): # Assuming 'engine' fixture provides the test DB engine
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = Session(bind=connection)
#     yield session
#     session.close()
#     transaction.rollback()
#     connection.close()
#
# And client fixture:
# from fastapi.testclient import TestClient
# from app.main import app # Your FastAPI app instance
# @pytest.fixture(scope="module")
# def client():
#     with TestClient(app) as c:
#         yield c
#
# Ensure your FastAPI app (`app.main.app`) uses the test database when tests are run.
# This might involve environment variables or a specific test configuration.
# The current_user_id (DUMMY_USER_ID) is passed to service functions as required.
# The API tests for create template do not pass user_id as the get_current_user_id dependency handles it.
# For API tests, model_dump(mode='json') is used for UUID serialization in request body.
# Cleanup of AssetCategory and AssetTemplate tables is done at the beginning of tests that populate data,
# assuming the db_session fixture handles rollback for individual tests.
# If not, more explicit cleanup fixtures might be needed.
# The service `create_asset_template` takes current_user_id. This is provided in service tests.
# API endpoint for create template gets current_user_id from dependency.
# The tests for `get_asset_templates_by_category` for a non-existent category ID currently expect an empty list and 200 OK,
# as the service layer doesn't raise an error for this, and the router layer doesn't add an explicit check.
# This is a valid design choice, but could be changed to a 404 if desired.
# Tests for pagination assume default ordering (usually by primary key or insertion order if not specified).
# Added .model_dump(mode='json') for API tests sending data with UUIDs to ensure proper serialization.
# Corrected some cleanup logic to also clear AssetCategory when AssetTemplate is cleared.
# Added DUMMY_USER_ID for create_asset_template service calls.
# API create template test uses `template_in_data.model_dump(mode='json')` for proper UUID serialization.
# Added `response.text` to failed assertion in `test_api_create_asset_template_success` for better debugging.
# Ensured all tests that create data also clean up AssetCategory table if relevant.
# Added `current_user_id=DUMMY_USER_ID` to all service layer calls of `create_asset_template`.
# Added `model_dump(mode='json')` to `test_api_create_asset_template_non_existent_category` for consistency.
# Clarified comments about test database setup and fixture responsibilities.

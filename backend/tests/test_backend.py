import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.nlp_service import NLPService
from backend.app.services.ml_service import MLService
from backend.app.database import ProductivityDB

client = TestClient(app)

def test_nlp_date_parsing():
    nlp = NLPService()
    # Test natural date parsing "tomorrow"
    date_str = nlp.extract_due_date("Finish the homework tomorrow at 3pm")
    assert date_str is not None
    
    # Test non-date sentence
    no_date = nlp.extract_due_date("Clean my room")
    assert no_date is None

def test_nlp_tagging():
    nlp = NLPService()
    tags = nlp.extract_keywords_and_tags("Read organic chemistry pages on photosynthesis", "Study")
    # Tags should contain the category and keywords
    assert "study" in tags
    assert "organic" in tags or "chemistry" in tags or "photosynthesis" in tags

def test_ml_predictions_fallback():
    ml = MLService()
    # Test fallback categorization rules
    pred = ml.predict_fallback("Prepare study notes for the physics exam tomorrow")
    assert pred["intent"] in ["Task", "Note", "Reminder", "Todo"]
    assert pred["category"] == "Study"
    assert pred["priority"] == "High"  # due to "exam" keyword

def test_db_fallback():
    db = ProductivityDB()
    # Ensure database is initialised (either MongoDB or SQLite)
    assert db.get_db_type() in ["MongoDB", "SQLite"]
    
    # Test creation and deletion of mock task
    item = db.create_item(
        text="Test mock database item",
        intent="Task",
        category="Work",
        priority="Medium"
    )
    assert item["text"] == "Test mock database item"
    assert item["id"] is not None
    
    retrieved = db.get_item_by_id(item["id"])
    assert retrieved is not None
    assert retrieved["text"] == "Test mock database item"
    
    deleted = db.delete_item(item["id"])
    assert deleted is True

def test_api_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "ml_models_loaded" in data

def test_api_capture_endpoint():
    response = client.post("/api/tasks/capture", json={"text": "Buy green apples tomorrow"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["item"]["text"] == "Buy green apples tomorrow"
    assert data["item"]["category"] == "Shopping"
    assert data["item"]["due_date"] is not None
    
    # Clean up created task
    client.delete(f"/api/tasks/{data['item']['id']}")

def test_api_analytics_summary():
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "metrics" in data
    assert "productivity_score" in data["metrics"]

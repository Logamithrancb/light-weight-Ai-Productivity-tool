from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.app.database import ProductivityDB
from backend.app.services.ml_service import MLService
from backend.app.services.nlp_service import NLPService

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Database & Services singletons (initialized on application startup or dynamically)
db = ProductivityDB()
ml_service = MLService()
nlp_service = NLPService()

# Pydantic schemas for request validation
class TaskCaptureRequest(BaseModel):
    text: str

class TaskUpdateRequest(BaseModel):
    text: Optional[str] = None
    intent: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None

@router.post("/capture")
def capture_task(req: TaskCaptureRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text query cannot be empty.")
        
    text = req.text.strip()
    
    # 1. Run ML classification (Intent, Category, Priority)
    predictions = ml_service.predict(text)
    
    # 2. Run NLP services
    due_date = nlp_service.extract_due_date(text)
    tags = nlp_service.extract_keywords_and_tags(text, predictions["category"])
    embedding = nlp_service.get_embedding(text)
    
    # 3. Save to database
    item = db.create_item(
        text=text,
        intent=predictions["intent"],
        category=predictions["category"],
        priority=predictions["priority"],
        status="pending",
        due_date=due_date,
        tags=tags,
        embedding=embedding
    )
    
    return {
        "success": True,
        "item": item,
        "meta": {
            "model_type": predictions["method"],
            "has_embedding": len(embedding) > 0
        }
    }

@router.get("")
def list_tasks(
    status: Optional[str] = None,
    intent: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    q: Optional[str] = None
):
    if q and q.strip():
        query_str = q.strip()
        # Retrieve all items with embeddings for hybrid search
        items = db.get_all_embeddings()
        if not items:
            # If no items have embeddings yet, try to search over all items
            items = db.get_items()
            
        search_results = nlp_service.search(query_str, items)
        
        # Apply other filters post-search
        filtered_results = []
        for item in search_results:
            if status and item.get("status") != status:
                continue
            if intent and item.get("intent") != intent:
                continue
            if category and item.get("category") != category:
                continue
            if priority and item.get("priority") != priority:
                continue
            filtered_results.append(item)
            
        return filtered_results
    else:
        return db.get_items(status=status, intent=intent, category=category, priority=priority)

@router.get("/{task_id}")
def get_task(task_id: str):
    item = db.get_item_by_id(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    return item

@router.put("/{task_id}")
def update_task(task_id: str, req: TaskUpdateRequest):
    item = db.get_item_by_id(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
        
    update_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    
    # If text is updated, regenerate tags and embedding
    if "text" in update_dict and update_dict["text"] != item["text"]:
        new_text = update_dict["text"]
        cat = update_dict.get("category", item["category"])
        update_dict["tags"] = nlp_service.extract_keywords_and_tags(new_text, cat)
        update_dict["embedding"] = nlp_service.get_embedding(new_text)
        # Re-extract date if not manually provided
        if "due_date" not in update_dict:
            update_dict["due_date"] = nlp_service.extract_due_date(new_text)

    # Handle completion timestamp
    if "status" in update_dict:
        if update_dict["status"] == "completed" and item["status"] != "completed":
            update_dict["completed_at"] = datetime.utcnow().isoformat()
        elif update_dict["status"] == "pending":
            update_dict["completed_at"] = None

    updated_item = db.update_item(task_id, update_dict)
    # Remove embedding from output representation
    if updated_item and "embedding" in updated_item:
        del updated_item["embedding"]
        
    return updated_item

@router.post("/{task_id}/toggle")
def toggle_task(task_id: str):
    item = db.get_item_by_id(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
        
    new_status = "completed" if item["status"] == "pending" else "pending"
    completed_at = datetime.utcnow().isoformat() if new_status == "completed" else None
    
    updated_item = db.update_item(task_id, {
        "status": new_status,
        "completed_at": completed_at
    })
    
    if updated_item and "embedding" in updated_item:
        del updated_item["embedding"]
        
    return updated_item

@router.delete("/{task_id}")
def delete_task(task_id: str):
    success = db.delete_item(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": "Task deleted successfully"}

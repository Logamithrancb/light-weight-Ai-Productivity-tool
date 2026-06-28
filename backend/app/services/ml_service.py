import os
import joblib
from backend.app import config

class MLService:
    def __init__(self):
        self.models_loaded = False
        self.intent_pipeline = None
        self.category_pipeline = None
        self.priority_pipeline = None
        
        self.load_models()

    def load_models(self):
        intent_path = os.path.join(config.SAVED_MODELS_DIR, "intent_pipeline.joblib")
        category_path = os.path.join(config.SAVED_MODELS_DIR, "category_pipeline.joblib")
        priority_path = os.path.join(config.SAVED_MODELS_DIR, "priority_pipeline.joblib")
        
        if (os.path.exists(intent_path) and 
            os.path.exists(category_path) and 
            os.path.exists(priority_path)):
            try:
                self.intent_pipeline = joblib.load(intent_path)
                self.category_pipeline = joblib.load(category_path)
                self.priority_pipeline = joblib.load(priority_path)
                self.models_loaded = True
                print("Successfully loaded all ML models.")
            except Exception as e:
                print(f"Error loading saved ML models: {e}. Using fallback rule-based models.")
                self.models_loaded = False
        else:
            print("ML model files not found. Using fallback rule-based models. Run the training script first to deploy optimized models.")
            self.models_loaded = False

    def predict_fallback(self, text: str) -> dict:
        """Rule-based classifier fallback when model files are not found."""
        text_lower = text.lower()
        
        # 1. Intent classifier
        intent = "Task"
        if any(w in text_lower for w in ["remind", "reminder", "alarm", "clock", "date"]):
            intent = "Reminder"
        elif any(w in text_lower for w in ["note", "journal", "write down", "record", "concept", "idea", "thoughts"]):
            intent = "Note"
        elif any(w in text_lower for w in ["todo", "to-do", "buy", "get", "clean", "do", "finish", "complete", "schedule"]):
            intent = "Todo"
            
        # 2. Category classifier
        category = "Personal"
        if any(w in text_lower for w in ["study", "exam", "class", "course", "lecture", "book", "read", "chapter", "professor", "syllabus"]):
            category = "Study"
        elif any(w in text_lower for w in ["meeting", "work", "project", "report", "client", "code", "bug", "deploy", "email", "manager", "timesheet"]):
            category = "Work"
        elif any(w in text_lower for w in ["buy", "shop", "grocery", "groceries", "purchase", "order", "store", "supermarket"]):
            category = "Shopping"
        elif any(w in text_lower for w in ["health", "gym", "doctor", "medicine", "prescription", "run", "workout", "stretch", "therapy", "checkup"]):
            category = "Health"
        elif any(w in text_lower for w in ["bill", "pay", "rent", "finance", "money", "budget", "tax", "stock", "stocks", "utility"]):
            category = "Finance"
            
        # 3. Priority classifier
        priority = "Medium"
        if any(w in text_lower for w in ["urgent", "asap", "deadline", "emergency", "doctor", "bill", "pay", "rent", "exam", "critical"]):
            priority = "High"
        elif any(w in text_lower for w in ["if time permits", "low priority", "wishlist", "buy", "grocery", "some day"]):
            priority = "Low"
            
        return {
            "intent": intent,
            "category": category,
            "priority": priority,
            "method": "rule-based fallback"
        }

    def predict(self, text: str) -> dict:
        if not self.models_loaded:
            # Try to reload models dynamically if they were trained in the background
            self.load_models()
            if not self.models_loaded:
                return self.predict_fallback(text)
                
        try:
            intent = str(self.intent_pipeline.predict([text])[0])
            category = str(self.category_pipeline.predict([text])[0])
            priority = str(self.priority_pipeline.predict([text])[0])
            
            return {
                "intent": intent,
                "category": category,
                "priority": priority,
                "method": "trained ML models"
            }
        except Exception as e:
            print(f"Prediction failed: {e}. Falling back to rule-based classification.")
            return self.predict_fallback(text)

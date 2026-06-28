import os
import json
import sqlite3
from datetime import datetime
import uuid
from backend.app import config

class ProductivityDB:
    def __init__(self):
        self.use_mongo = False
        self.mongo_client = None
        self.db = None
        
        # Try to connect to MongoDB
        try:
            import pymongo
            self.mongo_client = pymongo.MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=1500)
            # Check connection
            self.mongo_client.server_info()
            self.db = self.mongo_client[config.DB_NAME]
            self.use_mongo = True
            print("Successfully connected to MongoDB.")
        except Exception as e:
            print(f"MongoDB connection failed: {e}. Falling back to SQLite at: {config.SQLITE_PATH}")
            self.use_mongo = False
            self._init_sqlite()

    def _init_sqlite(self):
        os.makedirs(os.path.dirname(config.SQLITE_PATH), exist_ok=True)
        conn = sqlite3.connect(config.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                intent TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                due_date TEXT,
                tags TEXT,
                embedding TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _row_to_dict(self, row):
        if row is None:
            return None
        res = dict(row)
        # Deserialize JSON arrays
        res["tags"] = json.loads(res["tags"]) if res.get("tags") else []
        res["embedding"] = json.loads(res["embedding"]) if res.get("embedding") else []
        return res

    def get_db_type(self):
        return "MongoDB" if self.use_mongo else "SQLite"

    def create_item(self, text: str, intent: str, category: str, priority: str, status: str = "pending", due_date: str = None, tags: list = None, embedding: list = None) -> dict:
        item_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        item = {
            "id": item_id,
            "text": text,
            "intent": intent,
            "category": category,
            "priority": priority,
            "status": status,
            "due_date": due_date,
            "tags": tags or [],
            "embedding": embedding or [],
            "created_at": created_at,
            "completed_at": None
        }
        
        if self.use_mongo:
            # Map 'id' to '_id' for mongo consistency, keep 'id' as a string field too
            mongo_item = dict(item)
            mongo_item["_id"] = item_id
            self.db.items.insert_one(mongo_item)
        else:
            conn = sqlite3.connect(config.SQLITE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO items (id, text, intent, category, priority, status, due_date, tags, embedding, created_at, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, text, intent, category, priority, status, due_date, 
                 json.dumps(item["tags"]), json.dumps(item["embedding"]), created_at, None)
            )
            conn.commit()
            conn.close()
            
        return item

    def get_items(self, status: str = None, intent: str = None, category: str = None, priority: str = None) -> list:
        if self.use_mongo:
            query = {}
            if status:
                query["status"] = status
            if intent:
                query["intent"] = intent
            if category:
                query["category"] = category
            if priority:
                query["priority"] = priority
            
            cursor = self.db.items.find(query).sort("created_at", -1)
            results = []
            for doc in cursor:
                doc["id"] = doc.get("_id", doc.get("id"))
                if "_id" in doc:
                    del doc["_id"]
                results.append(doc)
            return results
        else:
            conn = sqlite3.connect(config.SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM items WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if intent:
                query += " AND intent = ?"
                params.append(intent)
            if category:
                query += " AND category = ?"
                params.append(category)
            if priority:
                query += " AND priority = ?"
                params.append(priority)
                
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = [self._row_to_dict(row) for row in rows]
            conn.close()
            return results

    def get_item_by_id(self, item_id: str) -> dict:
        if self.use_mongo:
            doc = self.db.items.find_one({"_id": item_id})
            if doc:
                doc["id"] = doc.get("_id")
                del doc["_id"]
            return doc
        else:
            conn = sqlite3.connect(config.SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            conn.close()
            return self._row_to_dict(row)

    def update_item(self, item_id: str, update_data: dict) -> dict:
        if self.use_mongo:
            self.db.items.update_one({"_id": item_id}, {"$set": update_data})
            return self.get_item_by_id(item_id)
        else:
            conn = sqlite3.connect(config.SQLITE_PATH)
            cursor = conn.cursor()
            
            fields = []
            params = []
            for k, v in update_data.items():
                if k in ["tags", "embedding"]:
                    fields.append(f"{k} = ?")
                    params.append(json.dumps(v))
                else:
                    fields.append(f"{k} = ?")
                    params.append(v)
                    
            if not fields:
                conn.close()
                return self.get_item_by_id(item_id)
                
            params.append(item_id)
            query = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return self.get_item_by_id(item_id)

    def delete_item(self, item_id: str) -> bool:
        if self.use_mongo:
            res = self.db.items.delete_one({"_id": item_id})
            return res.deleted_count > 0
        else:
            conn = sqlite3.connect(config.SQLITE_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            count = cursor.rowcount
            conn.commit()
            conn.close()
            return count > 0

    def get_all_embeddings(self) -> list:
        # Helper to get all non-empty embeddings for semantic search calculation
        if self.use_mongo:
            cursor = self.db.items.find({"embedding": {"$exists": True, "$ne": []}})
            results = []
            for doc in cursor:
                results.append({
                    "id": doc.get("_id"),
                    "text": doc.get("text"),
                    "intent": doc.get("intent"),
                    "category": doc.get("category"),
                    "priority": doc.get("priority"),
                    "status": doc.get("status"),
                    "embedding": doc.get("embedding")
                })
            return results
        else:
            conn = sqlite3.connect(config.SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, text, intent, category, priority, status, embedding FROM items WHERE embedding IS NOT NULL AND embedding != '[]'")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["embedding"] = json.loads(item["embedding"])
                results.append(item)
            conn.close()
            return results

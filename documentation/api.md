# API Documentation

The SysAi backend runs on FastAPI and exposes REST endpoints. Below is the API reference.

---

## 🟢 Base Routes

### `GET /`
Returns the status of the local backend, verifying whether SQLite fallback is active and which ML modules are active.
* **Response (JSON)**:
  ```json
  {
    "status": "healthy",
    "service": "Offline AI Personal Productivity Assistant",
    "version": "1.0.0",
    "database": "SQLite",
    "ml_models_loaded": true,
    "semantic_embeddings_loaded": true
  }
  ```

---

## 📝 Task Management Routes

### `POST /api/tasks/capture`
Submits raw text input, runs local classification (Intent, Category, Priority), parses date expressions, extracts tags, and inserts the item.
* **Request Body (JSON)**:
  ```json
  {
    "text": "Send contract to Acme Corp tomorrow at 3pm"
  }
  ```
* **Response (JSON)**:
  ```json
  {
    "success": true,
    "item": {
      "id": "e7b0e14a-f38b-4a49-968b-5777a83d7350",
      "text": "Send contract to Acme Corp tomorrow at 3pm",
      "intent": "Task",
      "category": "Work",
      "priority": "High",
      "status": "pending",
      "due_date": "2026-06-26T15:00:00",
      "tags": ["work", "contract", "send", "acme"],
      "created_at": "2026-06-25T09:18:24.123456",
      "completed_at": null
    },
    "meta": {
      "model_type": "trained ML models",
      "has_embedding": true
    }
  }
  ```

### `GET /api/tasks`
Lists all saved tasks, reminders, and notes. Supports URL query parameters for filtering and smart hybrid search.
* **Query Parameters**:
  - `status` (Optional): "pending" | "completed"
  - `intent` (Optional): "Task" | "Note" | "Reminder" | "Todo"
  - `category` (Optional): "Work" | "Study" | "Shopping" | "Health" | "Personal" | "Finance"
  - `priority` (Optional): "High" | "Medium" | "Low"
  - `q` (Optional): String query. Triggers hybrid semantic + keyword search.
* **Response (JSON)**:
  ```json
  [
    {
      "id": "e7b0e14a-f38b-4a49-968b-5777a83d7350",
      "text": "Send contract to Acme Corp tomorrow at 3pm",
      "intent": "Task",
      "category": "Work",
      "priority": "High",
      "status": "pending",
      "due_date": "2026-06-26T15:00:00",
      "tags": ["work", "contract", "send", "acme"],
      "created_at": "2026-06-25T09:18:24.123456",
      "completed_at": null,
      "score": 0.9412
    }
  ]
  ```

### `GET /api/tasks/{task_id}`
Returns details for a single task.

### `PUT /api/tasks/{task_id}`
Modifies fields of an existing task. If the text field is updated, it automatically regenerates embeddings, tags, and extracts due dates unless manual parameters are passed.
* **Request Body (JSON)**:
  ```json
  {
    "text": "Send revised contract to Acme Corp tomorrow at 4pm",
    "priority": "High"
  }
  ```

### `POST /api/tasks/{task_id}/toggle`
Toggles status of task between "pending" and "completed". Sets `completed_at` timestamp.

### `DELETE /api/tasks/{task_id}`
Deletes the item from database.

---

## 🎙️ Speech-to-Task Routes

### `POST /api/voice/capture`
Accepts a binary audio file upload, transcribes it to text via Vosk, runs the standard NLP/ML task capture pipeline, and saves the task.
* **Request Form-Data**:
  - `file`: WAV audio file binary
* **Response (JSON)**:
  ```json
  {
    "success": true,
    "transcript": "buy fresh tomatoes from market tomorrow",
    "item": {
      "id": "1b08fa11-482a-4311-bf1f-b5b48de9aef8",
      "text": "buy fresh tomatoes from market tomorrow",
      "intent": "Todo",
      "category": "Shopping",
      "priority": "Low",
      "status": "pending",
      "due_date": "2026-06-26T09:00:00",
      "tags": ["shopping", "buy", "fresh", "tomatoes", "market"],
      "created_at": "2026-06-25T09:19:12.333444",
      "completed_at": null
    },
    "meta": {
      "model_type": "trained ML models",
      "has_embedding": true
    }
  }
  ```

---

## 📊 Analytics Routes

### `GET /api/analytics/summary`
Generates the algorithmic daily summary text and overall counts.
* **Response (JSON)**:
  ```json
  {
    "summary": "Today, you captured 4 items with a focus on **Work**. Great job! You achieved a solid completion rate of 75%, finishing 3 tasks. ⚠️ **Attention**: You have 1 pending **High Priority** tasks due. We recommend tackling these first...",
    "metrics": {
      "total_tasks": 4,
      "completed_tasks": 3,
      "pending_tasks": 1,
      "completion_rate": 75,
      "productivity_score": 83,
      "grade": "A",
      "high_priority_pending": 1,
      "focus_category": "Work"
    }
  }
  ```

### `GET /api/analytics/weekly`
Generates multi-dimensional stats for charts representing the last 7 days of logs.
* **Response (JSON)**:
  ```json
  {
    "score": 78,
    "total_tasks": 28,
    "completed_tasks": 22,
    "pending_tasks": 6,
    "completion_rate": 78,
    "daily_trends": [
      { "day": "Mon", "Created": 4, "Completed": 3 },
      { "day": "Tue", "Created": 6, "Completed": 5 }
      // ...
    ],
    "category_distribution": [
      { "name": "Work", "value": 12 },
      { "name": "Study", "value": 8 }
      // ...
    ],
    "priority_distribution": [
      { "name": "High", "value": 6 },
      { "name": "Medium", "value": 15 },
      { "name": "Low", "value": 7 }
    ]
  }
  ```

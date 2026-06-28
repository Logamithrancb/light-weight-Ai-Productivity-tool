# Installation Guide

Follow these steps to set up and run the SysAi assistant on your local machine.

---

## 📋 Prerequisites

- **Python**: Version 3.8 to 3.12 (highly recommended).
- **Node.js**: Version 18.x or 20.x (packaged with `npm`).
- **MongoDB** (Optional): Version 5.x or 6.x. The backend automatically switches to SQLite if MongoDB is not found running.

---

## 🐍 Backend Setup (Python)

1. **Clone/Navigate** to the project folder:
   ```bash
   cd d:/hackton (lwt)/backend
   ```

2. **Create a Virtual Environment** (Highly Recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Core Dependencies**:
   Install all backend libraries using the requirements file:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Windows, installing `sentence-transformers` and `scipy` can take up to 2-3 minutes as they resolve dependencies like PyTorch.*

---

## 🎙️ Speech Model Installation (Vosk)

The assistant uses an offline speech recognition model. You do not need to download this manually:
- The backend contains an **automatic download helper** (`VoiceService`).
- On the first API call to the voice transcription endpoint (`POST /api/voice/capture`), the server checks if the model directory `backend/vosk_model` exists.
- If it is missing, the service automatically downloads the lightweight English acoustic model `vosk-model-small-en-us-0.15` (approx. 40MB) and extracts it for you.
- Alternatively, you can download it yourself from [Alpha Cephei](https://alphacephei.com/vosk/models) and unzip it into `backend/vosk_model/`.

---

## 💻 Frontend Setup (React)

1. **Navigate** to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. **Install Node packages**:
   ```bash
   npm install --legacy-peer-deps
   ```
   *Note: Using `--legacy-peer-deps` is recommended when using React 19 to bypass peer warnings from libraries like Recharts.*

3. **Verify Configuration**:
   The frontend connects to the backend on `http://127.0.0.1:8000` by default. You can adjust this configuration at the top of [App.jsx](file:///d:/hackton%20(lwt)/frontend/src/App.jsx) if your backend runs on a different port.

---

## ⚡ Running the Application

### 1. Training ML Models
Before launching the server, train your models so the backend uses optimized classification:
```bash
# Navigate to the root directory
cd d:/hackton (lwt)

# Run synthetic dataset generation
python ml/datasets/generate_dataset.py

# Run training
python ml/training/train.py
```

### 2. Launch FastAPI
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Launch React Dashboard
```bash
cd ../frontend
npm run dev
```
Open your browser and navigate to `http://localhost:5173`.

from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.database import ProductivityDB
from backend.app.services.ml_service import MLService
from backend.app.services.nlp_service import NLPService
from backend.app.services.voice_service import VoiceService

router = APIRouter(prefix="/api/voice", tags=["Voice"])

db = ProductivityDB()
ml_service = MLService()
nlp_service = NLPService()
voice_service = VoiceService()

@router.post("/capture")
async def capture_voice_task(file: UploadFile = File(...)):
    """Receives audio file (WAV), transcribes it, and captures the task."""
    if not file.filename.lower().endswith(('.wav', '.webm', '.ogg', '.mp3')):
        raise HTTPException(status_code=400, detail="Unsupported audio format. WAV preferred.")
        
    try:
        # Read uploaded audio bytes
        audio_bytes = await file.read()
        
        # 1. Transcribe audio to text
        print(f"Transcribing voice file: {file.filename} ({len(audio_bytes)} bytes)")
        text = voice_service.transcribe_audio_bytes(audio_bytes)
        
        if not text.strip():
            raise HTTPException(status_code=422, detail="Could not transcribe any words from the audio. Please speak clearly.")
            
        # 2. Run ML classification (Intent, Category, Priority)
        predictions = ml_service.predict(text)
        
        # 3. Run NLP details
        due_date = nlp_service.extract_due_date(text)
        tags = nlp_service.extract_keywords_and_tags(text, predictions["category"])
        embedding = nlp_service.get_embedding(text)
        
        # 4. Save to database
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
            "transcript": text,
            "item": item,
            "meta": {
                "model_type": predictions["method"],
                "has_embedding": len(embedding) > 0
            }
        }
        
    except Exception as e:
        print(f"Voice capture error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process voice capture: {str(e)}")

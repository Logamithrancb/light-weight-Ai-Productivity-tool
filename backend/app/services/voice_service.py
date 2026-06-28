import os
import wave
import urllib.request
import zipfile
import json
import io
from backend.app import config

# Fallback imports setup
try:
    from vosk import Model, KaldiRecognizer
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False
    print("vosk not installed. Voice transcription will not be available.")

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False
    print("soundfile not installed. Conversions of non-standard audio formats will be limited.")

class VoiceService:
    def __init__(self):
        self.model = None
        self._model_downloading = False

    def check_and_download_model(self):
        """Checks if Vosk model exists. If not, downloads and extracts it."""
        if not HAS_VOSK:
            raise RuntimeError("Vosk library is not installed in the python environment.")
            
        model_dir = config.VOSK_MODEL_DIR
        # The zip extracts into a folder named vosk-model-small-en-us-0.15
        expected_folder = os.path.join(model_dir, "vosk-model-small-en-us-0.15")
        
        # If the expected subdirectory or base directory has the model, it's valid
        if os.path.exists(expected_folder) or (os.path.exists(model_dir) and any(f in os.listdir(model_dir) for f in ["am", "conf", "ivector"])):
            # Load the model if not loaded yet
            if not self.model:
                load_path = expected_folder if os.path.exists(expected_folder) else model_dir
                print(f"Loading Vosk model from: {load_path}...")
                self.model = Model(load_path)
            return

        print("Vosk model not found. Downloading lightweight English model (~40MB)...")
        self._model_downloading = True
        
        os.makedirs(model_dir, exist_ok=True)
        zip_path = os.path.join(model_dir, "model.zip")
        
        try:
            # Download model zip file
            urllib.request.urlretrieve(config.VOSK_MODEL_URL, zip_path)
            print("Download complete. Extracting model...")
            
            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)
                
            print("Extraction complete. Cleaning up zip file...")
            os.remove(zip_path)
            
            # Load model
            load_path = expected_folder if os.path.exists(expected_folder) else model_dir
            print(f"Loading Vosk model from: {load_path}...")
            self.model = Model(load_path)
            self._model_downloading = False
            print("Vosk model loaded successfully.")
            
        except Exception as e:
            self._model_downloading = False
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise RuntimeError(f"Failed to download or load Vosk model: {e}")

    def transcribe_audio_file(self, file_path: str) -> str:
        """Transcribes audio from a WAV file path."""
        self.check_and_download_model()
        
        wf = wave.open(file_path, "rb")
        
        # Check audio format validity
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            # If format is incorrect and soundfile is available, try to convert it to correct format
            wf.close()
            if HAS_SOUNDFILE:
                print("Converting audio file to Vosk compatible format (16kHz, mono, PCM 16-bit)...")
                data, samplerate = sf.read(file_path)
                # Resample to 16000 if not already
                # Convert to mono if stereo
                if len(data.shape) > 1:
                    data = data.mean(axis=1)
                
                temp_wav = file_path + "_converted.wav"
                sf.write(temp_wav, data, 16000, subtype='PCM_16')
                
                wf = wave.open(temp_wav, "rb")
                # Prepare clean-up callback
                cleanup_file = temp_wav
            else:
                raise ValueError("Audio must be in WAV format (PCM 16-bit mono). Install soundfile to support auto-conversion.")
        else:
            cleanup_file = None

        # Setup recognizer
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get("text"):
                    results.append(res["text"])
                    
        final_res = json.loads(rec.FinalResult())
        if final_res.get("text"):
            results.append(final_res["text"])
            
        wf.close()
        
        if cleanup_file and os.path.exists(cleanup_file):
            try:
                os.remove(cleanup_file)
            except Exception:
                pass
                
        return " ".join(results)

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> str:
        """Transcribes audio from raw in-memory bytes (WAV format)."""
        temp_file = os.path.join(config.BASE_DIR, "backend", "temp_voice.wav")
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
            
        try:
            transcript = self.transcribe_audio_file(temp_file)
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
                    
        return transcript

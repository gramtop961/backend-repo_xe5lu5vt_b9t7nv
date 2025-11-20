import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# --- Realtime Telemetry via WebSocket ---
# Provides a synthetic multimodal biometrics stream at ~10Hz
async def generate_sample(ts: float):
    import math
    import random
    heart_rate = 55 + int(25 * math.sin(ts / 0.5)) + int(random.random() * 5)
    oxygen = 96 + int(random.random() * 3)
    lactate = 3.8 + random.random() * 0.6
    motion = {
        "x": math.sin(ts / 0.4) * 0.5,
        "y": math.cos(ts / 0.5) * 0.5,
        "z": math.sin(ts / 0.7) * 0.5,
    }
    emg = [0.5 * math.sin(ts / (0.08 + i * 0.01)) + (random.random() - 0.5) * 0.2 for i in range(8)]
    eeg = {
        "alpha": abs(math.sin(ts / 0.9)),
        "beta": abs(math.sin(ts / 0.7)),
        "gamma": abs(math.sin(ts / 0.5)),
        "theta": abs(math.sin(ts / 1.2)),
        "delta": abs(math.sin(ts / 1.5)),
    }
    return {
        "timestamp": int(ts * 1000),
        "heartRate": heart_rate,
        "oxygenSaturation": oxygen,
        "lactateThreshold": lactate,
        "motion": motion,
        "emg": emg,
        "eeg": eeg,
    }

@app.websocket("/ws/telemetry")
async def websocket_telemetry(ws: WebSocket):
    await ws.accept()
    try:
        # Optional: wait for a START message to begin streaming
        # But we stream immediately for simplicity
        while True:
            ts = asyncio.get_event_loop().time()
            sample = await generate_sample(ts)
            await ws.send_text(json.dumps(sample))
            await asyncio.sleep(0.1)  # ~10Hz
    except WebSocketDisconnect:
        # Client disconnected
        return
    except Exception as e:
        try:
            await ws.close(code=1011, reason=str(e))
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

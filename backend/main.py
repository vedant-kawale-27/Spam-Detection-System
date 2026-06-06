import os
import joblib
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.xai_service import get_explanation

# import environment config
from backend.config import FRONTEND_URL, BASE_URL, PORT

# Load your models
# Ensure these files are in the root directory

model = joblib.load("backend/linear_svm_model.pkl")
vectorizer = joblib.load("backend/tfidf_vectorizer.pkl")

app = FastAPI(title="Spam Detection System")

# ── CORS setup ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        os.getenv("FRONTEND_DEV_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prediction Model Input Schema ─────────────────────────────
class PredictIn(BaseModel):
    text: str
    type: str

# ── Prediction Route ──────────────────────────────────────────
@app.post("/predict")
def predict(body: PredictIn):
    try:
        # Vectorize
        vectorized_text = vectorizer.transform([body.text])
        
        # 1. FIX: Use .item() to convert numpy.int64 to a standard Python int
        prediction = model.predict(vectorized_text)[0].item() 
        
        # 2. Add the explanation (as we did before)
        explanation = get_explanation(body.text)
        
        # 3. Return the clean data
        return {
            "prediction": prediction,
            "explanation": explanation
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ── Basic health check ────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Spam Detection API is running",
        "base_url": BASE_URL,
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# -- EMAIL DATABASE ROUTES (Issue #13) -------------------------
from backend.emails import router as emails_router
# from backend.database import init_db # Uncomment if DB is set up

# init_db()
app.include_router(emails_router)

# ── Optional: run directly ─────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=True)
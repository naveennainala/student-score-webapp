# =========================================================
# Student Score Prediction - Backend API
# =========================================================
# This wraps your original training script in a web server.
# Instead of running the script once and printing a result,
# it trains the model ONE TIME when the server starts, then
# waits for the frontend to send new student data and replies
# with a prediction — as many times as needed.
# =========================================================

import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file and loads TABPFN_TOKEN into the environment

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from tabpfn import TabPFNRegressor

app = FastAPI(title="Student Score Prediction API")

# CORS lets the frontend (running on a different address/port)
# talk to this backend. Without this, browsers block the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # in production, replace "*" with your real frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# This holds the trained model in memory once it's ready.
model = None
metrics = {}


class StudentInput(BaseModel):
    """This defines exactly what shape of data the /predict endpoint expects.
    FastAPI automatically validates incoming requests against this."""
    hours_studied: float
    previous_scores: float
    extracurricular_activities: str  # "Yes" or "No"
    sleep_hours: float
    sample_question_papers_practiced: float


@app.on_event("startup")
def train_model_on_startup():
    """Runs once, automatically, when the server starts.
    This is the same logic as your original script, just moved here
    so it happens once instead of every single prediction."""
    global model, metrics

    token = os.getenv("TABPFN_TOKEN")
    if not token or token == "your-api-key-here":
        raise RuntimeError(
            "TABPFN_TOKEN is missing. Copy .env.example to .env and add your real key."
        )
    os.environ["TABPFN_TOKEN"] = token

    csv_path = os.path.join(os.path.dirname(__file__), "Student_Performance.csv")
    df = pd.read_csv(csv_path)

    df["Extracurricular Activities"] = df["Extracurricular Activities"].map({"Yes": 1, "No": 0})

    X = df.drop("Performance Index", axis=1)
    y = df["Performance Index"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    X_train_small = X_train.sample(min(1000, len(X_train)), random_state=42)
    y_train_small = y_train.loc[X_train_small.index]

    trained_model = TabPFNRegressor()
    trained_model.fit(X_train_small, y_train_small)

    # Quick accuracy check, same as your original script, logged for reference.
    predictions = trained_model.predict(X_test)
    metrics["mae"] = float(mean_absolute_error(y_test, predictions))
    metrics["r2"] = float(r2_score(y_test, predictions))

    model = trained_model
    print(f"Model trained. MAE={metrics['mae']:.3f}  R2={metrics['r2']:.3f}")


@app.get("/health")
def health():
    """Lets the frontend (or you, in a browser) check whether the model
    has finished training and is ready to make predictions."""
    return {"status": "ok", "model_ready": model is not None, "metrics": metrics}


@app.post("/predict")
def predict(student: StudentInput):
    """Receives one student's data as JSON, returns the predicted score."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model is still training, try again shortly.")

    extracurricular_num = 1 if student.extracurricular_activities.strip().lower() == "yes" else 0

    input_df = pd.DataFrame({
        "Hours Studied": [student.hours_studied],
        "Previous Scores": [student.previous_scores],
        "Extracurricular Activities": [extracurricular_num],
        "Sleep Hours": [student.sleep_hours],
        "Sample Question Papers Practiced": [student.sample_question_papers_practiced],
    })

    prediction = model.predict(input_df)
    return {"predicted_performance_index": round(float(prediction[0]), 2)}

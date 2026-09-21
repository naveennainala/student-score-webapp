# Student Score Predictor — Webapp

This turns your training script into a real webapp:
- **backend/** — a server that trains the model once and answers prediction requests
- **frontend/** — a webpage with a form where you enter student info and see the prediction

---

## Part 1 — Run it on your own computer

### Step 1: Open a terminal in the `backend` folder
This is where all backend commands run.

```
cd student-score-webapp/backend
```

### Step 2: Install the required libraries
This reads `requirements.txt` and installs everything the backend needs (FastAPI, pandas, tabpfn, etc).

```
pip install -r requirements.txt
```

### Step 3: Add your TabPFN API key
Copy the example env file and edit it:

```
cp .env.example .env
```

Open `.env` in any text editor and replace `your-api-key-here` with your real key from https://ux.priorlabs.ai/account

> This keeps your key out of the code itself — `.env` should never be shared or uploaded anywhere public.

### Step 4: Start the backend server

```
uvicorn main:app --reload
```

You should see `Model trained. MAE=... R2=...` in the terminal once it finishes training. Leave this terminal running — it's your live server.

Check it worked by opening this in a browser: **http://localhost:8000/health**
You should see `"model_ready": true`.

### Step 5: Open the frontend
No installation needed — just open the file directly:

```
frontend/index.html
```

(Double-click it, or drag it into your browser.) You'll see the form. Fill in some values and click **Predict Score** — it sends your data to the backend running in Step 4 and shows the result.

---

## What's actually happening (the connections)

```
[ index.html ]  --fetch("/predict")-->  [ FastAPI backend ]  --uses-->  [ TabPFN model ]
   (your browser)                        (localhost:8000)                (trained on your CSV)
```

- The **CSV** lives in `backend/` and is only read once, when the server starts.
- The **model** trains once at startup and stays in the server's memory — each prediction reuses it instead of retraining.
- The **frontend** never talks to the model directly. It only ever calls the backend's web address (`/predict`), the same way any website talks to any server.
- `.env` holds your secret key. `main.py` reads it through `os.getenv(...)` — the key itself never appears in code you might later share or push to GitHub.

---

## Part 2 — Putting it online (deploying)

Two things go live separately, and then get pointed at each other:

1. **Deploy the backend** to a service like Render or Railway.
   - Push the `backend/` folder to a GitHub repo.
   - Create a new "Web Service" on Render/Railway pointing at that repo.
   - Set the start command to: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add `TABPFN_TOKEN` as an environment variable in the hosting dashboard (not in a file this time — the host stores it securely for you).
   - You'll get a public URL like `https://your-app.onrender.com`.

2. **Deploy the frontend** to a service like Netlify or Vercel.
   - Push the `frontend/` folder to a GitHub repo (or the same one).
   - Connect it in Netlify/Vercel — it'll host `index.html` automatically.
   - Open `index.html` and change the line:
     ```js
     const API_URL = "http://localhost:8000";
     ```
     to your real backend URL from step 1, e.g.:
     ```js
     const API_URL = "https://your-app.onrender.com";
     ```

3. **Note on TabPFN**: because your model calls TabPFN's cloud service for every prediction, your hosted backend needs outbound internet access (most hosts allow this by default) and the API key set correctly in that host's environment variables.

---

## Troubleshooting

| Problem | Likely cause |
|---|---|
| "Can't reach the backend" on the webpage | The `uvicorn` server (Step 4) isn't running |
| `TABPFN_TOKEN is missing` error on startup | `.env` file missing or key not replaced |
| `Student_Performance.csv` not found | Make sure the CSV stayed inside `backend/` |
| CORS error in browser console | Only happens if you edit `allow_origins` in `main.py` — leave it as `["*"]` while testing locally |

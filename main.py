from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

EMAIL = "24f2007252@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-3hxo59.example.com",
    # Allow the exam page as well
    "https://exam.sanand.workers.dev",
]

RATE_LIMIT = 15
WINDOW = 10

app = FastAPI()

# ---------------- CORS ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# client_id -> timestamps
rate_limit = {}


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------- Rate Limit ----------
    client = request.headers.get("X-Client-Id")

    if client:
        now = time.time()

        timestamps = rate_limit.get(client, [])

        timestamps = [t for t in timestamps if now - t < WINDOW]

        if len(timestamps) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": "10",
                    "X-Request-ID": request_id,
                },
                content={
                    "detail": "Too Many Requests"
                },
            )

        timestamps.append(now)

        rate_limit[client] = timestamps

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def home():
    return {
        "status": "running"
    }


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

EMAIL = "24f2007252@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-3hxo59.example.com",
    # Exam page origin (keep this)
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
rate_limit_store = {}

# ---------------- Request Context ----------------

@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # ALWAYS echo the request ID
    response.headers["X-Request-ID"] = request_id

    return response


# ---------------- Rate Limiter ----------------

@app.middleware("http")
async def rate_limiter(request: Request, call_next):

    client = request.headers.get("X-Client-Id")

    if client:

        now = time.time()

        timestamps = rate_limit_store.get(client, [])

        timestamps = [t for t in timestamps if now - t < WINDOW]

        if len(timestamps) >= RATE_LIMIT:

            request_id = getattr(
                request.state,
                "request_id",
                request.headers.get("X-Request-ID", str(uuid.uuid4()))
            )

            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": "10",
                    "X-Request-ID": request_id,
                },
                content={
                    "detail": "Too Many Requests"
                }
            )

        timestamps.append(now)

        rate_limit_store[client] = timestamps

    return await call_next(request)


# ---------------- Home ----------------

@app.get("/")
def home():
    return {"status": "running"}


# ---------------- Ping ----------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }

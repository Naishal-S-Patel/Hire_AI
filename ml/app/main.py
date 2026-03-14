from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.routers import ml_router

app = FastAPI(title="AI Recruitment ML Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip middleware — only compress responses larger than 1MB to avoid
# small JSON responses being returned as compressed bytes
app.add_middleware(GZipMiddleware, minimum_size=1024 * 1024)

# Include ML router with /ml/v1 prefix
app.include_router(ml_router.router)

# Also include parse_resume at root level for backward compatibility
app.include_router(ml_router.root_router)


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "ML Service"}
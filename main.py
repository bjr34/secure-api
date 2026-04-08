from fastapi import FastAPI
from database.db import Base, engine

Base.metadata.create_all(bind=engine)
# This ensures tables exist before any request arrives
app = FastAPI()

# TODO: Import and include your routes
# Hint: from routes.api import router
# Then: app.include_router(router)


@app.get("/health")
def health_check():
    """Simple endpoint to verify the API is running."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    # Run the FastAPI application with Uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development").lower() == "development"
    )
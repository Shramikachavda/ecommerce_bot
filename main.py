from fastapi import FastAPI
from routes.chat_api import router
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="FarmNest Chatbot",
    description="Production-ready AI chatbot for agricultural product queries",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "FarmNest Chatbot is running! Connect via WebSocket at /chat"}

# Include WebSocket router
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
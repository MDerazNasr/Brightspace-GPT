from fastapi import FastAPI

app = FastAPI(title="uOttawa Brightspace Assistant")

@app.get("/")
async def root():
    return {
        "message": "uOttawa Brightspace LLM Assistant API",
        "version": "1.0.0", 
        "status": "running"
    }

@app.get("/test")
async def test():
    return {"test": "success"}

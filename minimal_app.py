from fastapi import FastAPI
import sys

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World", "python_version": sys.version}

if __name__ == "__main__":
    import uvicorn
    print("Starting server...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8008)

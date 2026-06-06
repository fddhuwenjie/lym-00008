import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import fastapi
    print(f"FastAPI version: {fastapi.__version__}")
except ImportError:
    print("FastAPI not installed")

try:
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError:
    print("Uvicorn not installed")

try:
    import pydantic
    print(f"Pydantic version: {pydantic.__version__}")
except ImportError:
    print("Pydantic not installed")

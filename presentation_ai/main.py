import os
os.environ["TEMP"] = "E:\\Slide_Generator\\temp"
os.environ["TMP"] = "E:\\Slide_Generator\\temp"
os.makedirs("E:\\Slide_Generator\\temp", exist_ok=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tempfile
from api.routes import router

app = FastAPI(title="Presentation AI API")

# Enable CORS for all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount temporary directory for serving generated images and diagrams to the frontend
app.mount("/static", StaticFiles(directory=tempfile.gettempdir()), name="static")

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Presentation AI API. Use POST /generate to create slides."}



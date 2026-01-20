from fastapi import FastAPI
from fastapi.responses import FileResponse
import os


app = FastAPI()


@app.get("/dashboard.html")
def dashboard_html():
    path = os.path.join(os.path.dirname(__file__), "../../dashboard_modern.html")
    return FileResponse(path, media_type="text/html")

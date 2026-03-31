from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.preview import router as preview_router

app = FastAPI(
    title="Bag Builders Exchange",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(preview_router, prefix="/api")

app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
app.mount("/js", StaticFiles(directory="static/js"), name="js")


@app.get("/")
def landing_page():
    return FileResponse("static/index.html")


@app.get("/docs")
def docs_page():
    return FileResponse("static/docs.html")


@app.get("/support")
def support_page():
    return FileResponse("static/support.html")


@app.get("/terms")
def terms_page():
    return FileResponse("static/terms.html")


@app.get("/privacy")
def privacy_page():
    return FileResponse("static/privacy.html")


@app.get("/disclaimer")
def disclaimer_page():
    return FileResponse("static/disclaimer.html")
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import models  # noqa: F401
from app.database import Base, engine, get_db
from app.routes.auth import (
    require_current_user,
    require_tool_access,
    router as auth_router,
)
from app.routes.preview import router as preview_router
from app.routes.stripe_routes import router as stripe_router

SESSION_SECRET = os.getenv("SESSION_SECRET")
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

if not SESSION_SECRET:
    raise RuntimeError(
        "SESSION_SECRET is missing. Add it to your .env file."
    )


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Bag Builders Exchange",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


session_options = {
    "secret_key": SESSION_SECRET,
    "session_cookie": "bbe_session",
    "max_age": 60 * 60 * 24,
    "same_site": "lax",
    "https_only": IS_PRODUCTION,
}

if IS_PRODUCTION:
    session_options["domain"] = ".bagbuildersexchange.com"

app.add_middleware(
    SessionMiddleware,
    **session_options,
)


app.include_router(preview_router, prefix="/api")
app.include_router(auth_router)
app.include_router(stripe_router)


app.mount(
    "/assets",
    StaticFiles(directory="static/assets"),
    name="assets",
)

app.mount(
    "/js",
    StaticFiles(directory="static/js"),
    name="js",
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/")
def landing_page():
    return FileResponse("static/index.html")


@app.get("/qqq")
@app.get("/qqq/")
def qqq_page(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, "qqq-live-chart")

    return FileResponse("static/qqq/index.html")


@app.get("/spy")
@app.get("/spy/")
def spy_page(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, "spy-live-chart")

    return FileResponse("static/spy/index.html")


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


@app.get("/login")
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/account",
            status_code=303,
        )

    return FileResponse("static/auth/login.html")


@app.get("/register")
def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/account",
            status_code=303,
        )

    return FileResponse("static/auth/register.html")

@app.get("/pricing")
def pricing_page():
    return FileResponse("static/auth/pricing.html")

@app.get("/account")
def account_page(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    return FileResponse("static/auth/account.html")
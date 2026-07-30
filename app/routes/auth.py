import os
import re

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Response
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


PLAN_ACCESS = {
    "free": {
        "dashboard",
        "education",
        "market-status",
    },

    "starter": {
        "dashboard",
        "education",
        "market-status",
        "qqq-live-chart",
        "spy-live-chart",
    },

    "trader": {
        "dashboard",
        "education",
        "market-status",
        "qqq-live-chart",
        "spy-live-chart",
        "qqq-scale-board",
        "spy-scale-board",
    },

    "professional": {
        "dashboard",
        "education",
        "market-status",
        "qqq-live-chart",
        "spy-live-chart",
        "qqq-scale-board",
        "spy-scale-board",
        "impulse",
        "leap",
    },
}

PAID_PLANS = {
    "starter",
    "trader",
    "professional",
}

KNOWN_TOOLS = set().union(*PLAN_ACCESS.values())


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    city: str
    state: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def normalize_plan(plan: str | None) -> str:
    return (plan or "free").strip().lower()


def normalize_tool(tool: str) -> str:
    return tool.strip().lower()

##This makes a free user behave like Professional during the active trial without changing their saved plan.

def normalize_utc(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def has_active_trial(user: User) -> bool:
    trial_ends_at = normalize_utc(user.trial_ends_at)

    if trial_ends_at is None:
        return False

    return datetime.now(timezone.utc) < trial_ends_at


def get_effective_plan(user: User) -> str:
    stored_plan = normalize_plan(user.membership_plan)

    if stored_plan in PAID_PLANS:
        return stored_plan

    if has_active_trial(user):
        return "professional"

    return "free"


def serialize_user(user: User) -> dict:
    membership_plan = normalize_plan(user.membership_plan)
    effective_plan = get_effective_plan(user)
    trial_active = has_active_trial(user)

    trial_started_at = normalize_utc(user.trial_started_at)
    trial_ends_at = normalize_utc(user.trial_ends_at)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "username": user.username,
        "city": user.city,
        "state": user.state,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "membership_status": user.membership_status,
        "membership_plan": membership_plan,
        "effective_plan": effective_plan,
        "trial_active": trial_active,
        "trial_started_at": (
            trial_started_at.isoformat()
            if trial_started_at
            else None
        ),
        "trial_ends_at": (
            trial_ends_at.isoformat()
            if trial_ends_at
            else None
        ),
        "trial_used": bool(user.trial_used),

        "stripe_customer_id": user.stripe_customer_id,
        "stripe_subscription_id": user.stripe_subscription_id,
        "stripe_subscription_status": user.stripe_subscription_status,
        "stripe_price_id": user.stripe_price_id,

        "allowed_tools": sorted(
            PLAN_ACCESS.get(effective_plan, set())
        ),
    }


def require_current_user(
    request: Request,
    db: Session,
) -> User:
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="You must log in to access this resource.",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user or not user.is_active:
        request.session.clear()

        raise HTTPException(
            status_code=401,
            detail="Your session is no longer valid.",
        )

    return user

def require_tool_access(
    user: User,
    tool: str,
) -> User:
    normalized_tool = normalize_tool(tool)

    stored_plan = normalize_plan(user.membership_plan)
    effective_plan = get_effective_plan(user)

    membership_status = (
        user.membership_status or "inactive"
    ).strip().lower()

    if normalized_tool not in KNOWN_TOOLS:
        raise HTTPException(
            status_code=404,
            detail="Unknown platform tool.",
        )

    if stored_plan not in PLAN_ACCESS:
        raise HTTPException(
            status_code=403,
            detail="Your account has an unrecognized subscription plan.",
        )

    if effective_plan not in PLAN_ACCESS:
        raise HTTPException(
            status_code=403,
            detail="Your account has an unrecognized access plan.",
        )

    # A stored paid plan must have an active subscription.
    # A free account with an active trial does not require one.
    if (
        stored_plan in PAID_PLANS
        and membership_status != "active"
    ):
        raise HTTPException(
            status_code=403,
            detail="An active subscription is required.",
        )

    if normalized_tool not in PLAN_ACCESS[effective_plan]:
        raise HTTPException(
            status_code=403,
            detail="Your current access level does not include this tool.",
        )

    return user


@router.get("/access/{tool}")
def authorize_tool(
    tool: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, tool)

    return Response(status_code=204)
    
@router.post("/register")
def register_user(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):

    email = payload.email.lower().strip()
    full_name = payload.full_name.strip()
    username = payload.username.strip().lower()
    city = payload.city.strip()
    state = payload.state.strip().upper()

    password_bytes = payload.password.encode("utf-8")

    if len(full_name) < 2 or len(full_name) > 120:
        raise HTTPException(
            status_code=400,
            detail="Full name must be between 2 and 120 characters.",
        )

    if not re.fullmatch(r"[a-z0-9_]{3,30}", username):
        raise HTTPException(
            status_code=400,
            detail=(
                "Username must be 3 to 30 characters and may "
                "contain only lowercase letters, numbers, and underscores."
            ),
        )

    if len(city) < 2 or len(city) > 100:
        raise HTTPException(
            status_code=400,
            detail="City must be between 2 and 100 characters.",
        )

    if not re.fullmatch(r"[A-Z]{2}", state):
        raise HTTPException(
            status_code=400,
            detail="State must be a valid two-letter abbreviation.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must be 72 bytes or fewer.",
        )

    existing_email = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="An account with that email already exists.",
        )

    existing_username = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="That username is already taken.",
        )

    now = datetime.now(timezone.utc)

    user = User(
        email=email,
        password_hash=password_context.hash(payload.password),
        full_name=full_name,
        username=username,
        city=city,
        state=state,
        membership_plan="free",
        membership_status="inactive",
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=7),
        trial_used=True,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "An account with that email or username already exists."
            ),
        )

    db.refresh(user)
    request.session.clear()
    request.session["user_id"] = user.id

    return {
        "message": (
            "Account created successfully. "
            "Your 7-day Professional trial is active."
        ),
        "user": serialize_user(user),
    }


@router.post("/login")
def login_user(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()

    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=401,
            detail="Invalid email address or password.",
        )

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email address or password.",
        )

    if not password_context.verify(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email address or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="This account is currently disabled.",
        )

    request.session.clear()
    request.session["user_id"] = user.id

    return {
        "message": "Login successful.",
        "user": serialize_user(user),
    }


@router.get("/me")
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)

    return {
        "user": serialize_user(user),
    }


@router.get("/nginx/qqq-live-chart")
def nginx_qqq_live_chart_access(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, "qqq-live-chart")

    return {"allowed": True}

@router.get("/nginx/spy-live-chart")
def nginx_spy_live_chart_access(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, "spy-live-chart")

    return {"allowed": True}
    
@router.post("/logout")
def logout_user(request: Request):
    request.session.clear()

    return {
        "message": "You have been logged out.",
    }


@router.get("/logout")
def logout_user_browser(request: Request):
    request.session.clear()

    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    cookie_options = {
        "key": "bbe_session",
        "path": "/",
        "samesite": "lax",
    }

    if os.getenv("APP_ENV", "development").lower() == "production":
        cookie_options["domain"] = ".bagbuildersexchange.com"
        cookie_options["secure"] = True

    response.delete_cookie(**cookie_options)

    return response
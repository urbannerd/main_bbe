from fastapi import APIRouter, Depends, HTTPException, Request
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
        "qqq-board-scale",
        "spy-board-scale",
    },

    "professional": {
        "dashboard",
        "education",
        "market-status",
        "qqq-live-chart",
        "spy-live-chart",
        "qqq-board-scale",
        "spy-board-scale",
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
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def normalize_plan(plan: str | None) -> str:
    return (plan or "free").strip().lower()


def normalize_tool(tool: str) -> str:
    return tool.strip().lower()


def serialize_user(user: User) -> dict:
    plan = normalize_plan(user.membership_plan)

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "membership_status": user.membership_status,
        "membership_plan": plan,
        "allowed_tools": sorted(PLAN_ACCESS.get(plan, set())),
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
    plan = normalize_plan(user.membership_plan)
    membership_status = (user.membership_status or "inactive").strip().lower()

    if normalized_tool not in KNOWN_TOOLS:
        raise HTTPException(
            status_code=404,
            detail="Unknown platform tool.",
        )

    if plan not in PLAN_ACCESS:
        raise HTTPException(
            status_code=403,
            detail="Your account has an unrecognized subscription plan.",
        )

    # Paid plans must have a currently active subscription.
    if plan in PAID_PLANS and membership_status != "active":
        raise HTTPException(
            status_code=403,
            detail="An active subscription is required.",
        )

    if normalized_tool not in PLAN_ACCESS[plan]:
        raise HTTPException(
            status_code=403,
            detail="Your subscription plan does not include this tool.",
        )

    return user


@router.post("/register")
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()
    password_bytes = payload.password.encode("utf-8")

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

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with that email already exists.",
        )

    user = User(
        email=email,
        password_hash=password_context.hash(payload.password),
        membership_plan="free",
        membership_status="inactive",
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="An account with that email already exists.",
        )

    db.refresh(user)

    return {
        "message": "Account created successfully.",
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


@router.get("/access/{tool}")
def check_tool_access(
    tool: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, tool)

    return {
        "allowed": True,
        "tool": normalize_tool(tool),
        "membership_plan": normalize_plan(user.membership_plan),
        "membership_status": user.membership_status,
    }

@router.get("/nginx/qqq-live-chart")
def nginx_qqq_live_chart_access(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)
    require_tool_access(user, "qqq-live-chart")

    return {"allowed": True}
    
@router.post("/logout")
def logout_user(request: Request):
    request.session.clear()

    return {
        "message": "You have been logged out.",
    }
import os
import re
import hashlib
import secrets
import smtplib

from email.message import EmailMessage
from fastapi import BackgroundTasks

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import (
    EmailVerificationToken,
    PasswordResetToken,
    User,
)
from app.security.turnstile import verify_turnstile
from app.security.email_verification import (
    generate_email_verification_token,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def send_password_reset_email(
    recipient_email: str,
    reset_link: str,
) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
    smtp_from_name = os.getenv(
        "SMTP_FROM_NAME",
        "Bag Builders Exchange",
    )

    missing_settings = [
        name
        for name, value in {
            "SMTP_HOST": smtp_host,
            "SMTP_USERNAME": smtp_username,
            "SMTP_PASSWORD": smtp_password,
            "SMTP_FROM_EMAIL": smtp_from_email,
        }.items()
        if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing SMTP settings: "
            + ", ".join(missing_settings)
        )

    message = EmailMessage()

    message["Subject"] = (
        "Reset your Bag Builders Exchange password"
    )
    message["From"] = (
        f"{smtp_from_name} <{smtp_from_email}>"
    )
    message["To"] = recipient_email

    message.set_content(
        f"""
A password reset was requested for your
Bag Builders Exchange account.

Use the link below to reset your password:

{reset_link}

This link expires in 30 minutes and can only
be used once.

If you did not request this password reset,
you can safely ignore this email.
""".strip()
    )

    message.add_alternative(
        f"""
<!doctype html>
<html lang="en">
  <body style="
    margin: 0;
    padding: 32px 18px;
    background: #070708;
    color: #e8e8ea;
    font-family: Arial, sans-serif;
  ">
    <div style="
      max-width: 560px;
      margin: 0 auto;
      padding: 32px;
      border: 1px solid rgba(214, 162, 26, 0.38);
      border-radius: 18px;
      background: #111116;
    ">
      <h1 style="
        margin: 0 0 18px;
        color: #ffcc3c;
        font-size: 28px;
      ">
        Reset Your Password
      </h1>

      <p style="
        margin: 0 0 18px;
        color: #e8e8ea;
        line-height: 1.6;
      ">
        A password reset was requested for your
        Bag Builders Exchange account.
      </p>

      <p style="margin: 28px 0;">
        <a
          href="{reset_link}"
          style="
            display: inline-block;
            padding: 14px 22px;
            border-radius: 12px;
            background: #d6a21a;
            color: #070708;
            font-weight: 700;
            text-decoration: none;
          "
        >
          Reset Password
        </a>
      </p>

      <p style="
        margin: 0 0 14px;
        color: #a9a9b2;
        line-height: 1.6;
      ">
        This link expires in 30 minutes and can
        only be used once.
      </p>

      <p style="
        margin: 0;
        color: #a9a9b2;
        line-height: 1.6;
      ">
        If you did not request this reset, you can
        safely ignore this email.
      </p>
    </div>
  </body>
</html>
""".strip(),
        subtype="html",
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=30,
    ) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(
            smtp_username,
            smtp_password,
        )

        smtp.send_message(message)
    
def send_email_verification_email(
        recipient_email: str,
        verification_link: str,
    ) -> None:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
        smtp_from_name = os.getenv(
            "SMTP_FROM_NAME",
            "Bag Builders Exchange",
        )

        missing_settings = [
            name
            for name, value in {
                "SMTP_HOST": smtp_host,
                "SMTP_USERNAME": smtp_username,
                "SMTP_PASSWORD": smtp_password,
                "SMTP_FROM_EMAIL": smtp_from_email,
            }.items()
            if not value
        ]

        if missing_settings:
            raise RuntimeError(
                "Missing SMTP settings: "
                + ", ".join(missing_settings)
            )

        message = EmailMessage()

        message["Subject"] = (
            "Verify your Bag Builders Exchange account"
        )
        message["From"] = (
            f"{smtp_from_name} <{smtp_from_email}>"
        )
        message["To"] = recipient_email

        message.set_content(
            f"""
    Thanks for creating your Bag Builders Exchange account.

    Use the link below to verify your email address:

    {verification_link}

    This link expires in 24 hours and can only be used once.

    If you did not create this account, you can safely ignore this email.
    """.strip()
        )

        message.add_alternative(
            f"""
    <!doctype html>
    <html lang="en">
    <body style="
        margin: 0;
        padding: 32px 18px;
        background: #070708;
        color: #e8e8ea;
        font-family: Arial, sans-serif;
    ">
        <div style="
        max-width: 560px;
        margin: 0 auto;
        padding: 32px;
        border: 1px solid rgba(214, 162, 26, 0.38);
        border-radius: 18px;
        background: #111116;
        ">
        <h1 style="
            margin: 0 0 18px;
            color: #ffcc3c;
            font-size: 28px;
        ">
            Verify Your Email
        </h1>

        <p style="
            margin: 0 0 18px;
            color: #e8e8ea;
            line-height: 1.6;
        ">
            Thanks for creating your Bag Builders Exchange account.
            Verify your email address to activate your account and
            begin your 7-day Professional trial.
        </p>

        <p style="margin: 28px 0;">
            <a
            href="{verification_link}"
            style="
                display: inline-block;
                padding: 14px 22px;
                border-radius: 12px;
                background: #d6a21a;
                color: #070708;
                font-weight: 700;
                text-decoration: none;
            "
            >
            Verify Email
            </a>
        </p>

        <p style="
            margin: 0 0 14px;
            color: #a9a9b2;
            line-height: 1.6;
        ">
            This link expires in 24 hours and can only be used once.
        </p>

        <p style="
            margin: 0;
            color: #a9a9b2;
            line-height: 1.6;
        ">
            If you did not create this account, you can safely ignore
            this email.
        </p>
        </div>
    </body>
    </html>
    """.strip(),
            subtype="html",
        )

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=30,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(
                smtp_username,
                smtp_password,
            )

            smtp.send_message(message)


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
    turnstile_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    turnstile_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    turnstile_token: str
class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr
    turnstile_token: str

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
        "email_verified": bool(user.email_verified),
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

    session_version = request.session.get("session_version")

    if session_version != user.session_version:
        request.session.clear()

        raise HTTPException(
            status_code=401,
            detail=(
                "Your session has expired. "
                "Please log in again."
            ),
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
async def register_user(
    payload: RegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):

    if not await verify_turnstile(
        payload.turnstile_token,
        request.client.host if request.client else None,
    ):
        raise HTTPException(
            status_code=400,
            detail="Security verification failed. Please try again.",
        )

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

    raw_token, token_hash, expires_at = (
        generate_email_verification_token()
    )

    user = User(
        email=email,
        password_hash=password_context.hash(payload.password),
        full_name=full_name,
        username=username,
        city=city,
        state=state,
        membership_plan="free",
        membership_status="inactive",
        email_verified=False,
        trial_started_at=None,
        trial_ends_at=None,
        trial_used=False,
    )

    db.add(user)

    try:
        # Assign user.id without committing yet.
        db.flush()

        verification_token = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        db.add(verification_token)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "An account with that email or username already exists."
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create your account. Please try again."
            ),
        )

    app_url = os.getenv(
        "APP_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    verification_link = (
        f"{app_url}/api/auth/verify-email"
        f"?token={raw_token}"
    )

    background_tasks.add_task(
        send_email_verification_email,
        user.email,
        verification_link,
    )

    request.session.clear()

    return {
        "message": (
            "Your account was created. "
            "Please check your email to verify your account."
        ),
        "verification_required": True,
    }


@router.get("/verify-email")
def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    raw_token = token.strip()

    if not raw_token:
        raise HTTPException(
            status_code=400,
            detail="The email verification token is missing.",
        )

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    verification_record = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == token_hash,
        )
        .first()
    )

    if not verification_record:
        raise HTTPException(
            status_code=400,
            detail="This email verification link is invalid.",
        )

    now = datetime.now(timezone.utc)

    if verification_record.used_at is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                "This email verification link has already been used."
            ),
        )

    expires_at = normalize_utc(
        verification_record.expires_at
    )

    if expires_at is None or now >= expires_at:
        verification_record.used_at = now
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="This email verification link has expired.",
        )

    user = (
        db.query(User)
        .filter(User.id == verification_record.user_id)
        .first()
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Unable to verify this account.",
        )

    user.email_verified = True

    if not user.trial_used:
        user.trial_started_at = now
        user.trial_ends_at = now + timedelta(days=7)
        user.trial_used = True

    verification_record.used_at = now

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.id != verification_record.id,
        EmailVerificationToken.used_at.is_(None),
    ).update(
        {
            EmailVerificationToken.used_at: now,
        },
        synchronize_session=False,
    )

    try:
        db.commit()
    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to verify your email. Please try again."
            ),
        )

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["session_version"] = user.session_version

    return RedirectResponse(
        url="/account",
        status_code=303,
    )

@router.post("/resend-verification")
async def resend_verification_email(
    payload: ResendVerificationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not await verify_turnstile(
        payload.turnstile_token,
        request.client.host if request.client else None,
    ):
        raise HTTPException(
            status_code=400,
            detail="Security verification failed. Please try again.",
        )

    email = payload.email.lower().strip()
    now = datetime.now(timezone.utc)

    neutral_response = {
        "message": (
            "If an unverified account exists for that email address, "
            "a new verification email has been sent."
        )
    }

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user or user.email_verified or not user.is_active:
        return neutral_response

    # Limit verification email requests to once per minute.
    one_minute_ago = now - timedelta(minutes=1)

    recent_token = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.created_at >= one_minute_ago,
        )
        .first()
    )

    if recent_token:
        return neutral_response

    # Invalidate earlier unused verification links.
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None),
    ).update(
        {
            EmailVerificationToken.used_at: now,
        },
        synchronize_session=False,
    )

    raw_token, token_hash, expires_at = (
        generate_email_verification_token()
    )

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(verification_token)

    try:
        db.commit()
    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to send a verification email. "
                "Please try again."
            ),
        )

    app_url = os.getenv(
        "APP_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    verification_link = (
        f"{app_url}/api/auth/verify-email"
        f"?token={raw_token}"
    )

    background_tasks.add_task(
        send_email_verification_email,
        user.email,
        verification_link,
    )

    return neutral_response
    
@router.post("/login")
async def login_user(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()

    if not await verify_turnstile(
        payload.turnstile_token,
        request.client.host if request.client else None,
    ):
        raise HTTPException(
            status_code=400,
            detail="Security verification failed. Please try again.",
        )

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

    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail=(
                "Please verify your email address before logging in."
            ),
        )

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["session_version"] = user.session_version

    return {
        "message": "Login successful.",
        "user": serialize_user(user),
    }

@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):

    if not await verify_turnstile(
        payload.turnstile_token,
        request.client.host if request.client else None,
    ):
        raise HTTPException(
            status_code=400,
            detail="Security verification failed. Please try again.",
        )
        
    email = payload.email.lower().strip()
    now = datetime.now(timezone.utc)

    neutral_message = {
        "message": (
            "If an account exists for that email address, "
            "password reset instructions have been sent."
        )
    }

    # ---------------------------------------------------------
    # Clean up reset records that are more than two days old.
    # ---------------------------------------------------------

    cleanup_cutoff = now - timedelta(days=2)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.expires_at < cleanup_cutoff,
    ).delete(synchronize_session=False)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.used_at.is_not(None),
        PasswordResetToken.used_at < cleanup_cutoff,
    ).delete(synchronize_session=False)

    db.commit()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Always return the same response when the account does not exist.
    if not user:
        return neutral_message

    # ---------------------------------------------------------
    # Rate limit 1: no more than one request every 60 seconds.
    # ---------------------------------------------------------

    one_minute_ago = now - timedelta(minutes=1)

    recent_request = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at >= one_minute_ago,
        )
        .first()
    )

    if recent_request:
        return neutral_message

    # ---------------------------------------------------------
    # Rate limit 2: no more than five requests per hour.
    # ---------------------------------------------------------

    one_hour_ago = now - timedelta(hours=1)

    hourly_request_count = (
        db.query(func.count(PasswordResetToken.id))
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at >= one_hour_ago,
        )
        .scalar()
        or 0
    )

    if hourly_request_count >= 5:
        return neutral_message

    # ---------------------------------------------------------
    # Invalidate any older unused reset links.
    # Keep the records so they still count toward rate limits.
    # ---------------------------------------------------------

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update(
        {
            PasswordResetToken.used_at: now,
        },
        synchronize_session=False,
    )

    # ---------------------------------------------------------
    # Generate and store the new reset token.
    # ---------------------------------------------------------

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(minutes=30),
    )

    db.add(reset_token)

    try:
        db.commit()
    except Exception:
        db.rollback()

        # Do not expose internal errors or account existence.
        return neutral_message

    # ---------------------------------------------------------
    # Build the reset URL and send the email.
    # ---------------------------------------------------------

    app_url = os.getenv(
        "APP_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    reset_link = (
        f"{app_url}/reset-password"
        f"?token={raw_token}"
    )

    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        reset_link,
    )

    return neutral_message

@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    raw_token = payload.token.strip()
    password = payload.password
    confirm_password = payload.confirm_password

    if not raw_token:
        raise HTTPException(
            status_code=400,
            detail="The password reset token is missing.",
        )

    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match.",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must be 72 bytes or fewer.",
        )

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        )
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="This password reset link is invalid or has already been used.",
        )

    now = datetime.now(timezone.utc)
    expires_at = normalize_utc(reset_record.expires_at)

    if expires_at is None or now >= expires_at:
        reset_record.used_at = now
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="This password reset link has expired.",
        )

    user = (
        db.query(User)
        .filter(User.id == reset_record.user_id)
        .first()
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Unable to reset the password for this account.",
        )

    user.password_hash = password_context.hash(password)
    user.session_version = (
        user.session_version or 1
    ) + 1
    reset_record.used_at = now

    # Invalidate every other unused reset token for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_record.id,
        PasswordResetToken.used_at.is_(None),
    ).update(
        {
            PasswordResetToken.used_at: now,
        },
        synchronize_session=False,
    )

    try:
        db.commit()
    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update the password. Please try again.",
        )

    # Clear any current browser session after the password changes.
    request.session.clear()

    return {
        "message": (
            "Your password has been reset successfully. "
            "You can now log in with your new password."
        )
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
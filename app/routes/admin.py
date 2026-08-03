import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminAuditLog, User
from app.routes.auth import require_current_user, serialize_user

router = APIRouter(prefix="/api/admin", tags=["admin"])
ALLOWED_PLANS = {"free", "starter", "trader", "professional"}
STRIPE_MANAGED_STATUSES = {"active", "trialing", "past_due"}


class UpdateUserRequest(BaseModel):
    membership_plan: str | None = None
    is_active: bool | None = None


class ForceLogoutRequest(BaseModel):
    confirm: bool = False


def configured_admin_emails() -> set[str]:
    return {
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }


def require_admin(request: Request, db: Session) -> User:
    user = require_current_user(request, db)
    admin_emails = configured_admin_emails()
    if not admin_emails:
        raise HTTPException(503, "Admin access has not been configured.")
    if user.email.lower() not in admin_emails:
        raise HTTPException(403, "Administrator access is required.")
    return user


def require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        return
    expected = f"{request.url.scheme}://{request.url.netloc}"
    if origin.rstrip("/") != expected.rstrip("/"):
        raise HTTPException(403, "Cross-origin admin requests are not allowed.")


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    return user


def serialize_admin_user(user: User) -> dict:
    data = serialize_user(user)
    data["is_admin"] = user.email.lower() in configured_admin_emails()
    data["stripe_managed"] = bool(
        user.stripe_subscription_id
        and user.stripe_subscription_status in STRIPE_MANAGED_STATUSES
    )
    return data


def record_audit(
    db: Session,
    admin: User,
    action: str,
    target: User | None = None,
    details: str | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            admin_email=admin.email,
            target_user_id=target.id if target else None,
            target_email=target.email if target else None,
            action=action,
            details=details,
        )
    )


@router.get("/me")
def admin_me(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    return {"user": serialize_admin_user(user), "is_admin": True}


@router.get("/dashboard")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    now = datetime.now(timezone.utc)
    day_start = now - timedelta(hours=24)
    paid_plans = ["starter", "trader", "professional"]

    def count(*filters):
        return db.query(func.count(User.id)).filter(*filters).scalar() or 0

    stats = {
        "total_users": count(),
        "active_users": count(User.is_active.is_(True)),
        "paid_users": count(User.membership_plan.in_(paid_plans)),
        "trial_users": count(User.trial_ends_at.is_not(None), User.trial_ends_at > now),
        "new_users_24h": count(User.created_at >= day_start),
        "stripe_active": count(User.stripe_subscription_status.in_(["active", "trialing"])),
        "past_due": count(User.stripe_subscription_status == "past_due"),
        "disabled_users": count(User.is_active.is_(False)),
    }
    return {"stats": stats}


@router.get("/users")
def list_users(
    request: Request,
    search: str = Query("", max_length=120),
    status: str = Query("all", pattern="^(all|active|disabled)$"),
    plan: str = Query("all", pattern="^(all|free|starter|trader|professional)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    require_admin(request, db)
    query = db.query(User)
    search = search.strip().lower()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(
            func.lower(User.email).like(like),
            func.lower(func.coalesce(User.full_name, "")).like(like),
            func.lower(func.coalesce(User.username, "")).like(like),
        ))
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "disabled":
        query = query.filter(User.is_active.is_(False))
    if plan != "all":
        query = query.filter(User.membership_plan == plan)

    total = query.count()
    users = query.order_by(User.created_at.desc(), User.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "users": [serialize_admin_user(user) for user in users],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": max(1, (total + page_size - 1) // page_size),
        },
    }


@router.get("/users/{user_id}")
def get_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    return {"user": serialize_admin_user(get_user_or_404(db, user_id))}


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    require_same_origin(request)
    admin = require_admin(request, db)
    user = get_user_or_404(db, user_id)
    changes = []

    if payload.membership_plan is None and payload.is_active is None:
        raise HTTPException(400, "No user changes were supplied.")

    if payload.membership_plan is not None:
        plan = payload.membership_plan.strip().lower()
        if plan not in ALLOWED_PLANS:
            raise HTTPException(400, "Invalid membership plan.")
        if user.stripe_subscription_id and user.stripe_subscription_status in STRIPE_MANAGED_STATUSES:
            raise HTTPException(409, "This plan is managed by Stripe. Change it through Stripe or the billing portal.")
        old_plan = user.membership_plan or "free"
        if old_plan != plan:
            user.membership_plan = plan
            user.membership_status = "active" if plan != "free" else "inactive"
            changes.append(f"plan {old_plan} -> {plan}")

    if payload.is_active is not None and user.is_active != payload.is_active:
        if not payload.is_active and user.id == admin.id:
            raise HTTPException(409, "You cannot disable your own administrator account.")
        if not payload.is_active and user.email.lower() in configured_admin_emails():
            raise HTTPException(409, "Remove this address from ADMIN_EMAILS before disabling it.")
        old_status = "active" if user.is_active else "disabled"
        user.is_active = payload.is_active
        user.session_version = (user.session_version or 1) + 1
        changes.append(f"status {old_status} -> {'active' if user.is_active else 'disabled'}")

    if not changes:
        return {"message": "No changes were needed.", "user": serialize_admin_user(user)}

    record_audit(db, admin, "user.updated", user, "; ".join(changes))
    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully.", "user": serialize_admin_user(user)}


@router.post("/users/{user_id}/force-logout")
def force_logout(
    user_id: int,
    payload: ForceLogoutRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    require_same_origin(request)
    admin = require_admin(request, db)
    user = get_user_or_404(db, user_id)
    if not payload.confirm:
        raise HTTPException(400, "Confirmation is required.")
    if user.id == admin.id:
        raise HTTPException(409, "You cannot force logout your current administrator session.")
    user.session_version = (user.session_version or 1) + 1
    record_audit(db, admin, "user.force_logout", user, "All sessions invalidated")
    db.commit()
    return {"message": "All active sessions for this user have been invalidated."}


@router.get("/subscriptions")
def subscriptions(
    request: Request,
    status: str = Query("all", max_length=30),
    search: str = Query("", max_length=120),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    require_admin(request, db)
    query = db.query(User).filter(User.stripe_subscription_id.is_not(None))
    if status != "all":
        query = query.filter(User.stripe_subscription_status == status)
    if search.strip():
        like = f"%{search.strip().lower()}%"
        query = query.filter(or_(func.lower(User.email).like(like), func.lower(func.coalesce(User.full_name, "")).like(like)))
    total = query.count()
    rows = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "subscriptions": [serialize_admin_user(user) for user in rows],
        "pagination": {"page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)},
    }


@router.get("/audit-logs")
def audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    require_admin(request, db)
    query = db.query(AdminAuditLog)
    total = query.count()
    logs = query.order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "logs": [{
            "id": log.id,
            "admin_email": log.admin_email,
            "target_email": log.target_email,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at,
        } for log in logs],
        "pagination": {"page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)},
    }

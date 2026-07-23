import os
import traceback
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routes.auth import require_current_user


router = APIRouter(
    prefix="/api/stripe",
    tags=["stripe"],
)


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


PRICE_TO_PLAN = {
    os.getenv("STRIPE_STARTER_PRICE_ID"): "starter",
    os.getenv("STRIPE_TRADER_PRICE_ID"): "trader",
    os.getenv("STRIPE_PROFESSIONAL_PRICE_ID"): "professional",
}

PLAN_TO_PRICE = {
    plan: price_id
    for price_id, plan in PRICE_TO_PLAN.items()
    if price_id
}


if not STRIPE_SECRET_KEY:
    raise RuntimeError(
        "STRIPE_SECRET_KEY is missing from the environment."
    )


stripe.api_key = STRIPE_SECRET_KEY


class CheckoutRequest(BaseModel):
    plan: str

class ChangeSubscriptionRequest(BaseModel):
    plan: str


PLAN_RANK = {
    "free": 0,
    "starter": 1,
    "trader": 2,
    "professional": 3,
}

def normalize_stripe_id(value) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        return value

    return getattr(value, "id", None)


def extract_subscription_price_id(
    subscription,
) -> str | None:
    items = stripe_value(subscription, "items")

    if not items:
        return None

    item_data = stripe_value(items, "data", [])

    if not item_data:
        return None

    price = stripe_value(item_data[0], "price")

    return normalize_stripe_id(price)


def membership_status_from_stripe(status: str | None) -> str:
    active_statuses = {
        "active",
        "trialing",
    }

    if status in active_statuses:
        return "active"

    return "inactive"


def apply_subscription_to_user(
    user: User,
    subscription,
) -> None:
    subscription_id = normalize_stripe_id(
        stripe_value(subscription, "id")
    )

    customer_id = normalize_stripe_id(
        stripe_value(subscription, "customer")
    )

    price_id = extract_subscription_price_id(
        subscription
    )

    stripe_status = stripe_value(
        subscription,
        "status",
    )

    plan = PRICE_TO_PLAN.get(price_id)

    user.stripe_customer_id = customer_id
    user.stripe_subscription_id = subscription_id
    user.stripe_price_id = price_id
    user.stripe_subscription_status = stripe_status
    user.membership_status = (
        membership_status_from_stripe(
            stripe_status
        )
    )

    if plan:
        user.membership_plan = plan
    elif user.membership_status != "active":
        user.membership_plan = "free"


def find_user_for_subscription(
    db: Session,
    subscription,
) -> User | None:
    customer_id = normalize_stripe_id(
        stripe_value(subscription, "customer")
    )

    if customer_id:
        user = (
            db.query(User)
            .filter(
                User.stripe_customer_id == customer_id
            )
            .first()
        )

        if user:
            return user

    metadata = stripe_value(
        subscription,
        "metadata",
        {},
    )

    user_id = stripe_value(
        metadata,
        "user_id",
    )

    if user_id:
        try:
            return (
                db.query(User)
                .filter(User.id == int(user_id))
                .first()
            )
        except (TypeError, ValueError):
            return None

    return None


@router.post("/create-checkout-session")
def create_checkout_session(
    payload: CheckoutRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)

    plan = payload.plan.strip().lower()
    price_id = PLAN_TO_PRICE.get(plan)

    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid subscription plan.",
        )

    if user.stripe_subscription_id:
        raise HTTPException(
            status_code=409,
            detail=(
                "You already have a Stripe subscription. "
                "Use Manage Subscription instead."
            ),
        )

    session_options = {
        "mode": "subscription",
        "line_items": [
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        "success_url": (
            f"{APP_BASE_URL}/account"
            "?checkout=success"
            "&session_id={{CHECKOUT_SESSION_ID}}"
        ),
        "cancel_url": (
            f"{APP_BASE_URL}/account"
            "?checkout=cancelled"
        ),
        "client_reference_id": str(user.id),
        "metadata": {
            "user_id": str(user.id),
            "plan": plan,
        },
        "subscription_data": {
            "metadata": {
                "user_id": str(user.id),
                "plan": plan,
            }
        },
        "allow_promotion_codes": True,
    }

    if user.stripe_customer_id:
        session_options["customer"] = (
            user.stripe_customer_id
        )
    else:
        session_options["customer_email"] = user.email

    try:
        checkout_session = (
            stripe.checkout.Session.create(
                **session_options
            )
        )

    except stripe.StripeError as error:
        error_message = (
            getattr(error, "user_message", None)
            or str(error)
        )

        print(
            "Stripe Checkout error:",
            error_message,
        )

        raise HTTPException(
            status_code=502,
            detail=error_message,
        ) from error

    return {
        "checkout_url": checkout_session.url,
    }


def stripe_value(
    obj,
    key: str,
    default=None,
):
    if obj is None:
        return default

    try:
        return obj[key]
    except (KeyError, TypeError, AttributeError):
        return getattr(obj, key, default)

@router.post("/create-portal-session")
def create_portal_session(
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)

    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe customer exists for this account.",
        )

    try:
        portal_session = (
            stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=f"{APP_BASE_URL}/account",
            )
        )
    except stripe.StripeError as error:
        raise HTTPException(
            status_code=502,
            detail="Stripe could not open the customer portal.",
        ) from error

    return {
        "portal_url": portal_session.url,
    }


@router.post("/change-subscription")
def change_subscription(
    payload: ChangeSubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_current_user(request, db)

    target_plan = payload.plan.strip().lower()
    target_price_id = PLAN_TO_PRICE.get(target_plan)

    if not target_price_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid subscription plan.",
        )

    if not user.stripe_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe subscription exists for this account.",
        )

    current_plan = (user.membership_plan or "free").lower()

    if PLAN_RANK.get(target_plan, -1) <= PLAN_RANK.get(current_plan, 0):
        raise HTTPException(
            status_code=400,
            detail="Select a plan above your current membership.",
        )

    try:
        subscription = stripe.Subscription.retrieve(
            user.stripe_subscription_id
        )

        items = stripe_value(subscription, "items")
        item_data = stripe_value(items, "data", [])

        if not item_data:
            raise HTTPException(
                status_code=409,
                detail="The Stripe subscription has no subscription item.",
            )

        subscription_item_id = normalize_stripe_id(item_data[0])

        if not subscription_item_id:
            raise HTTPException(
                status_code=409,
                detail="The Stripe subscription item could not be identified.",
            )

        updated_subscription = stripe.Subscription.modify(
            user.stripe_subscription_id,
            items=[
                {
                    "id": subscription_item_id,
                    "price": target_price_id,
                    "quantity": 1,
                }
            ],
            proration_behavior="always_invoice",
            payment_behavior="error_if_incomplete",
            metadata={
                "user_id": str(user.id),
                "plan": target_plan,
            },
        )

        apply_subscription_to_user(
            user,
            updated_subscription,
        )
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except stripe.StripeError as error:
        db.rollback()
        error_message = (
            getattr(error, "user_message", None)
            or str(error)
        )
        raise HTTPException(
            status_code=502,
            detail=error_message,
        ) from error
    except Exception as error:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Unable to update the subscription.",
        ) from error

    return {
        "updated": True,
        "plan": user.membership_plan,
        "status": user.membership_status,
    }
    
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Stripe webhook secret is not configured.",
        )

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe signature.",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload.",
        ) from error
    except stripe.SignatureVerificationError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature.",
        ) from error

    event_type = event["type"]
    event_object = event["data"]["object"]

    try:
        if event_type == "checkout.session.completed":
            user_id = stripe_value(
                event_object,
                "client_reference_id",
            )
            customer_id = normalize_stripe_id(
                stripe_value(event_object, "customer")
            )
            subscription_id = normalize_stripe_id(
                stripe_value(event_object, "subscription")
            )

            if user_id:
                user = (
                    db.query(User)
                    .filter(User.id == int(user_id))
                    .first()
                )

                if user:
                    user.stripe_customer_id = customer_id
                    user.stripe_subscription_id = (
                        subscription_id
                    )

                    if subscription_id:
                        subscription = (
                            stripe.Subscription.retrieve(
                                subscription_id
                            )
                        )
                        apply_subscription_to_user(
                            user,
                            subscription,
                        )

                    db.commit()

        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            subscription = event_object
            user = find_user_for_subscription(
                db,
                subscription,
            )

            if user:
                apply_subscription_to_user(
                    user,
                    subscription,
                )
                db.commit()

        elif event_type == "invoice.payment_failed":
            customer_id = normalize_stripe_id(
                stripe_value(event_object, "customer")
            )

            user = (
                db.query(User)
                .filter(
                    User.stripe_customer_id == customer_id
                )
                .first()
            )

            if user:
                user.membership_status = "inactive"
                user.stripe_subscription_status = (
                    "past_due"
                )
                db.commit()

    except Exception as error:
        db.rollback()

        print(
            "Stripe webhook processing failed:",
            repr(error),
        )
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed.",
        ) from error

    return {
        "received": True,
    }
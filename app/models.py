from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    email = Column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    membership_status = Column(
        String(20),
        default="inactive",
        server_default="inactive",
        nullable=False,
    )

    membership_plan = Column(
        String(50),
        default="free",
        server_default="free",
        nullable=False,
    )

    qqq_access = Column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )

    spy_access = Column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )

    stripe_customer_id = Column(
        String(255),
        nullable=True,
    )

    stripe_subscription_id = Column(
        String(255),
        nullable=True,
    )
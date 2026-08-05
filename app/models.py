from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User")

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User")
    
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

    session_version = Column(
    Integer,
    nullable=False,
    default=1,
    server_default="1",
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    email_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
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

    full_name = Column(
        String(120),
        nullable=True,
    )

    username = Column(
        String(60),
        nullable=True,
        unique=True,
        index=True,
    )

    city = Column(
        String(100),
        nullable=True,
    )

    state = Column(
        String(2),
        nullable=True,
    )

    trial_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    trial_ends_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    trial_used = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
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
        String,
        unique=True,
        nullable=True,
        index=True,
    )

    stripe_subscription_id = Column(
        String,
        unique=True,
        nullable=True,
        index=True,
    )

    stripe_price_id = Column(
        String,
        nullable=True,
    )

    stripe_subscription_status = Column(
        String,
        nullable=True,
    )

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    admin_email = Column(String(320), nullable=False, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_email = Column(String(320), nullable=True, index=True)
    action = Column(String(80), nullable=False, index=True)
    details = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

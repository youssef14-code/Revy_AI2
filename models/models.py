from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

egypt_tz = pytz.timezone("Africa/Cairo")

db = SQLAlchemy()

# -------------------------
# Users Table
# -------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    summary = db.Column(db.Text)          # ملخص المحادثة
    last_bot_reply = db.Column(db.Text)   # آخر رد من البوت

    # One-to-Many relationship
    appointments = db.relationship(
        "Appointment",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# -------------------------
# Appointments Table
# -------------------------
class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    day = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)

    description = db.Column(db.Text)
    name = db.Column(db.String(120), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(egypt_tz)
    )

    # Foreign Key → users.id
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationship
    user = db.relationship("User", back_populates="appointments" )

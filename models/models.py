from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

egypt_tz = pytz.timezone("Africa/Cairo")

db = SQLAlchemy()

# -------------------------
# Users Table
# -------------------------
class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    summary = db.Column(db.Text)          # ملخص المحادثة
    last_bot_reply = db.Column(db.Text)   # آخر رد من البوت

    # One-to-Many relationship
    appointments = db.relationship(
        "Appointment",
        back_populates="client",
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

    # Foreign Key → clients.id
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=False
    )

    # Relationship
    client = db.relationship("Client", back_populates="appointments" )
# -------------------------
# Jobs Table
# -------------------------
class Job(db.Model):
    __tablename__ = "jobs"

    id           = db.Column(db.Integer, primary_key=True)
    job_name     = db.Column(db.String(120), nullable=False)
    description  = db.Column(db.Text, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    
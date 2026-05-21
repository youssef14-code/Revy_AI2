from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# -------------------------
# Platform Table (Facebook, Instagram, etc.)
# -------------------------
class Platform(db.Model):
    __tablename__ = "platforms"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  # e.g. "facebook"

    pages = db.relationship("Page", back_populates="platform", cascade="all, delete-orphan")


# -------------------------
# Pages Table
# -------------------------
class Page(db.Model):
    __tablename__ = "pages"

    id          = db.Column(db.Integer, primary_key=True)
    token       = db.Column(db.String(255), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey("platforms.id"), nullable=False)

    platform = db.relationship("Platform", back_populates="pages")
    clients  = db.relationship("Client", back_populates="page", cascade="all, delete-orphan")


# -------------------------
# Clients Table
# -------------------------
class Client(db.Model):
    __tablename__ = "clients"

    id            = db.Column(db.Integer, primary_key=True)
    sender_id     = db.Column(db.String(100), nullable=False)  # Facebook sender_id → String مش Integer
    name          = db.Column(db.String(120), nullable=False)
    summary       = db.Column(db.Text)
    last_bot_reply = db.Column(db.Text)
    page_id       = db.Column(db.Integer, db.ForeignKey("pages.id"), nullable=False)

    page = db.relationship("Page", back_populates="clients")

    __table_args__ = (
        db.UniqueConstraint("sender_id", "page_id", name="uq_sender_page"),  # نفس اليوزر ممكن يبعت من pages مختلفة
    )


# -------------------------
# Appointments Table
# -------------------------
class Appointment(db.Model):
    __tablename__ = "appointments"

    id           = db.Column(db.Integer, primary_key=True)
    date         = db.Column(db.String , nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    description  = db.Column(db.Text , nullable=False)
    name         = db.Column(db.String(120), nullable=False)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.utcnow())


# -------------------------
# Jobs Table
# -------------------------
class Job(db.Model):
    __tablename__ = "jobs"

    id           = db.Column(db.Integer, primary_key=True)
    job_name     = db.Column(db.String(120), nullable=False)
    description  = db.Column(db.Text, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
from datetime import datetime, timedelta, timezone
from models.models import db, Client, Appointment


class BookingService:
    @staticmethod
    def book(client: Client, day: str, time: str, phone_number: str, description: str = ""):
        """
        Create a new appointment for a user.
        """

        # Check if appointment already exists
        existing = Appointment.query.filter_by(
            client_id=client.id,
            day=day,
            time=time,
            phone_number=phone_number
        ).first()

        if existing:
            print("⚠️ Appointment already exists")
            return False

        new_appointment = Appointment(
            client_id=client.id,
            name=client.name,
            day=day,
            time=time,
            phone_number=phone_number,
            description=description
        )

        try:
            db.session.add(new_appointment)
            db.session.commit()
            print("✅ Appointment saved successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ BookingService DB Error: {e}")
            return False


class MemoryService:
    @staticmethod
    def update(client: Client, summary: str, last_reply: str):
        try:
            client.summary = summary or ""
            client.last_bot_reply = last_reply
            db.session.add(client)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"❌ MemoryService DB Error: {e}")
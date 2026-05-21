from datetime import datetime, timedelta, timezone
from models.models import db, Client, Appointment
from app import app


class BookingService:
    @staticmethod
    def book(name: str, day: str, time: str, phone_number: str, description: str = ""):
        with app.app_context():
            date_str = f"{day} {time}"  # "March 15 10 AM"
            
            existing = Appointment.query.filter_by(
                date=date_str,
                phone_number=phone_number
            ).first()

            if existing:
                print("⚠️ Appointment already exists")
                return False

            try:
                new_appointment = Appointment(
                    name=name,
                    date=date_str,
                    phone_number=phone_number,
                    description=description
                )
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
        with app.app_context():
            try:
                fresh_client = db.session.get(Client, client.id)
                if fresh_client:
                    fresh_client.summary = summary or ""
                    fresh_client.last_bot_reply = last_reply
                    db.session.commit()
                    print("✅ Memory updated successfully")
                else:
                    print(f"❌ MemoryService: Client id={client.id} not found")
            except Exception as e:
                db.session.rollback()
                print(f"❌ MemoryService DB Error: {e}")
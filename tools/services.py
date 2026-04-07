from datetime import datetime, timedelta, timezone
from models.models import db, Client, Appointment
from agent.app import app    

class BookingService:
    
    @staticmethod
    def book(name: str, day: str, time: str, phone_number: str, description: str = ""):
        with app.app_context():

            # جيب أو اعمل user
            user = User.query.filter_by(name=name).first()
            if not user:
                user = User(name=name)
                db.session.add(user)
                db.session.flush()

            # تحقق إن الحجز مش موجود
            existing = Appointment.query.filter_by(
                user_id=user.id,
                day=day,
                time=time,
                phone_number=phone_number
            ).first()

            if existing:
                print("⚠️ Appointment already exists")
                return False

            new_appointment = Appointment(
                user_id=user.id,      # ← user.id مش 1
                name=name,
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
    def update(user: User, summary: str, last_reply: str):
        """
        Update conversation memory for a user.
        """
        with app.app_context(): 
            try:
                user.summary = summary or ""
                user.last_bot_reply = last_reply
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"❌ MemoryService DB Error: {e}")
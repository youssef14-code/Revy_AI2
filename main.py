# main.py
import sys, os
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from langchain_core.messages import HumanMessage
from graph.graph import build_graph
from models.models import db, Client

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///revy.db"
db.init_app(app)

graph = build_graph()

print("🤖 RevyAI Multi-Agent is running. Type 'exit' to quit.\n")

with app.app_context():
    db.create_all()

    # جيب أو عمل client
    client = Client.query.first()
    if not client:
        client = Client(name="Terminal User")
        db.session.add(client)
        db.session.commit()  

    current_state = {
        "messages": [],
        "next_agent": "",
        "rag_context": "",
        "lead": {},
        "summary": client.summary or "",
        "last_bot_reply": client.last_bot_reply or "",
        "client": client
    }

    while True:
        user_message = input("You: ")
        if user_message.lower() == "exit":
            break
        current_state["client"] = client
        current_state["messages"].append(HumanMessage(content=user_message))
        current_state = graph.invoke(current_state)
        print(f"RevyAI: {current_state['messages'][-1].content}\n")
        print(f"[DEBUG] Summary: {current_state.get('summary')}")
            # ← ضيف دي
        if current_state.get("booking_stage") == "confirmed":
            current_state["booking_stage"] = None
            current_state["lead"] = {}  # امسح الـ lead كمان
            print("[DEBUG] Booking stage reset ✅")
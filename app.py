import os
from flask import Flask, request
from twilio.rest import Client
import openai
from dotenv import load_dotenv

# ─── تحميل متغيرات البيئة من ملف .env ────────────────────────────────────────
load_dotenv()

# ─── إعداد المفاتيح والمتغيرات ───────────────────────────────────────────────
# رابط الـ API (خاص بـ OpenRouter، أو يمكنك حذفه إذا كنت تستخدم api.openai.com مباشرة)
OPENAI_API_BASE    = os.getenv("OPENAI_API_BASE")  
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER= os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER  = os.getenv("USER_PHONE_NUMBER")

# ─── تهيئة عميل OpenAI (v0.28.x) ────────────────────────────────────────────
openai.api_key = OPENAI_API_KEY
if OPENAI_API_BASE:
    openai.api_base = OPENAI_API_BASE

# ─── تهيئة عميل Twilio ───────────────────────────────────────────────────────
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ─── تهيئة Flask ─────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── دالة لإرسال رسالة واتساب عبر Twilio ────────────────────────────────────
def send_whatsapp(message: str):
    twilio_client.messages.create(
        from_ = f"whatsapp:{TWILIO_PHONE_NUMBER}",
        to    = f"whatsapp:{USER_PHONE_NUMBER}",
        body  = message
    )

# ─── الصفحة الرئيسية للاختبار ────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return "✅ Saudabot is running!"

# ─── نقطة استقبال رسائل ويبهوك /bot من Twilio ────────────────────────────────
@app.route("/bot", methods=["POST"])
def bot():
    incoming = request.values.get("Body", "").strip()
    if not incoming:
        return "❌ No text received", 200

    # توليد رد من ChatCompletion
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",        # أو "gpt-4" حسب اشتراكك
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في السعودة."},
                {"role": "user",   "content": incoming}
            ]
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        reply = f"❌ GPT Error: {e}"

    # إرساله عبر واتساب
    send_whatsapp(reply)
    return "OK", 200

# ─── تشغيل التطبيق ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

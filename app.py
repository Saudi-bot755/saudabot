from flask import Flask, request
import os
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from openai import OpenAI

# ─── إعداد المفاتيح من متغيرات البيئة ──────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
TWILIO_SID          = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER   = os.getenv("USER_PHONE_NUMBER")

# ─── تهيئة Flask ─────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── تهيئة OpenAI (الإصدار >=1.0.0) ────────────────────────────────────────
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─── تهيئة Twilio ──────────────────────────────────────────────────────────
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# ─── دالة لإرسال رسالة WhatsApp عبر Twilio ─────────────────────────────────
def send_whatsapp(message: str):
    twilio_client.messages.create(
        from_ = f"whatsapp:{TWILIO_PHONE_NUMBER}",
        to    = f"whatsapp:{USER_PHONE_NUMBER}",
        body  = message
    )

# ─── الصفحة الرئيسية للاختبار ──────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return "✅ سعودة بوت يعمل بنجاح"

# ─── نقطة استقبال ويبهوك /bot من Twilio ────────────────────────────────────
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    if not incoming_msg:
        return "❌ لم يصل نص"
    # توليد الرد من GPT
    reply = generate_response(incoming_msg)
    # إرساله عبر واتساب
    send_whatsapp(reply)
    return "OK"

# ─── دالة توليد رد باستخدام OpenAI ChatCompletion ──────────────────────────
def generate_response(user_text: str) -> str:
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # أو "gpt-4" حسب اشتراكك
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في السعودة."},
                {"role": "user",   "content": user_text}
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ خطأ من GPT: {e}"

# ─── (اختياري) بوت Selenium للتأمينات ───────────────────────────────────────
def run_saudah_bot(code=None):
    try:
        opts = Options()
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        # 👇 استكمل هنا خطوات تسجيل الدخول والقراءة
    except Exception as e:
        print(f"❌ خطأ في بوت السعودة: {e}")

# ─── تشغيل التطبيق ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # المنفذ يقرأ من بيئة Render أو يفرض 5000 محليًا
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

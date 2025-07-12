from flask import Flask, request
import os
import openai
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ─── إعداد المتغيرات من البيئة ────────────────────────────────────────────────
OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER  = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER    = os.getenv("USER_PHONE_NUMBER")

# ─── تهيئة Flask ─────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── تهيئة OpenAI (الإصدار >=1.0.0) ────────────────────────────────────────
openai.api_key = OPENAI_API_KEY

# ─── تهيئة Twilio ──────────────────────────────────────────────────────────
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ─── دالة لإرسال رسالة WhatsApp عبر Twilio ─────────────────────────────────
def send_whatsapp(message: str):
    twilio_client.messages.create(
        from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
        to=f"whatsapp:{USER_PHONE_NUMBER}",
        body=message
    )

# ─── الصفحة الرئيسية للاختبار ──────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return "✅ بوت السعودة يعمل بنجاح"

# ─── نقطة استقبال ويبهوك /bot من Twilio ────────────────────────────────────
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    if not incoming_msg:
        return "❌ لم يصل أي نص"
    reply = generate_response(incoming_msg)
    send_whatsapp(reply)
    return "OK"

# ─── دالة توليد رد باستخدام OpenAI ChatCompletion ──────────────────────────
def generate_response(user_text: str) -> str:
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # أو "gpt-4" إذا متاح
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في إجراءات السعودة."},
                {"role": "user",   "content": user_text}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ خطأ من GPT: {e}"

# ─── بوت الأتمتة باستخدام Selenium (اختياري) ────────────────────────────────
def run_saudah_bot(code: str = None):
    try:
        opts = Options()
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        # هنا: أضف خطوات Selenium لتسجيل الدخول واختيار "أعمال" وإرسال الكود
    except Exception as e:
        print(f"❌ خطأ أثناء تشغيل بوت السعودة: {e}")

# ─── تشغيل التطبيق ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

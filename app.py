from flask import Flask, request
import openai
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# ─── إعداد المتغيرات البيئية ─────────────────────────────────────────────
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
TWILIO_SID         = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER= os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER  = os.getenv("USER_PHONE_NUMBER")

# ─── إعداد Flask ────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── إعداد OpenAI ───────────────────────────────────────────────────────
openai.api_key = OPENAI_API_KEY

# ─── إعداد Twilio ───────────────────────────────────────────────────────
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# ─── دالة إرسال رسالة واتساب ────────────────────────────────────────────
def send_whatsapp(message):
    twilio_client.messages.create(
        from_='whatsapp:' + TWILIO_PHONE_NUMBER,
        to='whatsapp:'   + USER_PHONE_NUMBER,
        body=message
    )

# ─── الصفحة الرئيسة ─────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return "✅ بوت السعودة يعمل بنجاح"

# ─── نقطة استقبال رسائل واتساب من Twilio ─────────────────────────────────
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    if not incoming_msg:
        return "❌ لم يتم إرسال رسالة"
    response = generate_response(incoming_msg)
    send_whatsapp(response)
    return "OK"

# ─── دالة توليد رد باستخدام GPT ─────────────────────────────────────────
def generate_response(message):
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_response(message):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي."},
                {"role": "user", "content": message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ من GPT: {e}"

# ─── (اختياري) بوت السعودة عبر Selenium ─────────────────────────────────
def run_saudah_bot(code=None):
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        # 👇 تابع هنا كتابة أوامر Selenium حسب الحاجة
        # مثال:
        # driver.find_element(By.XPATH, "//button[text()='تسجيل دخول']").click()
    except Exception as e:
        print(f"❌ خطأ أثناء تشغيل بوت السعودة: {e}")

# ─── تشغيل التطبيق ────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

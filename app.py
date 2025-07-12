from flask import Flask, request
import openai
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# إعداد المفاتيح
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")

# إعداد Flask
app = Flask(__name__)

# إعداد مفتاح OpenAI
openai.api_key = OPENAI_API_KEY

# إعداد Twilio
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# إرسال واتساب
def send_whatsapp(message):
    twilio_client.messages.create(
        from_='whatsapp:' + TWILIO_PHONE_NUMBER,
        to='whatsapp:' + USER_PHONE_NUMBER,
        body=message
    )

# الصفحة الرئيسية
@app.route("/", methods=["GET"])
def home():
    return "بوت السعودة يعمل بنجاح ✅"

# نقطة استقبال الرسائل من Twilio
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    if not incoming_msg:
        return "❌ لم يتم إرسال رسالة"
    
    response = generate_response(incoming_msg)
    send_whatsapp(response)
    return "OK"

# توليد رد من GPT
def generate_response(message):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي لبوت السعودة."},
                {"role": "user", "content": message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ من GPT: {e}"

# تشغيل بوت السعودة (تسجيل الدخول والتأمينات)
def run_saudah_bot(code=None):
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.gosi.gov.sa/GOSIOnline/Login")

        # 👇 تابع كتابة أوامر Selenium هنا لتسجيل الدخول وتنفيذ السعودة

    except Exception as e:
        print("❌ خطأ أثناء تشغيل بوت السعودة:", e)

from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Flask
app = Flask(__name__)

def send_whatsapp(message):
    client.messages.create(
        from_="whatsapp:" + TWILIO_PHONE_NUMBER,
        to=USER_PHONE_NUMBER,
        body=message
    )

@app.route("/", methods=["GET"])
def home():
    return "✅ بوت السعودة يعمل بنجاح!"

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    if not incoming_msg:
        return "🚫 لم يتم إرسال رسالة!"

    response = generate_response(incoming_msg)
    send_whatsapp(response)
    return "OK"

def generate_response(message):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",  # أو استخدم gpt-3.5-turbo إذا لم يكن لديك اشتراك GPT-4
            messages=[{"role": "user", "content": message}]
        )
        return completion.choices[0].message["content"]
    except Exception as e:
        return f"❌ خطأ من GPT: {e}"

def run_saudah_bot(code=None):
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

        driver.get("https://www.gosi.gov.sa/GOSIOnline/")

        # ⏳ انتظر الضغط على "تسجيل الدخول" ثم "أعمال"
        # يمكن استخدام selenium للعثور على العناصر والضغط
        # مثال:
        # driver.find_element(By.XPATH, "...").click()

        if code:
            # أكمل الكود في صفحة التحقق
            pass

        # أكمل باقي خطوات السعودة تلقائياً
        # إضافة مشترك، الراتب 4000، المسمى محاسب

        driver.quit()
    except Exception as e:
        send_whatsapp(f"🚨 حدث خطأ أثناء تنفيذ البوت: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
from flask import Flask, request
from twilio.rest import Client
import openai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# —— Load env vars ——
load_dotenv()
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER= os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER  = os.getenv("USER_PHONE_NUMBER")

# —— Init clients ——
openai.api_key = OPENAI_API_KEY
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# —— Flask setup ——
app = Flask(__name__)

# —— Helper: Send WhatsApp ——
def send_whatsapp(message: str):
    client.messages.create(
        from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
        to=  f"whatsapp:{USER_PHONE_NUMBER}",
        body=message
    )

# —— Helper: Extract error from insurance site ——
def check_for_error_message(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    err = soup.find("div", class_="error-message")
    return err.text.strip() if err else None

# —— Health check endpoint ——
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running", 200

# —— Start flow: user sends “سعودة” أو “ابدأ” ——
@app.route("/bot", methods=["POST"])
def bot():
    msg = request.values.get("Body", "").strip().lower()
    if msg not in ["سعودة", "ابدأ"]:
        send_whatsapp("❌ أرسل 'سعودة' أو 'ابدأ' للبدء.")
        return "OK", 200

    send_whatsapp(
        "🔒 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n"
        "1234567890#mypassword"
    )
    return "OK", 200

# —— Receive credentials ——
@app.route("/credentials", methods=["POST"])
def credentials():
    data = request.values.get("Body", "").strip()
    if "#" not in data:
        send_whatsapp("❌ الصيغة غير مفهومة. استخدم: ID#PASSWORD")
        return "OK", 200

    user_id, pwd = data.split("#", 1)
    send_whatsapp("⏳ جاري تسجيل الدخول...")

    # —— Selenium login ——
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://example-insurance-portal.com/login")
        driver.find_element_by_id("id_input").send_keys(user_id)
        driver.find_element_by_id("pwd_input").send_keys(pwd)
        driver.find_element_by_id("submit_btn").click()
        html = driver.page_source
        err_msg = check_for_error_message(html)
        if err_msg:
            send_whatsapp(f"⚠️ فشل الدخول: {err_msg}")
        else:
            send_whatsapp("✅ تم الدخول بنجاح! أرسل 'تحليل' لتحليل البيانات.")
    except Exception as e:
        send_whatsapp(f"❌ خطأ أثناء التصفح: {e}")
    finally:
        driver.quit()

    return "OK", 200

# —— AI analysis endpoint ——
@app.route("/analyze", methods=["POST"])
def analyze():
    send_whatsapp("⏳ جاري معالجة البيانات عبر AI...")
    content = request.values.get("Body", "")
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد لتحليل بيانات التأمينات."},
                {"role": "user",   "content": "حلل هذا النص وقدم ملخصاً:\n" + content}
            ]
        )
        summary = resp.choices[0].message.content.strip()
        send_whatsapp(f"🤖 تحليل AI:\n{summary}")
    except Exception as e:
        send_whatsapp(f"❌ خطأ من AI: {e}")
    return "OK", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

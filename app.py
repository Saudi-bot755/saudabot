import os
from flask import Flask, request
from twilio.rest import Client
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# تحميل متغيرات البيئة
load_dotenv()

# إعداد مفاتيح Twilio
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
user_number = os.getenv("USER_PHONE_NUMBER")

client = Client(twilio_sid, twilio_token)

app = Flask(__name__)

# دالة لإرسال رسالة واتساب عبر Twilio
def send_whatsapp(msg):
    client.messages.create(
        from_="whatsapp:" + twilio_number,
        to="whatsapp:" + user_number,
        body=msg
    )

# دالة تنفيذ الدخول لموقع التأمينات واكتشاف الأخطاء

def process_saudah(id_number, password):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.get("https://www.gosi.gov.sa/GOSIOnline/" )

        # الانتقال لتسجيل الدخول
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "تسجيل الدخول"))).click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "أعمال"))).click()

        # إدخال البيانات
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loginId"))).send_keys(id_number)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "loginButton").click()

        # التحقق من وجود خطأ
        time.sleep(3)
        if "خطأ" in driver.page_source or "المعلومات غير صحيحة" in driver.page_source:
            driver.quit()
            return "❌ فشل تسجيل الدخول، تأكد من رقم الهوية أو كلمة المرور."

        # لو نجح الدخول
        driver.quit()
        return "✅ تم تسجيل الدخول بنجاح! مستعد لإكمال إجراءات السعودة."

    except Exception as e:
        return f"⚠️ حدث خطأ غير متوقع: {str(e)}"

# نقطة البداية للتأكد من عمل البوت
@app.route("/", methods=["GET"])
def home():
    return "🤖 Saudabot يعمل بنجاح", 200

# نقطة استقبال رسالة من المستخدم (واتساب)
@app.route("/bot", methods=["POST"])
def bot():
    msg = request.values.get("Body", "").strip()
    if msg.lower().startswith("سعودة"):
        send_whatsapp("📋 أرسل رقم الهوية متبوعًا بكلمة المرور بهذا الشكل:\nمثال: 1234567890#mypassword")
        return "OK", 200

    if "#" in msg:
        parts = msg.split("#")
        if len(parts) == 2:
            id_number = parts[0].strip()
            password = parts[1].strip()
            result = process_saudah(id_number, password)
            send_whatsapp(result)
            return "OK", 200

    send_whatsapp("❌ صيغة غير مفهومة. أرسل \"سعودة\" للبدء.")
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

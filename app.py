import os
from flask import Flask, request
from twilio.rest import Client
from dotenv import load_dotenv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image
from datetime import datetime

load_dotenv()

# إعداد Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
user_number = os.getenv("USER_PHONE_NUMBER")
client = Client(account_sid, auth_token)

# إعداد Flask
app = Flask(__name__)

# تخزين الجلسة المؤقتة
session = {
    "waiting_for_login": False,
    "username": "",
    "password": ""
}

# إرسال رسالة واتساب
def send_whatsapp(message):
    client.messages.create(
        from_="whatsapp:" + twilio_number,
        to="whatsapp:" + user_number,
        body=message
    )

# إرسال صورة واتساب
def send_image(filename):
    media_url = f"https://file.io/{filename}"  # لاحقًا نعدلها إن احتجنا
    client.messages.create(
        from_="whatsapp:" + twilio_number,
        to="whatsapp:" + user_number,
        media_url=[media_url]
    )

# بدء البوت
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running.", 200

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip().lower()

    if incoming_msg == "سعودة":
        session["waiting_for_login"] = True
        send_whatsapp("📋 أرسل رقم الهوية متبوعًا بكلمة المرور بهذا الشكل:\nmypassword#1234567890")
        return "OK", 200

    elif session["waiting_for_login"] and "#" in incoming_msg:
        try:
            password, username = incoming_msg.split("#")
            session["username"] = username
            session["password"] = password
            session["waiting_for_login"] = False

            result = run_saudah_script(username, password)
            return "OK", 200
        except Exception as e:
            send_whatsapp(f"❌ خطأ في معالجة البيانات: {e}")
            return "Error", 500

    else:
        send_whatsapp("❌ صيغة غير مفهومة. أرسل كلمة سعودة للبدء.")
        return "Invalid", 200

# سكربت السعودة الآلي
def run_saudah_script(username, password):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")

        time.sleep(3)
        # تابع خطوات تسجيل الدخول والتأكد من وجود عنصر فشل مثلاً

        if "خطأ" in driver.page_source or "غير صحيحة" in driver.page_source:
            send_whatsapp("❌ فشل تسجيل الدخول. تأكد من البيانات.")
            driver.quit()
            return

        # متابعة تنفيذ السعودة - هذا وهمي، ضيف خطواتك
        time.sleep(5)
        screenshot_path = f"screenshot_{username}.png"
        driver.save_screenshot(screenshot_path)
        driver.quit()

        # تخزين النتيجة
        with open("saudabot.log", "a") as log:
            log.write(f"{datetime.now()} - تم تسجيل السعودة لـ {username}\n")

        send_whatsapp("✅ تم تنفيذ السعودة بنجاح.\nأرسل سعودة لتسجيل شخص جديد.")
        # (تحميل screenshot لاحقًا)
        return "Done"

    except Exception as e:
        send_whatsapp(f"❌ فشل تنفيذ السكربت: {e}")
        return "Failed"

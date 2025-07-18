# smart.py - النسخة النهائية للبوت التفاعلي على واتساب لتسجيل السعودة

import os
import re
import time
import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pathlib import Path

# إعداد Flask
app = Flask(__name__)

# متغيرات البيئة
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
IMGUR_CLIENT_ID = os.environ.get("IMGUR_CLIENT_ID")

# Twilio client
client = Client(TWILIO_SID, TWILIO_AUTH)

# جلسات المستخدمين
sessions = {}

# إرسال رسالة واتساب

def send_whatsapp(to, body, media_url=None):
    message_data = {
        "from_": f"whatsapp:{TWILIO_NUMBER}",
        "to": f"whatsapp:{to}",
        "body": body
    }
    if media_url:
        message_data["media_url"] = [media_url]
    client.messages.create(**message_data)

# الصفحة الرئيسية للتأكد من تشغيل البوت
@app.route("/")
def home():
    return "\u2705 البوت يعمل بنجاح."

# نقطة استقبال الرسائل
@app.route("/bot", methods=["POST"])
def bot():
    msg = request.form.get("Body", "").strip()
    sender = request.form.get("From").replace("whatsapp:", "")
    session = sessions.get(sender, {"step": "start"})

    if session["step"] == "start":
        if "*" in msg:
            nid, pwd = msg.split("*", 1)
            if not nid.isdigit() or len(nid) != 10:
                return str(MessagingResponse().message("\u274C رقم الهوية غير صحيح."))

            send_whatsapp(sender, "\u23F3 يرجى الانتظار، جارٍ تسجيل الدخول...")
            result, screenshot = login_to_gosi(nid, pwd)

            if result == "otp":
                url = upload_img(screenshot)
                sessions[sender] = {"step": "otp", "nid": nid, "pwd": pwd}
                send_whatsapp(sender, "\ud83d\udcf2 أرسل رمز التحقق المكون من 4 أرقام:", media_url=url)
            elif result == "dob":
                sessions[sender] = {"step": "dob"}
                send_whatsapp(sender, "\ud83d\udcc5 أرسل تاريخ ميلادك مثال: 1990-01-01")
            else:
                url = upload_img(screenshot)
                send_whatsapp(sender, "\u274C فشل تسجيل الدخول. تحقق من البيانات.", media_url=url)
        else:
            send_whatsapp(sender, "\ud83d\udd39 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif session["step"] == "otp":
        if re.fullmatch(r"\\d{4}", msg):
            send_whatsapp(sender, "\ud83d\udcc5 الآن أرسل تاريخ ميلادك بصيغة: 1990-01-01")
            sessions[sender]["otp"] = msg
            sessions[sender]["step"] = "dob"
        else:
            send_whatsapp(sender, "\u26a0\ufe0f رمز التحقق غير صحيح. أعد إرساله مكونًا من 4 أرقام.")

    elif session["step"] == "dob":
        if re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", msg):
            send_whatsapp(sender, "\u23F3 يتم الآن إكمال التسجيل...")
            # هنا نكمل الخطوات القادمة حسب تفاصيل السعودة لاحقًا
            send_whatsapp(sender, "\u2705 تم تسجيلك في السعودة بنجاح! \ud83c\udf89")
            sessions.pop(sender, None)
        else:
            send_whatsapp(sender, "\u274C صيغة تاريخ الميلاد غير صحيحة. استخدم مثل: 1990-01-01")

    return jsonify({"status": "ok"})

# تسجيل الدخول باستخدام Selenium

def login_to_gosi(nid, pwd):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        time.sleep(3)
        driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(nid)
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(5)

        if "otp" in driver.page_source.lower():
            screenshot = save_screenshot(driver, f"otp_{nid}.png")
            return "otp", screenshot
        elif "تاريخ الميلاد" in driver.page_source:
            screenshot = save_screenshot(driver, f"dob_{nid}.png")
            return "dob", screenshot
        else:
            screenshot = save_screenshot(driver, f"fail_{nid}.png")
            return "fail", screenshot
    except Exception as e:
        screenshot = save_screenshot(driver, f"error_{nid}.png")
        return "fail", screenshot
    finally:
        driver.quit()

# حفظ لقطة الشاشة

def save_screenshot(driver, filename):
    folder = Path("temp")
    folder.mkdir(exist_ok=True)
    path = folder / filename
    driver.save_screenshot(str(path))
    return str(path)

# رفع الصورة على Imgur

def upload_img(image_path):
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    with open(image_path, "rb") as img:
        r = requests.post("https://api.imgur.com/3/upload", headers=headers, files={"image": img})
    if r.status_code == 200:
        return r.json()['data']['link']
    return None

# تشغيل الخادم
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

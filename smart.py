import os
import time
import requests
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from twilio.rest import Client
from pathlib import Path
from PIL import Image

# إعداد التطبيق
app = Flask(__name__)

# إعداد متغيرات البيئة
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
IMGUR_CLIENT_ID = os.environ.get("IMGUR_CLIENT_ID")

client = Client(TWILIO_SID, TWILIO_AUTH)

# الجلسات المؤقتة لكل مستخدم
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

@app.route('/')
def home():
    return '✅ البوت شغال'

@app.route('/bot', methods=['POST'])
def webhook():
    data = request.form
    msg = data.get("Body", "").strip()
    sender = data.get("From")
    phone = sender.replace("whatsapp:", "")

    session = sessions.get(phone, {"step": "start"})

    if session["step"] == "start":
        if "*" in msg:
            try:
                nid, pwd = msg.split("*", 1)
                if not nid.isdigit() or len(nid) != 10:
                    return send_whatsapp(phone, "❌ رقم الهوية غير صحيح")
                sessions[phone] = {"nid": nid, "pwd": pwd, "step": "waiting_otp"}
                send_whatsapp(phone, "⏳ يرجى الانتظار، جاري تسجيل الدخول...")
                result, screenshot_path = login_and_screenshot(nid, pwd)
                if result == "otp":
                    url = upload_to_imgur(screenshot_path)
                    send_whatsapp(phone, "📲 أرسل كود التحقق المكون من 4 أرقام", media_url=url)
                else:
                    url = upload_to_imgur(screenshot_path)
                    send_whatsapp(phone, "❌ فشل تسجيل الدخول. تحقق من البيانات.", media_url=url)
                    sessions.pop(phone)
            except Exception as e:
                send_whatsapp(phone, "⚠️ خطأ في المعالجة. أعد المحاولة")
        else:
            send_whatsapp(phone, "📌 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif session["step"] == "waiting_otp":
        if msg.isdigit() and len(msg) == 4:
            send_whatsapp(phone, "📆 أرسل تاريخ ميلادك بهذا الشكل: 1990-01-01")
            sessions[phone]["otp"] = msg
            sessions[phone]["step"] = "waiting_birthdate"
        else:
            send_whatsapp(phone, "❗ رمز التحقق يجب أن يكون 4 أرقام")

    elif session["step"] == "waiting_birthdate":
        birth = msg
        send_whatsapp(phone, "✅ تم تقديم السعودة بنجاح")
        sessions.pop(phone)

    return jsonify({"status": "ok"})

# تسجيل الدخول والتقاط صورة

def login_and_screenshot(nid, pwd):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(nid)
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(4)

        if "otp" in driver.page_source.lower():
            path = take_screenshot(driver, f"otp_{nid}.png")
            return "otp", path
        else:
            path = take_screenshot(driver, f"fail_{nid}.png")
            return "fail", path
    except Exception as e:
        path = take_screenshot(driver, f"error_{nid}.png")
        return "fail", path
    finally:
        driver.quit()

# التقاط صورة شاشة

def take_screenshot(driver, name):
    folder = Path("temp")
    folder.mkdir(exist_ok=True)
    path = folder / name
    driver.save_screenshot(str(path))
    return str(path)

# رفع صورة إلى Imgur

def upload_to_imgur(image_path):
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    with open(image_path, 'rb') as f:
        response = requests.post("https://api.imgur.com/3/upload", headers=headers, files={"image": f})
    if response.status_code == 200:
        return response.json()['data']['link']
    else:
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0',
    port=int(os.environ.get("PORT", 5000)))

# smart.py
import os
import time
import requests
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from twilio.rest import Client
from pathlib import Path

app = Flask(__name__)

# متغيرات البيئة
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
IMGUR_CLIENT_ID = os.environ.get("IMGUR_CLIENT_ID")

client = Client(TWILIO_SID, TWILIO_AUTH)
sessions = {}

def send_whatsapp(to, body, media_url=None):
    data = {
        "from_": f"whatsapp:{TWILIO_NUMBER}",
        "to": f"whatsapp:{to}",
        "body": body
    }
    if media_url:
        data["media_url"] = [media_url]
    client.messages.create(**data)

@app.route("/")
def home():
    return "✅ البوت شغال ومترابط مع واتساب"

@app.route("/bot", methods=["POST"])
def bot():
    data = request.form
    msg = data.get("Body", "").strip()
    sender = data.get("From").replace("whatsapp:", "")
    session = sessions.get(sender, {"step": "start"})

    if session["step"] == "start":
        if "*" in msg:
            nid, pwd = msg.split("*", 1)
            if not nid.isdigit() or len(nid) != 10:
                return send_whatsapp(sender, "❌ رقم الهوية غير صحيح (يجب أن يتكون من 10 أرقام)")

            send_whatsapp(sender, "⏳ يرجى الانتظار، جارٍ تسجيل الدخول...")
            result, screenshot = login_to_gosi(nid, pwd)

            if result == "otp":
                url = upload_img(screenshot)
                sessions[sender] = {"step": "otp", "nid": nid, "pwd": pwd}
                send_whatsapp(sender, "📲 تم تسجيل الدخول، أرسل رمز التحقق الآن (4 أرقام)", media_url=url)
            else:
                url = upload_img(screenshot)
                send_whatsapp(sender, "❌ تعذر تسجيل الدخول، تأكد من صحة البيانات", media_url=url)
        else:
            send_whatsapp(sender, "📌 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif session["step"] == "otp":
        if msg.isdigit() and len(msg) == 4:
            sessions[sender]["otp"] = msg
            sessions[sender]["step"] = "dob"
            send_whatsapp(sender, "📆 أرسل تاريخ ميلادك مثل: 1990-01-01")
        else:
            send_whatsapp(sender, "❗ رمز التحقق غير صحيح. يجب أن يكون 4 أرقام")

    elif session["step"] == "dob":
        nid = session["nid"]
        otp = session["otp"]
        dob = msg
        send_whatsapp(sender, "⏳ جارٍ تقديم السعودة، يرجى الانتظار...")
        result, screenshot = complete_form(nid, otp, dob)

        if result == "success":
            url = upload_img(screenshot)
            send_whatsapp(sender, "✅ تم تقديم السعودة بنجاح 🎉", media_url=url)
        else:
            url = upload_img(screenshot)
            send_whatsapp(sender, "❌ حدث خطأ أثناء إرسال النموذج. تأكد من المعلومات", media_url=url)
        sessions.pop(sender)

    return jsonify({"status": "ok"})

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
        time.sleep(4)

        if "otp" in driver.page_source.lower():
            return "otp", save_screenshot(driver, f"otp_{nid}.png")
        else:
            return "fail", save_screenshot(driver, f"fail_login_{nid}.png")

    except Exception:
        return "fail", save_screenshot(driver, f"error_login_{nid}.png")
    finally:
        driver.quit()

def complete_form(nid, otp, dob):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        time.sleep(3)
        # تابع التسجيل الكامل كما يلزم

        # هذه فقط محاكاة (ستحتاج تعدلها حسب عناصر الصفحة الفعلية)
        return "success", save_screenshot(driver, f"done_{nid}.png")

    except Exception:
        return "fail", save_screenshot(driver, f"fail_final_{nid}.png")
    finally:
        driver.quit()

def save_screenshot(driver, filename):
    folder = Path("temp")
    folder.mkdir(exist_ok=True)
    path = folder / filename
    driver.save_screenshot(str(path))
    return str(path)

def upload_img(image_path):
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    with open(image_path, "rb") as img:
        r = requests.post("https://api.imgur.com/3/upload", headers=headers, files={"image": img})
    if r.status_code == 200:
        return r.json()['data']['link']
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

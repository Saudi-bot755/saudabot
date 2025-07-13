from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.common.by import By
import json, time, os
from datetime import datetime

app = Flask(__name__)

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    user_id = data["id"]
    password = data["password"]
    sender = data["sender"]

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.gosi.gov.sa/")

        # مثال: تنفيذ تسجيل الدخول
        # ملاحظة: يجب تعديل عناصر ID بناءً على الموقع الحقيقي
        driver.find_element(By.ID, "id_field").send_keys(user_id)
        driver.find_element(By.ID, "pass_field").send_keys(password)
        driver.find_element(By.ID, "login_btn").click()
        time.sleep(3)

        if "خطأ" in driver.page_source or "غير صحيحة" in driver.page_source:
            screenshot_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = f"screenshots/{screenshot_name}"
            os.makedirs("screenshots", exist_ok=True)
            driver.save_screenshot(path)
            log_status = "فشل"
            send_whatsapp(sender, f"❌ فشل الدخول. أرفقنا لك صورة من الموقع.", path)
        else:
            log_status = "نجاح"
            send_whatsapp(sender, f"✅ تم تنفيذ السعودة بنجاح للمستخدم {user_id}.")

        driver.quit()
    except Exception as e:
        log_status = "فشل"
        send_whatsapp(sender, f"❌ حدث خطأ غير متوقع: {str(e)}")

    os.makedirs("logs", exist_ok=True)
    with open("logs/logs.json", "a") as f:
        json.dump({"timestamp": str(datetime.now()), "id": user_id, "status": log_status}, f)
        f.write("\n")

    return {"status": "ok"}

def send_whatsapp(to, message, media=None):
    import requests
    url = "https://api.twilio.com/2010-04-01/Accounts/YOUR_SID/Messages.json"
    data = {
        "To": to,
        "From": "whatsapp:+14155238886",
        "Body": message
    }
    files = {"MediaUrl": open(media, "rb")} if media else None
    auth = ("YOUR_SID", "YOUR_AUTH_TOKEN")
    requests.post(url, data=data, auth=auth)
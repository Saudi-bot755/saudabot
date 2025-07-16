import os
import tempfile
import time
import requests
from flask import Flask, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = Flask(__name__)

# بيانات Twilio من متغيرات البيئة
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
USER_NUMBER = os.getenv("USER_NUMBER")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_whatsapp_message(body):
    twilio_client.messages.create(
        from_=TWILIO_NUMBER,
        to=USER_NUMBER,
        body=body
    )

def send_whatsapp_image(image_url, caption=""):
    twilio_client.messages.create(
        from_=TWILIO_NUMBER,
        to=USER_NUMBER,
        body=caption,
        media_url=[image_url]
    )

def upload_image_to_imgbb(image_path):
    with open(image_path, 'rb') as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY}
        files = {"image": file}
        response = requests.post(url, data=payload, files=files)
        if response.status_code == 200:
            return response.json()['data']['url']
        else:
            return None

def capture_screenshot(driver):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    driver.save_screenshot(tmp_file.name)
    return tmp_file.name

def perform_registration(national_id, password):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.gosi.gov.sa/")
        time.sleep(3)
        # مثال: البحث عن المدخلات وتعبئة البيانات
        driver.find_element(By.ID, "id_number").send_keys(national_id)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login_button").click()
        time.sleep(5)

        if "الصفحة الرئيسية" in driver.page_source:
            screenshot_path = capture_screenshot(driver)
            return True, screenshot_path
        else:
            screenshot_path = capture_screenshot(driver)
            return False, screenshot_path
    except Exception as e:
        screenshot_path = capture_screenshot(driver)
        return False, screenshot_path
    finally:
        driver.quit()

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    session = request.values.get("WaId")

    if incoming_msg.lower().startswith("سعوده"):
        send_whatsapp_message("✅ يرجى إرسال رقم الهوية متبوعًا بكلمة المرور على الشكل التالي:\nرقم_الهوية*كلمة_المرور")
    elif "*" in incoming_msg:
        try:
            national_id, password = incoming_msg.split("*")
            send_whatsapp_message("⏳ يرجى الانتظار، جارٍ التسجيل...")
            success, screenshot_path = perform_registration(national_id, password)
            image_url = upload_image_to_imgbb(screenshot_path)
            os.remove(screenshot_path)
            if image_url:
                if success:
                    send_whatsapp_image(image_url, "✅ تم التسجيل بنجاح")
                else:
                    send_whatsapp_image(image_url, "❌ حدث خطأ أثناء محاولة التسجيل")
            else:
                send_whatsapp_message("⚠️ تعذر رفع الصورة، لكن العملية تمت")
        except Exception as e:
            send_whatsapp_message("⚠️ تنسيق غير صحيح. استخدم الشكل: رقم_الهوية*كلمة_المرور")
    else:
        send_whatsapp_message("👋 مرحبًا، أرسل كلمة \"سعوده\" للبدء")

    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

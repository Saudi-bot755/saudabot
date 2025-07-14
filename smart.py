from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os, time, json, datetime
from twilio.rest import Client
from PIL import Image
import pytesseract
from convertdate import islamic, gregorian
import re

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ البوت شغال تمام'

@app.route('/bot', methods=['POST'])
def bot_webhook():
    data = request.json
    print("📩 رسالة جديدة:", data)
    return jsonify({"msg": "تم استلام الرسالة ✅"})

@app.route('/saudabot-login', methods=['POST'])
def saudabot_login():
    data = request.get_json()
    national_id = data.get("id")
    password = data.get("password")
    code = data.get("code")
    birth_date = data.get("birth_date")
    sender = data.get("sender")

    # تحويل التاريخ إذا كان ميلادي
    if re.search(r'\d{4}-\d{2}-\d{2}', birth_date):
        try:
            y, m, d = map(int, birth_date.split('-'))
            hijri = islamic.from_gregorian(y, m, d)
            birth_date = f"{hijri[2]:02d}/{hijri[1]:02d}/{hijri[0]}"
        except:
            birth_date = birth_date  # يبقى كما هو إذا فشل التحويل

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[contains(text(), 'أعمال')]").click()
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(national_id)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(3)
        driver.find_element(By.ID, "otp").send_keys(code)
        driver.find_element(By.ID, "verify-button").click()
        time.sleep(5)

        # 👨‍💼 تنفيذ السعودة - إضافة مشترك جديد
        driver.find_element(By.LINK_TEXT, "إدارة الاشتراكات").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "إضافة مشترك").click()
        time.sleep(2)
        driver.find_element(By.ID, "nationalId").send_keys(national_id)
        driver.find_element(By.ID, "birthDateHijri").send_keys(birth_date)
        driver.find_element(By.ID, "occupation").send_keys("محاسب")
        driver.find_element(By.ID, "salary").send_keys("4000")
        driver.find_element(By.ID, "submit-button").click()
        time.sleep(5)

        img_path = f"screenshots/{national_id}.png"
        driver.save_screenshot(img_path)
        send_whatsapp(sender, f"✅ تم تسجيل سعودي جديد\nالمهنة: محاسب\nالراتب: 4000\n📅 تاريخ الميلاد: {birth_date}")
        send_whatsapp(sender, "📸 صورة الشاشة:", file_path=img_path)
        return jsonify({"status": "done"}), 200

    except Exception as e:
        img_path = f"screenshots/error_{national_id}.png"
        driver.save_screenshot(img_path)
        error_text = extract_text(img_path)
        send_whatsapp(sender, f"❌ فشل التسجيل:\n{error_text}")
        send_whatsapp(sender, "📸 صورة الخطأ:", file_path=img_path)
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

def extract_text(img_path):
    try:
        return pytesseract.image_to_string(Image.open(img_path), lang='ara+eng').strip()
    except:
        return "تعذر قراءة الخطأ من الصورة"

def send_whatsapp(to, body, file_path=None):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    client = Client(sid, token)

    data = {"body": body, "from_": from_number, "to": to}
    if file_path:
        url = f"https://your-server.com/screenshots/{os.path.basename(file_path)}"
        data["media_url"] = [url]

    client.messages.create(**data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

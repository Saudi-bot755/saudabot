from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os, time, json, datetime, re
from twilio.rest import Client
import pytesseract
from PIL import Image
from pathlib import Path

app = Flask(__name__)
TEMP_STORAGE = {}

@app.route('/')
def home():
    return '✅ البوت شغال بنجاح'

@app.route('/bot', methods=['POST'])
def bot_webhook():
    data = request.json
    msg = data.get("body", "").strip()
    sender = data.get("from")

    # إذا كان يحتوي على فاصلة (هوية + كلمة مرور)
    if "," in msg:
        parts = [x.strip() for x in msg.split(",")]
        if len(parts) != 2:
            return send_whatsapp(sender, "❌ تأكد من كتابة الهوية وكلمة المرور بهذا الشكل:\n1234567890, MyPass123")

        national_id, password = parts
        if not national_id.isdigit() or len(national_id) != 10:
            return send_whatsapp(sender, "❌ رقم الهوية غير صحيح. يجب أن يكون 10 أرقام.")

        if not validate_password(password):
            return send_whatsapp(sender, "❌ كلمة المرور يجب أن تحتوي على حرف كبير وحرف صغير ورقم.")

        TEMP_STORAGE[sender] = {"id": national_id, "password": password}
        send_whatsapp(sender, "🔐 جارٍ التسجيل... أرسل كود التحقق المكوّن من 4 أرقام")
        return jsonify({"status": "waiting_code"})

    # إذا كان كود تحقق
    elif msg.isdigit() and len(msg) == 4:
        if sender not in TEMP_STORAGE:
            return send_whatsapp(sender, "⚠️ أرسل الهوية وكلمة المرور أولاً قبل كود التحقق.")

        user_data = TEMP_STORAGE[sender]
        code_file = f"codes/{user_data['id']}.txt"
        with open(code_file, "w") as f:
            f.write(msg)

        send_whatsapp(sender, "✅ تم استلام الكود... جاري تنفيذ السعودة")
        start_saudah(user_data["id"], user_data["password"], sender)
        return jsonify({"status": "processing"})

    # أي رسالة أخرى
    else:
        return send_whatsapp(sender, "✉️ أرسل الهوية وكلمة المرور بهذا الشكل:\n1234567890, MyPass123")

# تنفيذ التسجيل في التأمينات
def start_saudah(national_id, password, sender):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
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

        code = wait_for_code(national_id)
        driver.find_element(By.ID, "otp").send_keys(code)
        driver.find_element(By.ID, "verify-button").click()
        time.sleep(3)

        ### 👇👇👇 تنفيذ السعودة 👇👇👇
        driver.get("https://www.gosi.gov.sa/GOSIOnline/Business/NewSubscriber")
        time.sleep(2)
        driver.find_element(By.ID, "jobTitle").send_keys("محاسب")
        driver.find_element(By.ID, "salary").send_keys("4000")
        driver.find_element(By.ID, "add-subscriber-btn").click()
        time.sleep(3)

        img_path = f"screenshots/{national_id}.png"
        driver.save_screenshot(img_path)
        send_whatsapp(sender, "✅ تم تنفيذ السعودة بنجاح: محاسب براتب 4000 ريال")
        send_whatsapp(sender, "📸 صورة الشاشة:", file_path=img_path)
        log_action(national_id, "✅ تم تنفيذ السعودة")

    except Exception as e:
        img_path = f"screenshots/error_{national_id}.png"
        driver.save_screenshot(img_path)
        error_text = extract_text(img_path)
        send_whatsapp(sender, f"❌ فشل في التسجيل:\n{error_text}")
        send_whatsapp(sender, "📸 صورة المشكلة:", file_path=img_path)
        log_action(national_id, f"❌ فشل: {error_text}")

    finally:
        driver.quit()

def wait_for_code(id_number):
    for _ in range(60):
        try:
            with open(f"codes/{id_number}.txt", "r") as f:
                return f.read().strip()
        except:
            time.sleep(3)
    return ""

def send_whatsapp(to, body, file_path=None):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    client = Client(sid, token)
    data = {"body": body, "from_": from_number, "to": to}
    if file_path:
        data["media_url"] = [f"https://your-server.com/screenshots/{Path(file_path).name}"]
    client.messages.create(**data)

def extract_text(img_path):
    try:
        return pytesseract.image_to_string(Image.open(img_path), lang='eng+ara').strip()
    except:
        return "تعذر قراءة الخطأ من الصورة"

def log_action(national_id, msg):
    log = {"id": national_id, "msg": msg, "time": datetime.datetime.now().isoformat()}
    with open("logs.json", "a", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False)
        f.write(",\n")

def validate_password(password):
    return (
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

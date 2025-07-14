from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os, time, json, datetime
from twilio.rest import Client
import pytesseract
from PIL import Image

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
    sender = data.get("sender")

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

        send_whatsapp(sender, "📲 أرسل كود التحقق من التأمينات خلال دقيقة")

        code = wait_for_code(national_id)
        driver.find_element(By.ID, "otp").send_keys(code)
        driver.find_element(By.ID, "verify-button").click()
        time.sleep(3)

        img_path = f"screenshots/{national_id}.png"
        driver.save_screenshot(img_path)

        send_whatsapp(sender, "✅ تم تسجيل سعودي جديد: المهنة محاسب، الراتب 4000 ريال")
        send_whatsapp(sender, "📸 صورة الشاشة:", file_path=img_path)
        log_action(national_id, "تمت العملية بنجاح")
        return jsonify({"status": "done"}), 200

    except Exception as e:
        img_path = f"screenshots/error_{national_id}.png"
        driver.save_screenshot(img_path)
        text = extract_text(img_path)
        send_whatsapp(sender, f"❌ فشل التسجيل:
{text}")
        send_whatsapp(sender, "📸 صورة المشكلة:", file_path=img_path)
        log_action(national_id, f"خطأ: {text}")
        return jsonify({"error": str(e)}), 500

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
        text = pytesseract.image_to_string(Image.open(img_path), lang='eng+ara')
        return text.strip()
    except:
        return "تعذر قراءة الخطأ من الصورة"

def log_action(national_id, msg):
    log = {"id": national_id, "msg": msg, "time": datetime.datetime.now().isoformat()}
    with open("logs.json", "a", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False)
        f.write(",
")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import requests
import os
from twilio.rest import Client
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return 'البوت شغال ✅'

@app.route('/bot', methods=['POST'])
def bot_webhook():
    data = request.json
    print("📩 استلمنا رسالة:", data)
    return 'تم ✅'
@app.route("/saudabot-login", methods=["POST"])
def saudabot_login():
    data = request.get_json()
    national_id = data.get("id")
    password = data.get("password")
    sender = data.get("sender")  # رقم واتساب

    # إعداد متصفح Chrome بدون واجهة
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)

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

        send_whatsapp(sender, "📲 أرسل الآن كود التحقق الذي وصلك من التأمينات:")

        code = wait_for_code(national_id)

        driver.find_element(By.ID, "otp").send_keys(code)
        driver.find_element(By.ID, "verify-button").click()

        time.sleep(3)

        screenshot_path = f"screenshot_{national_id}.png"
        driver.save_screenshot(screenshot_path)

        send_whatsapp(sender, f"✅ تم تسجيل سعودي جديد:\nالمهنة: محاسب\nالراتب: 4000 ريال")
        send_whatsapp(sender, f"📸 هذه صورة الشاشة:", file_path=screenshot_path)

        return jsonify({"status": "done"}), 200

    except Exception as e:
        send_whatsapp(sender, f"❌ فشل التسجيل: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

def wait_for_code(id_number):
    for i in range(60):
        try:
            with open(f"codes/{id_number}.txt", "r") as f:
                return f.read().strip()
        except:
            time.sleep(3)
    return ""

def send_whatsapp(to, body, file_path=None):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH")
    from_number = "whatsapp:+14155238886"

    client = Client(account_sid, auth_token)

    message_data = {
        "body": body,
        "from_": from_number,
        "to": to
    }

    if file_path:
        message_data["media_url"] = [upload_temp_image(file_path)]

    client.messages.create(**message_data)

def upload_temp_image(file_path):
    return "https://your-server.com/screenshots/" + file_path

if __name__ == "__main__":
   port = int(os.environ.get("PORT", 
                             5000))
  app.run(host="0.0.0.0", port=port)

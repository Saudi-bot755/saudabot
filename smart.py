from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os, time, json
from twilio.rest import Client
from pathlib import Path
from PIL import Image
import openai

# تعيين مفتاح GPT من متغيرات البيئة
openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

# Twilio credentials
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
client = Client(TWILIO_SID, TWILIO_AUTH)

# إرسال رسالة واتساب
def send_whatsapp(to, body):
    client.messages.create(
        from_='whatsapp:+14155238886',  # رقم الساندبوكس الرسمي
        to='whatsapp:' + to,
        body=body
    )
    )

@app.route('/')
def home():
    return '✅ البوت شغال تمام'

@app.route('/bot', methods=['POST'])
def bot_webhook():
    data = request.form.to_dict()
    msg = data.get("Body", "").strip().lower()
    sender = data.get("From")

    if "سعوده" in msg:
        send_whatsapp(sender, "📝 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")
    elif "*" in msg:
        try:
            national_id, password = msg.split("*")
            if not national_id.isdigit() or len(national_id) != 10 or not national_id.startswith("1"):
                return send_whatsapp(sender, "❌ رقم الهوية غير صحيح. يجب أن يكون مكون من 10 أرقام ويبدأ بـ 1.")
            if len(password) < 8 or password.lower() == password:
                return send_whatsapp(sender, "❌ كلمة المرور يجب أن تحتوي على حرف كبير وحروف إنجليزية.")
            send_whatsapp(sender, "⏳ جاري تنفيذ السعودة.. الرجاء الانتظار")
            Path("codes").mkdir(exist_ok=True)
            with open(f"codes/{national_id}.txt", "w") as f:
                f.write("")  # Reset old code
            login_and_saudah(national_id, password, sender)
        except:
            send_whatsapp(sender, "❌ التنسيق غير صحيح. أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")
    elif msg.isdigit() and len(msg) == 4:
        for file in Path("codes").glob("*.txt"):
            with open(file, "w") as f:
                f.write(msg)
        send_whatsapp(sender, "📆 أرسل تاريخ ميلادك بهذا الشكل: 1999-01-30")
    elif "-" in msg:
        try:
            national_id = Path("codes").glob("*.txt").__next__().stem
            birthday = msg.strip()
            complete_saudah(national_id, birthday, sender)
        except:
            send_whatsapp(sender, "❌ حدث خطأ. تأكد من إرسال تاريخ الميلاد بشكل صحيح")
    else:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": msg}]
            )
            reply = response.choices[0].message.content.strip()
            send_whatsapp(sender, reply)
        except:
            send_whatsapp(sender, "⚠️ حدث خطأ في الاتصال بالذكاء الاصطناعي")
    return jsonify({"status": "ok"})

def wait_for_code(national_id, timeout=60):
    file_path = f"codes/{national_id}.txt"
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(file_path):
            with open(file_path) as f:
                code = f.read().strip()
                if code:
                    return code
        time.sleep(2)
    return None

def login_and_saudah(national_id, password, sender):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
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

        send_whatsapp(sender, "📲 أرسل كود التحقق الآن (أربعة أرقام)")
        code = wait_for_code(national_id)
        if not code:
            send_whatsapp(sender, "⌛ انتهى الوقت ولم يتم استلام كود التحقق")
            driver.quit()
            return

        driver.find_element(By.ID, "otp-input").send_keys(code)
        driver.find_element(By.ID, "confirm-otp").click()
        time.sleep(5)
        send_whatsapp(sender, "📆 أرسل تاريخ ميلادك بهذا الشكل: 1999-01-30")

    except Exception as e:
        screenshot = f"error_{national_id}.png"
        driver.save_screenshot(screenshot)
        send_whatsapp(sender, f"❌ حدث خطأ أثناء الدخول: {str(e)}")
        driver.quit()

def complete_saudah(national_id, birthday, sender):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        time.sleep(5)
        driver.find_element(By.ID, "job-title").send_keys("محاسب")
        driver.find_element(By.ID, "salary").send_keys("4000")
        driver.find_element(By.ID, "birthday").send_keys(birthday)
        driver.find_element(By.ID, "submit").click()
        send_whatsapp(sender, "✅ تم تقديم السعودة بنجاح")
        driver.quit()
    except Exception as e:
        screenshot = f"final_error_{national_id}.png"
        driver.save_screenshot(screenshot)
        send_whatsapp(sender, f"❌ حدث خطأ أثناء إكمال النموذج: {str(e)}")
        driver.quit()

# تشغيل التطبيق
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)

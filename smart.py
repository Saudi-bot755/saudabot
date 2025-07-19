import os
import time
import base64
import datetime
from flask import Flask, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests

# Flask setup
app = Flask(__name__)

# Load environment variables
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
user_number = os.environ['USER_PHONE_NUMBER']
imgbb_api_key = os.environ['IMGBB_API_KEY']

client = Client(account_sid, auth_token)

# Session state
session = {
    'step': None,
    'nid': None,
    'pwd': None,
    'otp': None,
    'employee': {},
    'confirming': False,
    'screenshot': None
}

# Helper to send WhatsApp

def send_whatsapp(to, body, media_url=None):
    try:
        data = {'from_': f'whatsapp:{twilio_number}', 'to': f'whatsapp:{to}', 'body': body}
        if media_url:
            data['media_url'] = [media_url]
        client.messages.create(**data)
    except Exception as e:
        print(f"Twilio error: {e}")

# Upload screenshot

def upload_screenshot(path):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        res = requests.post("https://api.imgbb.com/1/upload", data={"key": imgbb_api_key, "image": encoded})
        return res.json()['data']['url'] if res.status_code == 200 else None
    except Exception as e:
        print(f"ImgBB error: {e}")
        return None

# Execute full registration

def register_employee():
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

        driver.get("https://www.gosi.gov.sa")
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "دخول أعمال").click()
        time.sleep(2)

        driver.find_element(By.ID, "username").send_keys(session['nid'])
        driver.find_element(By.ID, "password").send_keys(session['pwd'])
        driver.find_element(By.ID, "loginButton").click()
        time.sleep(3)

        # Assume OTP or DOB is handled (simulate pass)
        # Continue to form

        # Navigate to "تسجيل موظف سعودي"
        driver.find_element(By.LINK_TEXT, "خدمات المشتركين").click()
        time.sleep(1)
        driver.find_element(By.LINK_TEXT, "تسجيل مشترك سعودي").click()
        time.sleep(3)

        # Fill form
        driver.find_element(By.XPATH, "//*[@id='nationalId']").send_keys(session['employee']['id'])
        driver.find_element(By.XPATH, "//*[@id='birthDate']").send_keys(session['employee']['dob'])
        driver.find_element(By.XPATH, "//*[@id='nationality']").send_keys(session['employee']['nationality'])
        driver.find_element(By.XPATH, "//*[@id='employmentDate']").send_keys(session['employee']['start'])
        driver.find_element(By.XPATH, "//*[@id='contractType']").send_keys(session['employee']['contract'])

        if session['employee'].get('duration'):
            driver.find_element(By.XPATH, "//*[@id='contractDuration']").send_keys(session['employee']['duration'])

        driver.find_element(By.XPATH, "//*[@id='jobTitle']").send_keys(session['employee']['job'])
        driver.find_element(By.XPATH, "//*[@id='basicSalary']").send_keys(session['employee']['salary'])

        if session['employee'].get('allowance'):
            driver.find_element(By.XPATH, "//*[@id='allowances']").send_keys(session['employee']['allowance'])

        driver.find_element(By.XPATH, "//*[@id='subscriptionSalary']").send_keys(session['employee']['subscribe'])
        driver.find_element(By.XPATH, "//*[@id='registrationReason']").send_keys(session['employee']['reason'])

        if session['employee'].get('branch'):
            driver.find_element(By.XPATH, "//*[@id='branch']").send_keys(session['employee']['branch'])

        if session['employee'].get('notes'):
            driver.find_element(By.XPATH, "//*[@id='notes']").send_keys(session['employee']['notes'])

        driver.save_screenshot("done.png")
        img = upload_screenshot("done.png")

        driver.find_element(By.XPATH, "//*[@id='submitBtn']").click()
        time.sleep(2)
        driver.quit()
        return True, img
    except Exception as e:
        print(f"Register error: {e}")
        driver.save_screenshot("error.png")
        return False, upload_screenshot("error.png")

@app.route("/bot", methods=['POST'])
def bot():
    msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace('whatsapp:', '')

    if msg.lower() == 'سعوده':
        session.update({'step': 'login'})
        send_whatsapp(sender, "🔐 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")
        return ('', 200)

    if session['step'] == 'login' and '*' in msg:
        nid, pwd = msg.split("*")
        session.update({'nid': nid, 'pwd': pwd, 'step': 'employee_id'})
        send_whatsapp(sender, "🆔 أرسل رقم هوية الموظف")
        return ('', 200)

    steps = [
        ('employee_id', '🎂 أرسل تاريخ الميلاد (مثال: 1410/01/01)', 'dob'),
        ('dob', '🌍 الجنسية (اكتب: سعودي)', 'nationality'),
        ('nationality', '📆 تاريخ مباشرة العمل (مثال: 1446/01/01)', 'start'),
        ('start', '📄 نوع العقد (دائم – مؤقت – تدريب)', 'contract'),
        ('contract', '⏱️ مدة العقد (اكتب "تخطي" إذا لا يوجد)', 'duration'),
        ('duration', '🧾 المهنة (مثال: محاسب)', 'job'),
        ('job', '💰 الراتب الأساسي (مثال: 4000)', 'salary'),
        ('salary', '🏠 البدلات (اكتب "تخطي" إذا لا يوجد)', 'allowance'),
        ('allowance', '📊 الأجر الخاضع للاشتراك (الراتب + البدلات)', 'subscribe'),
        ('subscribe', '📌 سبب التسجيل (التحاق جديد – نقل...)', 'reason'),
        ('reason', '🏢 جهة العمل أو الفرع (أو اكتب "تخطي")', 'branch'),
        ('branch', '📝 ملاحظات إضافية (أو اكتب "تخطي")', 'notes'),
    ]

    for step, next_msg, field in steps:
        if session['step'] == step:
            if msg == 'تخطي':
                session['employee'][field] = None
            else:
                session['employee'][field] = msg
            next_step = steps[steps.index((step, next_msg, field)) + 1] if step != 'notes' else None
            session['step'] = next_step[0] if next_step else 'confirm'
            send_whatsapp(sender, next_step[1] if next_step else '📤 جاري رفع الطلب...')
            if not next_step:
                success, shot = register_employee()
                msg = '✅ تم التسجيل بنجاح!' if success else '❌ فشل التسجيل'
                send_whatsapp(sender, msg, media_url=shot)
            return ('', 200)

    return ('', 200)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

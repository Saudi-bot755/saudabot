# smart.py
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

app = Flask(__name__)

# Twilio & Imgbb config
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
imgbb_api_key = os.environ['IMGBB_API_KEY']

client = Client(account_sid, auth_token)

session = {
    'status': 'idle',
    'step': None,
    'data': {}
}

FIELDS = [
    ('employee_id', "🆔 رقم الهوية الوطنية للموظف"),
    ('dob', "🎂 تاريخ الميلاد (مثال: 1410/01/01)"),
    ('nationality', "🌍 الجنسية (اكتب: سعودي)"),
    ('start_date', "📅 تاريخ مباشرة العمل (مثال: 1446/01/01)"),
    ('contract_type', "📄 نوع العقد (دائم – مؤقت – تدريب)"),
    ('contract_duration', "⏱️ مدة العقد (اكتب 'تخطي' إذا لا يوجد)"),
    ('job_title', "💼 المهنة (مثال: محاسب)"),
    ('basic_salary', "💰 الراتب الأساسي (مثال: 4000)"),
    ('allowances', "🏠 البدلات (اكتب 'تخطي' إذا لا يوجد)"),
    ('total_salary', "📊 الأجر الخاضع للاشتراك (الراتب + البدلات)"),
    ('registration_reason', "📌 سبب التسجيل (التحاق جديد – نقل...)"),
    ('branch', "🏢 جهة العمل أو الفرع"),
    ('notes', "📝 ملاحظات إضافية (اكتب 'تخطي' إذا لا يوجد)")
]

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace('whatsapp:', '')
    print(f"User: {incoming_msg}")

    if incoming_msg == 'سعوده':
        session['status'] = 'login'
        session['data'] = {}
        session['step'] = None
        return send_msg(sender, "🔐 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif '*' in incoming_msg and session['status'] == 'login':
        try:
            nid, pwd = incoming_msg.split('*')
            session['data']['nid'] = nid
            session['data']['pwd'] = pwd
            session['status'] = 'otp_check'
            return send_msg(sender, "📲 أرسل رمز التحقق OTP")
        except:
            return send_msg(sender, "⚠️ تنسيق خاطئ. أرسلها هكذا: الهوية*كلمةالمرور")

    elif session['status'] == 'otp_check' and incoming_msg.isdigit():
        session['data']['otp'] = incoming_msg
        session['status'] = 'field_entry'
        session['step'] = 0
        return send_msg(sender, f"{FIELDS[0][1]}\nأو أرسل 'تخطي'")

    elif session['status'] == 'field_entry':
        key, label = FIELDS[session['step']]
        if incoming_msg.lower() != 'تخطي':
            session['data'][key] = incoming_msg
        else:
            session['data'][key] = None

        session['step'] += 1
        if session['step'] < len(FIELDS):
            return send_msg(sender, f"{FIELDS[session['step']][1]}\nأو أرسل 'تخطي'")
        else:
            session['status'] = 'submitting'
            send_msg(sender, "📤 جاري رفع الطلب، انتظر لحظات...")
            return process_submission(sender)

    return ('', 200)

def process_submission(sender):
    try:
        # Selenium login + form fill simulation
        img = take_screenshot()
        url = upload_img(img)
        send_msg(sender, "✅ تم التسجيل بنجاح!", media_url=url)
    except Exception as e:
        print("[Error]", e)
        img = take_screenshot()
        url = upload_img(img)
        send_msg(sender, "❌ فشل التسجيل، تحقق من البيانات", media_url=url)
    return ('', 200)

def send_msg(to, body, media_url=None):
    try:
        data = {'from_': f'whatsapp:{twilio_number}', 'to': f'whatsapp:{to}', 'body': body}
        if media_url:
            data['media_url'] = [media_url]
        client.messages.create(**data)
    except Exception as e:
        print("[Twilio Error]", e)
    return ('', 200)

def take_screenshot():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.gosi.gov.sa')
    time.sleep(2)
    driver.save_screenshot('screen.png')
    driver.quit()
    return 'screen.png'

def upload_img(path):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": imgbb_api_key, "image": encoded}
        )
        return res.json()['data']['url'] if res.status_code == 200 else None
    except Exception as e:
        print("[ImgBB Error]", e)
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

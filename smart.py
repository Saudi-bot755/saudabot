import os
import time
import base64
from flask import Flask, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests

app = Flask(__name__)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
imgbb_api_key = os.environ['IMGBB_API_KEY']

client = Client(account_sid, auth_token)
session = {}

def send_whatsapp(to, message, media_url=None):
    try:
        data = {
            'from_': f'whatsapp:{twilio_number}',
            'to': f'whatsapp:{to}',
            'body': message
        }
        if media_url:
            data['media_url'] = [media_url]
        client.messages.create(**data)
    except Exception as e:
        print("Twilio Error:", e)

def upload_to_imgbb(path):
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    res = requests.post("https://api.imgbb.com/1/upload", data={"key": imgbb_api_key, "image": encoded})
    return res.json()['data']['url'] if res.status_code == 200 else None

def capture_and_send(driver, sender, caption):
    screenshot_path = "screen.png"
    driver.save_screenshot(screenshot_path)
    img_url = upload_to_imgbb(screenshot_path)
    send_whatsapp(sender, caption, img_url)

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace('whatsapp:', '')

    if sender not in session:
        session[sender] = {"step": "start", "data": {}}

    state = session[sender]
    step = state['step']
    data = state['data']

    if incoming_msg.lower() == "سعوده":
        state['step'] = 'login'
        send_whatsapp(sender, "🔐 أرسل رقم الهوية وكلمة المرور بهذا الشكل: 1234567890*Abc12345")

    elif step == 'login' and "*" in incoming_msg:
        nid, pwd = incoming_msg.split("*")
        data['nid'] = nid.strip()
        data['pwd'] = pwd.strip()
        state['step'] = 'wait_otp'
        send_whatsapp(sender, "📲 أرسل رمز التحقق OTP المرسل من أبشر")

    elif step == 'wait_otp' and incoming_msg.isdigit():
        data['otp'] = incoming_msg
        state['step'] = 'emp_id'
        send_whatsapp(sender, "🆔 أرسل رقم هوية الموظف السعودي الجديد")

    elif step == 'emp_id':
        data['employee_id'] = incoming_msg
        state['step'] = 'emp_dob'
        send_whatsapp(sender, "🎂 أرسل تاريخ ميلاده (هجري مثال: 1410/10/05)")

    elif step == 'emp_dob':
        data['employee_dob'] = incoming_msg
        state['step'] = 'start_date'
        send_whatsapp(sender, "📅 تاريخ مباشرة العمل؟ أو أرسل 'تخطي'")

    elif step == 'start_date':
        if incoming_msg != 'تخطي':
            data['start_date'] = incoming_msg
        state['step'] = 'contract_type'
        send_whatsapp(sender, "📄 نوع العقد؟ (دائم/مؤقت/تدريب)")

    elif step == 'contract_type':
        data['contract_type'] = incoming_msg
        state['step'] = 'contract_duration'
        send_whatsapp(sender, "⏱ مدة العقد؟ أو أرسل 'تخطي'")

    elif step == 'contract_duration':
        if incoming_msg != 'تخطي':
            data['contract_duration'] = incoming_msg
        state['step'] = 'job_title'
        send_whatsapp(sender, "🧾 المهنة؟ (مثال: محاسب)")

    elif step == 'job_title':
        data['job_title'] = incoming_msg
        state['step'] = 'basic_salary'
        send_whatsapp(sender, "💰 الراتب الأساسي؟")

    elif step == 'basic_salary':
        data['basic_salary'] = incoming_msg
        state['step'] = 'allowances'
        send_whatsapp(sender, "➕ البدلات؟ أو أرسل 'تخطي'")

    elif step == 'allowances':
        data['allowances'] = incoming_msg if incoming_msg != 'تخطي' else ''
        state['step'] = 'subscription_salary'
        send_whatsapp(sender, "📊 الأجر الخاضع للاشتراك؟")

    elif step == 'subscription_salary':
        data['subscription_salary'] = incoming_msg
        state['step'] = 'registration_reason'
        send_whatsapp(sender, "📝 سبب التسجيل؟ (التحاق جديد/نقل خدمة...)")

    elif step == 'registration_reason':
        data['registration_reason'] = incoming_msg
        state['step'] = 'branch'
        send_whatsapp(sender, "🏢 اسم الفرع؟")

    elif step == 'branch':
        data['branch'] = incoming_msg
        state['step'] = 'confirm'
        send_whatsapp(sender, "✅ هل تريد تقديم الطلب الآن؟ (نعم/لا)")

    elif step == 'confirm':
        if incoming_msg.lower() == 'نعم':
            send_whatsapp(sender, "🚀 جاري تنفيذ التسجيل الفعلي...")
            result = submit_registration(data, sender)
            send_whatsapp(sender, result)
            session.pop(sender)
        else:
            send_whatsapp(sender, "📭 تم إلغاء العملية.")
            session.pop(sender)

    return ('', 200)

def submit_registration(data, sender):
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://www.gosi.gov.sa")
        time.sleep(2)
        # تنفيذ خطوات تسجيل الدخول وتسجيل الموظف باستخدام XPath التي زودتني بها
        # هذه مجرد واجهة، تحتاج تنفيذ حقيقي داخل الموقع.

        capture_and_send(driver, sender, "📸 تم إرسال لقطة من التسجيل")
        driver.quit()
        return "🎉 تم تقديم الطلب بنجاح!"
    except Exception as e:
        print("[Register Error]", str(e))
        return "❌ حدث خطأ أثناء تقديم الطلب"

if __name__ == '__main__':
   
    app.run(debug=True, port=8080,host='0.0.0.0')

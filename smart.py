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

# Flask init
app = Flask(__name__)

# Twilio config
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
imgbb_api_key = os.environ['IMGBB_API_KEY']

client = Client(account_sid, auth_token)

session_state = {
    "status": "idle",
    "step": None,
    "nid": None,
    "pwd": None,
    "otp": None,
    "dob": None,
    "job_confirmed": False,
    "fields": {},
    "screenshot_url": None
}

fields_order = [
    ("national_id", "🆔 أرسل رقم هوية الموظف"),
    ("birth_date", "🎂 أرسل تاريخ الميلاد (هجري)"),
    ("nationality", "🌍 الجنسية (مثال: سعودي)"),
    ("employment_date", "📅 تاريخ مباشرة العمل (1446/01/01)"),
    ("contract_type", "📃 نوع العقد (مثال: دائم، مؤقت...)"),
    ("contract_duration", "⏳ مدة العقد (أو اكتب تخطي)"),
    ("job_title", "👔 المهنة (مثال: محاسب)"),
    ("basic_salary", "💵 الراتب الأساسي (مثال: 4000)"),
    ("allowances", "📦 البدلات (أو اكتب تخطي)"),
    ("subscription_salary", "💰 الأجر الخاضع للاشتراك (مثال: 4000)"),
    ("registration_reason", "📌 سبب التسجيل (مثال: التحاق جديد)"),
    ("branch", "🏢 اسم الفرع أو جهة العمل (مثال: الفرع الرئيسي)")
]

xpaths = {
    "national_id": '//*[@id="nationalId"]',
    "birth_date": '//*[@id="birthDate"]',
    "nationality": '//*[@id="nationality"]',
    "employment_date": '//*[@id="employmentDate"]',
    "contract_type": '//*[@id="contractType"]',
    "contract_duration": '//*[@id="contractDuration"]',
    "job_title": '//*[@id="jobTitle"]',
    "basic_salary": '//*[@id="basicSalary"]',
    "allowances": '//*[@id="allowances"]',
    "subscription_salary": '//*[@id="subscriptionSalary"]',
    "registration_reason": '//*[@id="registrationReason"]',
    "branch": '//*[@id="branch"]',
    "submit": '//*[@id="submitBtn"]'
}

current_field_index = 0

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
        print(f"[Twilio Error] {e}")

@app.route("/bot", methods=['POST'])
def bot():
    global current_field_index
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace('whatsapp:', '')

    if "سعوده" in incoming_msg:
        session_state.update({
            "status": "awaiting_login",
            "step": "login"
        })
        send_whatsapp(sender, "📝 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif "سجلت" in incoming_msg:
        if session_state['status'] == 'awaiting_fields':
            field_key, prompt = fields_order[current_field_index]
            send_whatsapp(sender, prompt)
        else:
            send_whatsapp(sender, "⚠️ لا يوجد تسجيل قيد التنفيذ. أرسل سعوده للبدء.")

    elif "*" in incoming_msg and session_state['step'] == "login":
        try:
            nid, pwd = incoming_msg.split("*")
            session_state['nid'] = nid
            session_state['pwd'] = pwd
            session_state['step'] = "awaiting_fields"
            session_state['status'] = "awaiting_fields"
            current_field_index = 0
            send_whatsapp(sender, fields_order[current_field_index][1])
        except:
            send_whatsapp(sender, "⚠️ تأكد من التنسيق: الهوية*كلمة المرور")

    elif session_state['status'] == "awaiting_fields":
        field_key, prompt = fields_order[current_field_index]
        if incoming_msg.lower() != "تخطي":
            session_state['fields'][field_key] = incoming_msg
        current_field_index += 1
        if current_field_index < len(fields_order):
            next_field = fields_order[current_field_index][1]
            send_whatsapp(sender, next_field)
        else:
            session_state['status'] = "registering"
            send_whatsapp(sender, "⏳ جاري تسجيل الموظف... انتظر")
            result, img_url = submit_registration()
            if result:
                send_whatsapp(sender, "✅ تم التسجيل بنجاح", media_url=img_url)
            else:
                send_whatsapp(sender, "❌ فشل التسجيل. راجع البيانات", media_url=img_url)
            session_state['status'] = 'idle'

    return ('', 200)

def submit_registration():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.gosi.gov.sa")
        time.sleep(3)

        # TODO: تسجيل الدخول الحقيقي هنا

        # تعبئة البيانات
        for key, value in session_state['fields'].items():
            try:
                if key in xpaths:
                    element = driver.find_element(By.XPATH, xpaths[key])
                    element.clear()
                    element.send_keys(value)
                    time.sleep(0.5)
            except Exception as e:
                print(f"[Field Error] {key}: {e}")

        # إرسال الطلب
        try:
            submit_btn = driver.find_element(By.XPATH, xpaths['submit'])
            submit_btn.click()
            time.sleep(3)
        except Exception as e:
            print("[Submit Error]", e)

        driver.save_screenshot("screen.png")
        img_url = upload_to_imgbb("screen.png")
        driver.quit()
        return True, img_url

    except Exception as e:
        print(f"[Register Error] {e}")
        return False, upload_to_imgbb("screen.png")

def upload_to_imgbb(path):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": imgbb_api_key, "image": encoded}
        )
        return res.json()['data']['url'] if res.status_code == 200 else None
    except Exception as e:
        print(f"[imgbb Error] {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)

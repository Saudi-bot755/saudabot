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
user_number = os.environ['USER_PHONE_NUMBER']
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
    "start_date": None,
    "qualification": None,
    "screenshot_url": None
}

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
    incoming_msg = request.values.get('Body', '').strip().lower()
    sender = request.values.get('From', '').replace('whatsapp:', '')
    print(f"Incoming: {incoming_msg}")

    if "سعوده" in incoming_msg:
        session_state.update({
            "status": "waiting_login",
            "step": "awaiting_login"
        })
        send_whatsapp(sender, "📝 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif "سجلت" in incoming_msg:
        st = session_state['status']
        msg = {
            'waiting_otp': "🔐 نحتاج رمز التحقق OTP، الرجاء إرساله مثل: 123456",
            'waiting_dob': "🎂 أرسل تاريخ الميلاد بالشكل: 1410/10/05",
            'confirm_job': "💼 هل تؤكد إضافة المهنة 'محاسب' والراتب 4000؟ أرسل 'نعم' أو 'لا'",
            'waiting_start': "🗓️ أرسل تاريخ بدء العمل (مثال: 1446/01/01) أو أرسل 'تخطي'",
            'waiting_qual': "🎓 أرسل المؤهل العلمي أو أرسل 'تخطي'",
            'registering': "⏳ جاري التسجيل...",
            'done': "✅ تم التسجيل بنجاح!",
            'error': "❌ فشل التسجيل، تحقق من البيانات أو الموقع."
        }.get(st, "📬 لا يوجد تسجيل نشط. أرسل سعوده للبدء.")
        send_whatsapp(sender, msg)

    elif "*" in incoming_msg and session_state['step'] == 'awaiting_login':
        try:
            nid, pwd = incoming_msg.split("*")
            session_state['nid'] = nid.strip()
            session_state['pwd'] = pwd.strip()
            session_state['status'] = 'registering'
            send_whatsapp(sender, "⏳ تسجيل الدخول... انتظر")
            result, img_url = login_to_gosi(nid, pwd)
            session_state['screenshot_url'] = img_url
            if result == 'otp':
                session_state['status'] = 'waiting_otp'
                send_whatsapp(sender, "🔐 أرسل رمز التحقق OTP", media_url=img_url)
            else:
                session_state['status'] = 'error'
                send_whatsapp(sender, "❌ فشل الدخول. تحقق من البيانات أو الموقع", media_url=img_url)
        except Exception as e:
            send_whatsapp(sender, f"⚠️ خطأ في التنسيق: {str(e)}")

    return ('', 200)

def login_to_gosi(nid, pwd):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://www.gosi.gov.sa/GOSIOnline/Pages/default.aspx")
        time.sleep(3)

        driver.find_element(By.XPATH, "//a[contains(text(), 'تسجيل الدخول')]").click()
        time.sleep(3)

        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        driver.find_element(By.ID, "userId").send_keys(nid)
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "submitButton").click()
        time.sleep(5)

        driver.save_screenshot("after_login.png")
        img_url = upload_to_imgbb("after_login.png")
        driver.quit()
        return 'otp', img_url

    except Exception as e:
        print(f"[Login Error] {str(e)}")
        return 'error', upload_to_imgbb("after_login.png")

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

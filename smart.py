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
imgbb_api_key = os.environ['IMGBB_API_KEY']  # استخدم متغير البيئة الجديد

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
            'waiting_start': "📅 أرسل تاريخ بدء العمل (مثال: 1446/01/01) أو أرسل 'تخطي'",
            'waiting_qual': "🎓 أرسل المؤهل العلمي أو أرسل 'تخطي'",
            'registering': "⏳ جاري التسجيل...",
            'done': "✅ تم التسجيل بنجاح!",
            'error': "❌ فشل التسجيل، تحقق من البيانات أو الموقع."
        }.get(st, "📭 لا يوجد تسجيل نشط. أرسل سعوده للبدء.")
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
                send_whatsapp(sender, "🔐 أرسل رمز التحقق OTP")
            elif result == 'dob':
                session_state['status'] = 'waiting_dob'
                send_whatsapp(sender, "🎂 أرسل تاريخ الميلاد بالشكل: 1410/10/05")
            elif result == 'success':
                session_state['status'] = 'confirm_job'
                send_whatsapp(sender, "💼 هل تؤكد إضافة المهنة 'محاسب' والراتب 4000؟ أرسل 'نعم' أو 'لا'", media_url=img_url)
            else:
                session_state['status'] = 'error'
                send_whatsapp(sender, "❌ خطأ أثناء الدخول", media_url=img_url)
        except:
            send_whatsapp(sender, "⚠️ تأكد من تنسيق الرسالة: الهوية*كلمةالمرور")

    elif incoming_msg == 'نعم' and session_state['status'] == 'confirm_job':
        session_state['job_confirmed'] = True
        session_state['status'] = 'waiting_start'
        send_whatsapp(sender, "📅 أرسل تاريخ بدء العمل (مثال: 1446/01/01) أو 'تخطي'")

    elif incoming_msg == 'تخطي' and session_state['status'] in ['waiting_start', 'waiting_qual']:
        if session_state['status'] == 'waiting_start':
            session_state['start_date'] = None
            session_state['status'] = 'waiting_qual'
            send_whatsapp(sender, "🎓 أرسل المؤهل العلمي أو 'تخطي'")
        elif session_state['status'] == 'waiting_qual':
            session_state['qualification'] = None
            session_state['status'] = 'done'
            send_whatsapp(sender, "✅ تم التسجيل النهائي")

    elif session_state['status'] == 'waiting_start':
        session_state['start_date'] = incoming_msg
        session_state['status'] = 'waiting_qual'
        send_whatsapp(sender, "🎓 أرسل المؤهل العلمي أو 'تخطي'")

    elif session_state['status'] == 'waiting_qual':
        session_state['qualification'] = incoming_msg
        session_state['status'] = 'done'
        send_whatsapp(sender, "✅ تم حفظ كل المعلومات بنجاح")

    elif session_state['status'] == 'waiting_otp' and incoming_msg.isdigit():
        session_state['otp'] = incoming_msg
        session_state['status'] = 'registering'
        send_whatsapp(sender, "⏳ جاري التحقق من رمز OTP...")

    elif session_state['status'] == 'waiting_dob' and "/" in incoming_msg:
        session_state['dob'] = incoming_msg
        session_state['status'] = 'registering'
        send_whatsapp(sender, "⏳ جاري التحقق من تاريخ الميلاد...")

    return ('', 200)

def login_to_gosi(nid, pwd):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.gosi.gov.sa")
        time.sleep(3)
        driver.save_screenshot("screen.png")
        img_url = upload_to_imgbb("screen.png")
        driver.quit()
        return 'success', img_url
    except Exception as e:
        print(f"[Login Error] {str(e)}")
        return 'error', upload_to_imgbb("screen.png")

def upload_to_imgur(path):
    try:
        import requests
        api_key = os.environ['IMGBB_API_KEY']
        with open(path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                'key': api_key,
                'image': img_base64
            }
        )
        if res.status_code == 200:
            return res.json()['data']['url']
        else:
            print(f"[ImgBB Error] {res.text}")
            return None
    except Exception as e:
        print(f"[ImgBB Exception] {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)

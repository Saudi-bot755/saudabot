# ملف smart.py النهائي

import os
from flask import Flask, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import base64
from PIL import Image
from io import BytesIO
import datetime

# تهيئة Flask
app = Flask(__name__)

# بيانات البيئة (من Railway)
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
user_number = os.environ['USER_PHONE_NUMBER']

client = Client(account_sid, auth_token)

# الحالة الحالية للجلسة
global session_state
session_state = {
    "status": "idle",  # idle, waiting_otp, waiting_dob, registering, done, error
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
        print(f"[خطأ Twilio] {e}")

@app.route("/bot", methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    sender = request.values.get('From', '').replace('whatsapp:', '')
    print(f"رسالة واردة: {incoming_msg}")

    if "سعوده" in incoming_msg:
        session_state['status'] = 'idle'
        send_whatsapp(sender, "📝 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    elif "سجلت" in incoming_msg:
        # الرد حسب حالة الجلسة
        status = session_state['status']
        if status == 'registering':
            send_whatsapp(sender, "⏳ جارٍ التسجيل... تأكد من بقاء التطبيق مفتوحًا")
        elif status == 'waiting_otp':
            send_whatsapp(sender, "🔐 نحتاج رمز التحقق (OTP) من أبشر، الرجاء إرساله مثل: 123456")
        elif status == 'waiting_dob':
            send_whatsapp(sender, "🎂 الرجاء إرسال تاريخ ميلادك بالشكل: 1410/10/05")
        elif status == 'done':
            send_whatsapp(sender, "✅ تم التسجيل بنجاح في السعودة")
        elif status == 'error':
            send_whatsapp(sender, "❌ فشل التسجيل، قد تكون هناك مشكلة في البيانات أو الموقع")
        else:
            send_whatsapp(sender, "📭 لا يوجد تسجيل نشط حالياً، أرسل كلمة 'سعودة' للبدء")

    elif "*" in incoming_msg:
        try:
            nid, pwd = incoming_msg.split("*")
            send_whatsapp(sender, "⏳ يرجى الانتظار، جاري تسجيل الدخول...")
            session_state['status'] = 'registering'

            result, screenshot_url = login_to_gosi(nid.strip(), pwd.strip())

            session_state['screenshot_url'] = screenshot_url

            if result == 'otp':
                session_state['status'] = 'waiting_otp'
                send_whatsapp(sender, "🔐 أرسل رمز التحقق OTP من أبشر")
            elif result == 'dob':
                session_state['status'] = 'waiting_dob'
                send_whatsapp(sender, "🎂 أرسل تاريخ الميلاد بالشكل: 1410/10/05")
            elif result == 'success':
                session_state['status'] = 'done'
                send_whatsapp(sender, "✅ تم التسجيل في السعودة بنجاح", media_url=screenshot_url)
            else:
                session_state['status'] = 'error'
                send_whatsapp(sender, "❌ حدث خطأ أثناء التسجيل", media_url=screenshot_url)
        except Exception as e:
            session_state['status'] = 'error'
            send_whatsapp(sender, f"❌ فشل التحليل، يرجى التأكد من التنسيق الصحيح: الهوية*كلمةالمرور")

    elif "/" in incoming_msg:
        # تاريخ الميلاد
        session_state['status'] = 'registering'
        send_whatsapp(sender, "⏳ جاري التحقق من البيانات...")
        # هنا يمكن استكمال التحقق من تاريخ الميلاد

    elif incoming_msg.isdigit() and len(incoming_msg) == 6:
        # رمز التحقق OTP
        session_state['status'] = 'registering'
        send_whatsapp(sender, "⏳ جارٍ إدخال رمز التحقق...")
        # هنا يمكن استكمال التحقق من otp

    return ('', 200)

# تسجيل الدخول لموقع التأمينات

def login_to_gosi(nid, pwd):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://www.gosi.gov.sa")
        time.sleep(2)

        # مثال فقط - تغيير حسب عناصر الموقع الحقيقية
        driver.save_screenshot("screen.png")
        screenshot_url = upload_to_imgur("screen.png")
        driver.quit()
        return 'success', screenshot_url

    except Exception as e:
        print("[خطأ أثناء التسجيل]:", str(e))
        return 'error', upload_to_imgur("screen.png")

def upload_to_imgur(path):
    try:
        import requests
        headers = {'Authorization': f'Client-ID {os.environ.get("IMGUR_CLIENT_ID")}'}
        with open(path, 'rb') as f:
            image_data = base64.b64encode(f.read())
        res = requests.post("https://api.imgur.com/3/upload", headers=headers, data={'image': image_data})
        return res.json()['data']['link'] if res.status_code == 200 else None
    except:
        return None

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)

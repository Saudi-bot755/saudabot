import os
import time
import base64
import datetime
from flask import Flask, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import requests
from PIL import Image
import io

app = Flask(__name__)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
client = Client(account_sid, auth_token)

sessions = {}

IMGUR_CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')


def send_whatsapp_message(to, body, media_url=None):
    message = {
        'from_': f'whatsapp:{twilio_number}',
        'body': body,
        'to': to
    }
    if media_url:
        message['media_url'] = [media_url]
    client.messages.create(**message)


def capture_screenshot(driver):
    screenshot = driver.get_screenshot_as_png()
    return screenshot


def upload_to_imgur(image_binary):
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    files = {"image": image_binary}
    response = requests.post("https://api.imgur.com/3/image", headers=headers, files=files)
    return response.json()["data"]["link"]


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    session = sessions.get(from_number, {'step': 'login'})

    def save_session():
        sessions[from_number] = session

    if session['step'] == 'login':
        if '*' not in incoming_msg:
            send_whatsapp_message(from_number, '🔐 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Aa123456')
            return ('', 200)
        nid, password = incoming_msg.split('*')
        session['nid'] = nid
        session['password'] = password

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)
        session['driver'] = driver

        try:
            driver.get("https://www.gosi.gov.sa/GOSIOnline/Individual")
            time.sleep(3)
            # تسجيل الدخول (حسب الموقع الفعلي)
            session['step'] = 'check_otp_or_dob'
            save_session()
            send_whatsapp_message(from_number, '✅ تم استلام البيانات بنجاح، جارٍ المتابعة...')
        except Exception as e:
            screenshot = capture_screenshot(driver)
            img_url = upload_to_imgur(screenshot)
            send_whatsapp_message(from_number, f'❌ حدث خطأ أثناء تسجيل الدخول:\n{str(e)}', media_url=img_url)
            session['step'] = 'login'
            save_session()
        return ('', 200)

    if session['step'] == 'check_otp_or_dob':
        driver = session['driver']
        try:
            if 'otp_sent' not in session:
                # تحقق هل الموقع يطلب OTP
                if True:  # شرط مؤقت افتراضي
                    send_whatsapp_message(from_number, '📲 أرسل رمز التحقق OTP الذي وصلك')
                    session['otp_sent'] = True
                    session['step'] = 'otp'
                    save_session()
                    return ('', 200)
            elif 'dob_sent' not in session:
                # تحقق هل الموقع يطلب تاريخ الميلاد
                if True:  # شرط مؤقت افتراضي
                    send_whatsapp_message(from_number, '📅 أرسل تاريخ الميلاد بصيغة: YYYY-MM-DD')
                    session['dob_sent'] = True
                    session['step'] = 'dob'
                    save_session()
                    return ('', 200)
        except Exception as e:
            screenshot = capture_screenshot(driver)
            img_url = upload_to_imgur(screenshot)
            send_whatsapp_message(from_number, f'❌ حدث خطأ أثناء التحقق:\n{str(e)}', media_url=img_url)
            session['step'] = 'login'
            save_session()
        return ('', 200)

    if session['step'] == 'otp':
        otp = incoming_msg
        session['otp'] = otp
        # إدخال OTP في الموقع هنا باستخدام Selenium
        session['step'] = 'check_otp_or_dob'
        save_session()
        send_whatsapp_message(from_number, '✅ تم استلام رمز OTP، جارٍ المتابعة...')
        return ('', 200)

    if session['step'] == 'dob':
        dob = incoming_msg
        session['dob'] = dob
        # إدخال تاريخ الميلاد في الموقع باستخدام Selenium
        session['step'] = 'register_start'
        save_session()
        send_whatsapp_message(from_number, '✅ تم استلام تاريخ الميلاد، جارٍ البدء في التسجيل...')
        return ('', 200)

    return ('', 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

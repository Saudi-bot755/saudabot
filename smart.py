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
twilio_number = os.environ['TWILIO_PHONE_NUMBER']
client = Client(account_sid, auth_token)

# Global sessions
sessions = {}

# Imgur upload
IMGUR_CLIENT_ID = os.environ['IMGUR_CLIENT_ID']
def upload_image(path):
    with open(path, "rb") as f:
        img_data = base64.b64encode(f.read())
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    data = {"image": img_data}
    res = requests.post("https://api.imgur.com/3/image", headers=headers, data=data)
    return res.json()['data']['link'] if res.status_code == 200 else None

# Selenium setup
def start_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def send_whatsapp(to, body, media_url=None):
    client.messages.create(
        from_=f"whatsapp:{twilio_number}",
        to=to,
        body=body,
        media_url=media_url
    )

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    if from_number not in sessions:
        sessions[from_number] = {'step': 'wait_id_pw'}

    session = sessions[from_number]

    try:
        if session['step'] == 'wait_id_pw':
            if '*' in incoming_msg:
                nid, pw = incoming_msg.split('*')
                session['nid'] = nid
                session['pw'] = pw
                send_whatsapp(from_number, '⏳ جاري تسجيل الدخول، الرجاء الانتظار...')

                driver = start_driver()
                session['driver'] = driver
                driver.get("https://www.gosi.gov.sa")

                # خطوات تسجيل الدخول
                # مثال (تغيير حسب الموقع الفعلي):
                driver.find_element(By.ID, 'id_number').send_keys(nid)
                driver.find_element(By.ID, 'password').send_keys(pw)
                driver.find_element(By.ID, 'login_button').click()

                time.sleep(3)
                if 'OTP' in driver.page_source:
                    session['step'] = 'wait_otp'
                    send_whatsapp(from_number, '🔐 أرسل رمز التحقق OTP من أبشر:')
                elif 'تاريخ الميلاد' in driver.page_source:
                    session['step'] = 'wait_birth'
                    send_whatsapp(from_number, '📅 الرجاء إدخال تاريخ الميلاد (مثال: 01/01/2000):')
                else:
                    session['step'] = 'confirm_job'
                    send_whatsapp(from_number, '🧾 هل تريد المتابعة لتسجيل المهنة "محاسب" والراتب 4000؟ (نعم/لا)')
            else:
                send_whatsapp(from_number, '🪪 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Pass1234')

        elif session['step'] == 'wait_otp':
            driver = session['driver']
            driver.find_element(By.ID, 'otp').send_keys(incoming_msg)
            driver.find_element(By.ID, 'submit_otp').click()
            session['step'] = 'wait_birth'
            send_whatsapp(from_number, '📅 الرجاء إدخال تاريخ الميلاد:')

        elif session['step'] == 'wait_birth':
            driver = session['driver']
            driver.find_element(By.ID, 'birthdate').send_keys(incoming_msg)
            driver.find_element(By.ID, 'submit_birth').click()
            session['step'] = 'confirm_job'
            send_whatsapp(from_number, '🧾 هل تريد تسجيل المهنة "محاسب" والراتب 4000؟ (نعم/لا)')

        elif session['step'] == 'confirm_job':
            if 'نعم' in incoming_msg:
                driver = session['driver']
                # إدخال بيانات التسجيل
                driver.find_element(By.ID, 'job_title').send_keys('محاسب')
                driver.find_element(By.ID, 'salary').send_keys('4000')
                driver.find_element(By.ID, 'submit_application').click()
                time.sleep(2)

                screenshot_path = f"/tmp/{from_number[-4:]}.png"
                driver.save_screenshot(screenshot_path)
                img_url = upload_image(screenshot_path)
                send_whatsapp(from_number, '✅ تم تقديم طلب التسجيل بنجاح!', media_url=img_url)
                driver.quit()
                del sessions[from_number]
            else:
                send_whatsapp(from_number, '❌ تم إلغاء الطلب.')
                sessions.pop(from_number, None)

        else:
            send_whatsapp(from_number, '⚠️ حدث خطأ غير متوقع. ابدأ من جديد.')
            sessions.pop(from_number, None)

    except Exception as e:
        img = None
        if 'driver' in session:
            path = f"/tmp/error_{from_number[-4:]}.png"
            session['driver'].save_screenshot(path)
            img = upload_image(path)
            session['driver'].quit()
        send_whatsapp(from_number, f'❌ حدث خطأ: {str(e)}', media_url=img)
        sessions.pop(from_number, None)

    return ('', 200)

if __name__ == '__main__':
    app.run(debug=False)

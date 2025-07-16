import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import re

app = Flask(__name__)

TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
sessions = {}

def respond(message):
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)

def login_to_gosi(national_id, password):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    driver.get("https://taminaty.gosi.gov.sa/")
    try:
        id_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        id_input.send_keys(national_id)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        return driver
    except Exception:
        driver.quit()
        raise

@app.route('/')
def home():
    return '✅ البوت يعمل بنجاح بدون ذكاء اصطناعي'

@app.route('/message', methods=['POST'])
def message():
    incoming_msg = request.form.get('Body').strip()
    from_number = request.form.get('From')
    session = sessions.get(from_number, {'state': 'awaiting_login'})
    state = session.get('state')

    if state == 'awaiting_login':
        if '*' in incoming_msg:
            parts = incoming_msg.split('*', 1)
            if len(parts) == 2 and parts[0].isdigit():
                national_id = parts[0]
                password = parts[1]
                try:
                    driver = login_to_gosi(national_id, password)
                    session['driver'] = driver
                    session['state'] = 'awaiting_otp'
                    sessions[from_number] = session
                    return respond("✅ تم تسجيل الدخول. أرسل رمز التحقق (OTP) المكون من 4 أرقام.")
                except:
                    return respond("❌ فشل تسجيل الدخول. تأكد من البيانات.")
        return respond("📌 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n\n1234567890*كلمةالمرور")

    elif state == 'awaiting_otp':
        if re.fullmatch(r"\d{4}", incoming_msg):
            driver = session.get('driver')
            if driver:
                try:
                    otp_input = driver.find_element(By.NAME, 'otp')
                    otp_input.send_keys(incoming_msg)
                    otp_input.send_keys(Keys.RETURN)
                    session['state'] = 'awaiting_dob'
                    sessions[from_number] = session
                    return respond("✅ تم التحقق. الآن أرسل تاريخ ميلادك مثل: 01/01/1400")
                except:
                    driver.quit()
                    sessions.pop(from_number, None)
                    return respond("❌ فشل التحقق من الرمز.")
        return respond("⚠️ رمز التحقق غير صحيح. أرسل 4 أرقام فقط.")

    elif state == 'awaiting_dob':
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", incoming_msg):
            driver = session.get('driver')
            if driver:
                try:
                    dob_input = driver.find_element(By.NAME, 'birthDate')
                    dob_input.send_keys(incoming_msg)
                    dob_input.send_keys(Keys.RETURN)
                    driver.quit()
                    sessions.pop(from_number, None)
                    return respond("✅ تم تقديم نموذج السعودة بنجاح!")
                except:
                    driver.quit()
                    sessions.pop(from_number, None)
                    return respond("❌ حدث خطأ أثناء إرسال النموذج.")
        return respond("📌 أرسل تاريخ الميلاد بالتنسيق: يوم/شهر/سنة هجرية مثل:\n01/01/1400")

    else:
        return respond("📢 مرحباً بك! أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*كلمةالمرور")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

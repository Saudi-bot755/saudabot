import os
import re
import openai
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# عرض رسالة على الصفحة الرئيسية
@app.route('/')
def home():
    return '✅ البوت شغال تمام'

# مفاتيح البيئة
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
openai.api_key = os.getenv('OPENAI_API_KEY')

# تخزين الجلسات
sessions = {}

def respond(message):
    """إنشاء رد Twilio"""
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
        try:
            login_button = driver.find_element(By.XPATH, "//button[contains(text(),'دخول') or contains(text(),'تسجيل')]")
            login_button.click()
        except:
            password_input.send_keys(Keys.RETURN)
        return driver
    except Exception:
        driver.quit()
        raise

@app.route('/bot', methods=['POST'])
def bot_webhook():
    incoming_msg = request.form.get('Body').strip()
    from_number = request.form.get('From')
    session = sessions.get(from_number, {'state': 'awaiting_login'})
    state = session['state']

    # انتظار تسجيل الدخول
    if state == 'awaiting_login':
        if '*' in incoming_msg:
            parts = incoming_msg.split('*', 1)
            if len(parts) == 2 and parts[0].isdigit():
                national_id, password = parts
                try:
                    driver = login_to_gosi(national_id, password)
                    session.update({'driver': driver, 'state': 'awaiting_otp'})
                    sessions[from_number] = session
                    return respond("تم تسجيل الدخول بنجاح. الرجاء إرسال رمز التحقق.")
                except:
                    return respond("فشل تسجيل الدخول. تحقق من البيانات.")
        return gpt_reply(incoming_msg)

    # انتظار OTP
    elif state == 'awaiting_otp':
        if re.fullmatch(r"\d{4}", incoming_msg):
            driver = session.get('driver')
            try:
                otp_input = driver.find_element(By.NAME, 'otp')
                otp_input.send_keys(incoming_msg)
                try:
                    verify_button = driver.find_element(By.XPATH, "//button[contains(text(),'تحقق') or contains(text(),'تأكيد') or contains(text(),'Verify')]")
                    verify_button.click()
                except:
                    otp_input.send_keys(Keys.RETURN)
                session['state'] = 'awaiting_dob'
                sessions[from_number] = session
                return respond("✅ أدخل تاريخ ميلادك (مثال: 01/01/1400)")
            except:
                driver.quit()
                sessions.pop(from_number, None)
                return respond("❌ فشل التحقق من OTP")
        return gpt_reply(incoming_msg)

    # انتظار تاريخ الميلاد
    elif state == 'awaiting_dob':
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", incoming_msg):
            driver = session.get('driver')
            try:
                dob_input = driver.find_element(By.NAME, 'birthDate')
                dob_input.send_keys(incoming_msg)
                try:
                    submit_button = driver.find_element(By.XPATH, "//button[contains(text(),'سعودة') or contains(text(),'إرسال') or contains(text(),'Submit')]")
                    submit_button.click()
                except:
                    dob_input.send_keys(Keys.RETURN)
                driver.quit()
                sessions.pop(from_number, None)
                return respond("🎉 تم تقديم السعودة بنجاح!")
            except:
                driver.quit()
                sessions.pop(from_number, None)
                return respond("❌ فشل إرسال النموذج.")
        return gpt_reply(incoming_msg)

    # أي حالة غير معروفة
    return gpt_reply(incoming_msg)

def gpt_reply(user_msg):
    messages = [
        {'role': 'system', 'content': 'أنت مساعد ذكي باللغة العربية. أجب بإيجاز ووضوح.'},
        {'role': 'user', 'content': user_msg}
    ]
    try:
        gpt_response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages)
        return respond(gpt_response.choices[0].message.content)
    except:
        return respond("❌ حدث خطأ أثناء التواصل مع الذكاء الاصطناعي")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

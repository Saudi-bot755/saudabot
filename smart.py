# يلزم تثبيت الحزم التالية قبل التشغيل:
# pip install flask twilio selenium openai python-dotenv
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
# من المكتبات الضرورية للتكامل مع موقع التأمينات
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import openai
import re
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ البوت شغال تمام'
    
# إعداد مفاتيح Twilio و OpenAI (يتم تعيينها في ملف .env)
# TWILIO_ACCOUNT_SID و TWILIO_AUTH_TOKEN (قد لا نحتاجهما عند الرد بواسطة TwiML)
# TWILIO_WHATSAPP_NUMBER: رقم صندوق الواتساب (Sandbox) بصيغة whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
openai.api_key = os.getenv('OPENAI_API_KEY')


# قاموس لتخزين جلسات المستخدمين وحالتهم
sessions = {}

def respond(message):
    """تحضير رد TwiML"""
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)

def login_to_gosi(national_id, password):
    """وظيفة تسجيل الدخول إلى موقع التأمينات باستخدام Selenium"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    # إذا كان chromedriver غير في PATH، اضبط المسار هنا:
    # driver = webdriver.Chrome(executable_path='/path/to/chromedriver', options=options)

    # افتح صفحة تسجيل الدخول (قد تحتاج تعديل الرابط وفق الموقع)
    driver.get("https://taminaty.gosi.gov.sa/")
    try:
        # ابحث عن حقل رقم الهوية
        id_input = None
        try:
            id_input = driver.find_element(By.ID, "username")
        except:
            pass
        if not id_input:
            try:
                id_input = driver.find_element(By.NAME, "username")
            except:
                pass
        if not id_input:
            id_input = driver.find_element(By.XPATH, "//label[contains(text(),'رقم الهوية')]/following::input")

        # ابحث عن حقل كلمة المرور
        password_input = None
        try:
            password_input = driver.find_element(By.ID, "password")
        except:
            pass
        if not password_input:
            try:
                password_input = driver.find_element(By.NAME, "password")
            except:
                pass
        if not password_input:
            password_input = driver.find_element(By.XPATH, "//label[contains(text(),'كلمة المرور')]/following::input")

        # أدخل بيانات المستخدم
        id_input.send_keys(national_id)
        password_input.send_keys(password)

        # اضغط زر تسجيل الدخول (قد يكون باسم 'دخول' أو 'تسجيل الدخول')
        try:
            login_button = driver.find_element(By.XPATH, "//button[contains(text(),'دخول') or contains(text(),'تسجيل')]")
            login_button.click()
        except:
            try:
                password_input.send_keys(Keys.RETURN)
            except:
                pass

        return driver
    except Exception:
        driver.quit()
        raise

@app.route('/message', methods=['POST'])
def message():
    incoming_msg = request.form.get('Body').strip()
    from_number = request.form.get('From')
    session = sessions.get(from_number, {'state': 'awaiting_login'})
    state = session.get('state')

    # الحالة الأولى: انتظار رقم الهوية وكلمة المرور
    if state == 'awaiting_login':
        # تحقق من وجود * في الرسالة للفصل بين الهوية والكلمة
        if '*' in incoming_msg:
            parts = incoming_msg.split('*', 1)
            if len(parts) == 2 and parts[0].isdigit():
                national_id = parts[0]
                password = parts[1]
                try:
                    driver = login_to_gosi(national_id, password)
                    # تسجيل نجاح تسجيل الدخول والانتقال للسؤال عن OTP
                    session['driver'] = driver
                    session['state'] = 'awaiting_otp'
                    sessions[from_number] = session
                    return respond("تم تسجيل الدخول بنجاح. الرجاء إرسال رمز التحقق المكون من 4 أرقام.")
                except Exception:
                    return respond("فشل تسجيل الدخول، يرجى التحقق من رقم الهوية وكلمة المرور.")
        # تنسيق غير صحيح: رد عام بواسطة GPT
        messages = [
            {'role': 'system', 'content': 'أنت مساعد ذكي باللغة العربية. أجب بإيجاز ووضوح.'},
            {'role': 'user', 'content': incoming_msg}
        ]
        try:
            gpt_response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages)
            answer = gpt_response.choices[0].message.content
        except Exception:
            answer = "عذراً، حدث خطأ أثناء معالجة الرسالة."
        return respond(answer)

    # الحالة الثانية: انتظار رمز التحقق OTP
    elif state == 'awaiting_otp':
        # التحقق من أن الرسالة 4 أرقام
        if re.fullmatch(r"\d{4}", incoming_msg):
            driver = session.get('driver')
            if driver:
                try:
                    otp_input = None
                    try:
                        otp_input = driver.find_element(By.NAME, 'otp')
                    except:
                        pass
                    if not otp_input:
                        otp_input = driver.find_element(By.XPATH, "//input[@type='text' or @type='number']")
                    otp_input.send_keys(incoming_msg)
                    try:
                        verify_button = driver.find_element(By.XPATH, "//button[contains(text(),'تحقق') or contains(text(),'تأكيد') or contains(text(),'Verify')]")
                        verify_button.click()
                    except:
                        try:
                            otp_input.send_keys(Keys.RETURN)
                        except:
                            pass
                    session['state'] = 'awaiting_dob'
                    sessions[from_number] = session
                    return respond("تم التحقق. الرجاء إرسال تاريخ ميلادك (مثال: 01/01/1400).")
                except Exception:
                    driver.quit()
                    sessions.pop(from_number, None)
                    return respond("حدث خطأ أثناء التحقق من رمز التحقق.")
        # غير صالح: رد عام بواسطة GPT
        messages = [
            {'role': 'system', 'content': 'أنت مساعد ذكي باللغة العربية. أجب بإيجاز ووضوح.'},
            {'role': 'user', 'content': incoming_msg}
        ]
        try:
            gpt_response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages)
            answer = gpt_response.choices[0].message.content
        except Exception:
            answer = "عذراً، حدث خطأ أثناء معالجة الرسالة."
        return respond(answer)

    # الحالة الثالثة: انتظار تاريخ الميلاد
    elif state == 'awaiting_dob':
        # التحقق من تنسيق تاريخ الميلاد
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", incoming_msg):
            driver = session.get('driver')
            if driver:
                try:
                    dob_input = None
                    try:
                        dob_input = driver.find_element(By.NAME, 'birthDate')
                    except:
                        pass
                    if not dob_input:
                        dob_input = driver.find_element(By.XPATH, "//label[contains(text(),'تاريخ الميلاد')]/following::input")
                    dob_input.send_keys(incoming_msg)
                    try:
                        submit_button = driver.find_element(By.XPATH, "//button[contains(text(),'سعودة') or contains(text(),'إرسال') or contains(text(),'Submit')]")
                        submit_button.click()
                    except:
                        try:
                            dob_input.send_keys(Keys.RETURN)
                        except:
                            pass
                    driver.quit()
                    sessions.pop(from_number, None)
                    return respond("تم تقديم نموذج السعودة بنجاح!")
                except Exception:
                    driver.quit()
                    sessions.pop(from_number, None)
                    return respond("فشل إرسال نموذج السعودة. يرجى المحاولة مرة أخرى.")
        # تنسيق غير صحيح: رد عام بواسطة GPT
        messages = [
            {'role': 'system', 'content': 'أنت مساعد ذكي باللغة العربية. أجب بإيجاز ووضوح.'},
            {'role': 'user', 'content': incoming_msg}
        ]
        try:
            gpt_response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages)
            answer = gpt_response.choices[0].message.content
        except Exception:
            answer = "عذراً، حدث خطأ أثناء معالجة الرسالة."
        driver = session.get('driver')
        if driver:
            driver.quit()
        sessions.pop(from_number, None)
        return respond(answer)

    # أي حالة أخرى: رد عام بواسطة GPT
    else:
        messages = [
            {'role': 'system', 'content': 'أنت مساعد ذكي باللغة العربية. أجب بإيجاز ووضوح.'},
            {'role': 'user', 'content': incoming_msg}
        ]
        try:
            gpt_response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages)
            answer = gpt_response.choices[0].message.content
        except Exception:
            answer = "عذراً، حدث خطأ أثناء معالجة الرسالة."
        return respond(answer)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

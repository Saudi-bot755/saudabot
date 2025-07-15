from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os, time, json, datetime
from twilio.rest import Client
from pathlib import Path
import pytesseract
from PIL import Image
import openai

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ البوت شغال تمام'

@app.route('/bot', methods=['POST'])
def bot_webhook():
    data = request.json
    msg = data.get("body", "").lower()
    sender = data.get("from")

    if "سعوده" in msg:
        send_whatsapp(sender, "📝 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")
    elif "*" in msg:
        try:
            national_id, password = msg.split("*")
            if len(password) < 8 or password.lower() == password:
                return send_whatsapp(sender, "❌ كلمة المرور يجب أن تحتوي على حرف كبير وحروف إنجليزية.")
            send_whatsapp(sender, "⏳ جارٍ تنفيذ السعودة.. الرجاء الانتظار")
            with open(f"codes/{national_id}.txt", "w") as f:
                f.write("")  # Reset old code
            login_and_saudah(national_id, password, sender)
        except:
            return send_whatsapp(sender, "❌ التنسيق غير صحيح. أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")
    else:
        # الرد الذكي باستخدام OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": msg}
                ]
            )
            reply = response.choices[0].message.content.strip()
            send_whatsapp(sender, reply)
        except:
            send_whatsapp(sender, "⚠️ حدث خطأ في الاتصال بالذكاء الاصطناعي")
    return jsonify({"status": "ok"})

def login_and_saudah(national_id, password, sender):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[contains(text(), 'أعمال')]").click()
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(national_id)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(3)

        send_whatsapp(sender, "📲 أرسل كود التحقق الآن")
        code = wait_for_code(national_id)
        driver.find_element(By.ID, "otp").send_keys(code)
        driver.find_element(By.ID, "verify-button").click()
        time.sleep(3)

        # تابع خطوات السعودة هنا
        driver.get("https://www.gosi.gov.sa/GOSIOnline/employer/add-employee")
        time.sleep(3)

        # تعبئة بيانات الموظف
        driver.find_element(By.ID, "jobTitle").send_keys("محاسب")
        driver.find_element(By.ID, "salary").send_keys("4000")

        # إرسال لقطة شاشة بعد النجاح
        screenshot_path = f"screenshots/{national_id}.png"
        driver.save_screenshot(screenshot_path)
        send_whatsapp(sender, "✅ تم تسجيل سعودي جديد")
        send_whatsapp(sender, "📸 صورة الشاشة:", file_path=screenshot_path)

    except Exception as e:
        error_img = f"screenshots/error_{national_id}.png"
        driver.save_screenshot(error_img)
        error_text = extract_text(error_img)
        send_whatsapp(sender, f"❌ فشل التسجيل:\n{error_text}")
        send_whatsapp(sender, "📸 صورة تم التقاطها بنجاح")
        if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

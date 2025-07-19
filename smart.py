from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, time, requests, base64

app = Flask(__name__)
@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    
    # استدعاء الدالة اللي تتعامل مع الرسائل
    response_text = handle_message(incoming_msg, from_number)
    
    return "OK", 200

def handle_message(msg, user):
    print(f"📩 رسالة من {user}: {msg}")
    return "تم استلام رسالتك ✅"
    
# إعداد المتغيرات البيئية
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

sessions = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From")
    msg = request.form.get("Body").strip()
    resp = MessagingResponse()
    reply = resp.message()

    session = sessions.get(sender, {"step": 0})

    def send(message):
        reply.body(message)
        return str(resp)

    def screenshot_and_upload(driver):
        path = "/tmp/shot.png"
        driver.save_screenshot(path)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read())
        r = requests.post(
            "https://api.imgur.com/3/image",
            headers={"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"},
            data={"image": b64}
        )
        if r.ok:
            return r.json()['data']['link']
        return None

    # خطوات المحادثة
    if msg.lower() in ["سعوده", "ابدأ"]:
        session = {"step": 1}
        sessions[sender] = session
        return send("🔐 أرسل رقم الهوية وكلمة المرور بهذا الشكل:\n1234567890*Abc12345")

    if session["step"] == 1:
        try:
            nid, pwd = msg.split("*")
            session.update({"nid": nid, "pwd": pwd})
            session["step"] = 2
            sessions[sender] = session
            return send("📲 أرسل رمز التحقق OTP")
        except:
            return send("❌ تأكد من التنسيق:\n1234567890*Abc12345")

    if session["step"] == 2:
        session["otp"] = msg
        session["step"] = 3
        sessions[sender] = session
        return send("🆔 رقم الهوية الوطنية للموظف\nأو أرسل 'تخطي'")

    if session["step"] == 3:
        session["emp_nid"] = msg
        session["step"] = 4
        sessions[sender] = session
        return send("🎂 تاريخ الميلاد (مثال: 1410/01/01)\nأو أرسل 'تخطي'")

    if session["step"] == 4:
        session["birth"] = msg
        session["step"] = 5
        sessions[sender] = session
        return send("🌍 الجنسية (اكتب: سعودي)\nأو أرسل 'تخطي'")

    if session["step"] == 5:
        session["nationality"] = msg
        session["step"] = 6
        sessions[sender] = session
        return send("📅 تاريخ مباشرة العمل (مثال: 1446/01/01)\nأو أرسل 'تخطي'")

    if session["step"] == 6:
        session["work_date"] = msg
        session["step"] = 7
        sessions[sender] = session
        return send("📄 نوع العقد (دائم – مؤقت – تدريب)\nأو أرسل 'تخطي'")

    if session["step"] == 7:
        session["contract"] = msg
        session["step"] = 8
        sessions[sender] = session
        return send("⏱️ مدة العقد (اكتب 'تخطي' إذا لا يوجد)\nأو أرسل 'تخطي'")

    if session["step"] == 8:
        session["duration"] = msg
        session["step"] = 9
        sessions[sender] = session
        return send("🧳 المهنة (مثال: محاسب)\nأو أرسل 'تخطي'")

    if session["step"] == 9:
        session["job"] = msg
        session["step"] = 10
        sessions[sender] = session
        return send("💰 الراتب الأساسي (مثال: 4000)\nأو أرسل 'تخطي'")

    if session["step"] == 10:
        session["salary"] = msg
        session["step"] = 11
        sessions[sender] = session
        return send("🏡 البدلات (اكتب 'تخطي' إذا لا يوجد)\nأو أرسل 'تخطي'")

    if session["step"] == 11:
        session["allow"] = msg
        session["step"] = 12
        sessions[sender] = session
        return send("📊 الأجر الخاضع للاشتراك (الراتب + البدلات)\nأو أرسل 'تخطي'")

    if session["step"] == 12:
        session["total"] = msg
        session["step"] = 13
        sessions[sender] = session
        return send("📌 سبب التسجيل (التحاق جديد – نقل...)\nأو أرسل 'تخطي'")

    if session["step"] == 13:
        session["reason"] = msg
        session["step"] = 14
        sessions[sender] = session
        return send("🏢 جهة العمل أو الفرع\nأو أرسل 'تخطي'")

    if session["step"] == 14:
        session["branch"] = msg
        session["step"] = 15
        sessions[sender] = session
        return send("📝 ملاحظات إضافية (اكتب 'تخطي' إذا لا يوجد)\nأو أرسل 'تخطي'")

    if session["step"] == 15:
        session["note"] = msg
        session["step"] = 16
        sessions[sender] = session

        # الآن نبدأ التنفيذ الحقيقي باستخدام Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get("https://www.gosi.gov.sa")
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "تسجيل الدخول"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "دخول أعمال"))).click()

            # دخول النفاذ الوطني (المفترض يتم تلقائي، يمكن التعديل لاحقًا)
            time.sleep(10)
            # إدخال OTP
            # يتم تجاوزه في هذا النموذج التجريبي

            # تسجيل الموظف السعودي:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="nationalId"]'))).send_keys(session['emp_nid'])
            if session['birth'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="birthDate"]').send_keys(session['birth'])
            if session['nationality'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="nationality"]').send_keys(session['nationality'])
            if session['work_date'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="employmentDate"]').send_keys(session['work_date'])
            if session['contract'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="contractType"]').send_keys(session['contract'])
            if session['duration'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="contractDuration"]').send_keys(session['duration'])
            if session['job'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="jobTitle"]').send_keys(session['job'])
            if session['salary'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="basicSalary"]').send_keys(session['salary'])
            if session['allow'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="allowances"]').send_keys(session['allow'])
            if session['total'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="subscriptionSalary"]').send_keys(session['total'])
            if session['reason'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="registrationReason"]').send_keys(session['reason'])
            if session['branch'] != "تخطي":
                driver.find_element(By.XPATH, '//*[@id="branch"]').send_keys(session['branch'])

            driver.find_element(By.XPATH, '//*[@id="submitBtn"]').click()

            link = screenshot_and_upload(driver)
            driver.quit()
            return send(f"📦 تم رفع الطلب بنجاح!\nصورة التأكيد: {link}")
        except Exception as e:
            img = screenshot_and_upload(driver)
            driver.quit()
            return send(f"❌ حدث خطأ أثناء التسجيل\nالصورة: {img}\nالخطأ: {str(e)}")

    return send("⚠️ أرسل 'سعوده' للبدء")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

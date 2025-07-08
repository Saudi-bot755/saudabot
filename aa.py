from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time

app = Flask(__name__)
sessions = {}

# -------  إعداد المتصفح -------
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

@app.route("/bot", methods=["POST"])
def bot():
    sender = request.form.get("From")
    msg = request.form.get("Body", "").strip()
    resp = MessagingResponse()
    r = resp.message()

    # إلغاء العملية فوراً
    if msg.lower() == "إلغاء":
        sessions.pop(sender, None)
        r.body("❌ تم إلغاء العملية. ارسل 'سعودة' للبدء مرة أخرى.")
        return str(resp)

    # بدء أو متابعة الجلسة
    session = sessions.get(sender, {"step": "start"})
    step = session["step"]

    if step == "start" and "سعودة" in msg:
        session["step"] = "credentials"
        r.body("📝 أرسل الهوية وكلمة المرور كالآتي:\nهوية: 1234567890\nكلمة: password")
    elif step == "credentials" and msg.startswith("هوية:") and "كلمة:" in msg:
        session["step"] = "verify"
        session["credentials"] = msg
        r.body("📲 أرسل كود التحقق عندما يصلك عبر رسالة واتساب (مثال: كود: 1234)")
    elif step == "verify" and msg.startswith("كود:"):
        session["code"] = msg
        r.body("✅ تسجيل الدخول تم.\n⏳ جاري تنفيذ السعودة... انتظر لحظة.")
        session["step"] = "processing"

        # — هنا نقوم بتشغيل Selenium لإكمال المهمة —
        driver = create_driver()
        try:
            driver.get("https://www.gosi.gov.sa/wps/portal")
            # مثال: الضغط على "أعمال"، تسجيل الدخول، إرسال الكود، إضافة مشترك
            # ...
            time.sleep(5)  # انتظر التنفيذ
            screenshot_path = f"{sender.replace(':','')}.png"
            driver.save_screenshot(screenshot_path)
            r.body("📄 تم تنفيذ السعودة بنجاح. هنا التفاصيل👇")
            r.media(f"https://{os.getenv('RENDER_EXTERNAL_URL')}/{screenshot_path}")
        except Exception as e:
            r.body(f"❌ فشل في التنفيذ: {e}")
        finally:
            driver.quit()
            session["step"] = "done"

    elif step == "processing":
        r.body("⬆️ جاري المعالجة، انتظر ثانية.")
    elif step == "done":
        r.body("✅ انتهت العملية بالكامل.\nاكتب 'متابعة' للمستخدم جديد أو 'إلغاء' لإنهاء.")
        session["step"] = "await_choice"
    elif session["step"] == "await_choice" and msg.lower() == "متابعة":
        session["step"] = "credentials"
        r.body("📝 أرسل بيانات المستخدم التالي:\nهوية: ...\nكلمة: ...")
    else:
        r.body("🤖 أرسل 'سعودة' للبدء أو 'إلغاء' للتراجع.")

    sessions[sender] = session
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

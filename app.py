from flask import Flask, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os, time, datetime

# ─── تحميل البيانات من ملف env ─────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")

# ─── تهيئة Flask و Twilio ──────────────────────────
app = Flask(__name__)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ─── دالة إرسال واتساب ─────────────────────────────
def send_whatsapp(message, media_path=None):
    data = {
        "from_": f"whatsapp:{TWILIO_PHONE_NUMBER}",
        "to": f"whatsapp:{USER_PHONE_NUMBER}",
        "body": message
    }
    if media_path:
        data["media_url"] = media_path
    twilio_client.messages.create(**data)

# ─── تسجيل الدخول وتنفيذ السعودة ───────────────────
def run_saudah_bot(code=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshot_file = f"screenshots/screenshot_{timestamp}.png"

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

        driver.get("https://www.gosi.gov.sa/GOSIOnline/")
        time.sleep(3)

        # مثال تسجيل الدخول (عدّل حسب موقع التأمينات الفعلي)
        driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "أعمال").click()
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("1234567890")
        driver.find_element(By.ID, "password").send_keys("mypassword")
        driver.find_element(By.ID, "login").click()

        if code:
            time.sleep(2)
            driver.find_element(By.ID, "otp").send_keys(code)
            driver.find_element(By.ID, "submit").click()

        time.sleep(5)
        # تنفيذ خطوات السعودة ...
        # إرسال الوظيفة والراتب

        with open("saudat_log.txt", "a") as log:
            log.write(f"{timestamp} | سعودة تمت بنجاح\n")

        driver.save_screenshot(screenshot_file)
        send_whatsapp("✅ تم تنفيذ السعودة بنجاح. جاري انتظار الطلب القادم...", screenshot_file)

    except WebDriverException as e:
        send_whatsapp(f"❌ خطأ في تنفيذ العملية: {str(e)}")
        try:
            driver.save_screenshot(screenshot_file)
            send_whatsapp("📸 هذا سكرين شوت الخطأ:", screenshot_file)
        except:
            pass
    finally:
        try:
            driver.quit()
        except:
            pass

# ─── نقطة البداية / الصفحة الرئيسية ─────────────────
@app.route("/", methods=["GET"])
def home():
    return "✅ Saudabot شغال بنجاح"

# ─── استقبال رسائل واتساب ───────────────────────────
@app.route("/bot", methods=["POST"])
def bot():
    msg = request.values.get("Body", "").strip()
    if not msg:
        return "❌ لم يتم استقبال رسالة"
    if msg.lower().startswith("كود"):
        code = msg.replace("كود", "").strip()
        run_saudah_bot(code=code)
        return "✅ تم استقبال الكود والتنفيذ"
    elif msg.lower() in ["ابدأ", "سعودة", "تشغيل"]:
        send_whatsapp("🔐 أرسل كود التحقق برسالة تبدأ بكلمة: كود 123456")
        return "🔔 بانتظار كود التحقق"
    else:
        send_whatsapp("❗ أرسل 'سعودة' أو 'ابدأ' لبدء العملية، أو 'كود 123456'")
        return "🟢 تم"

# ─── تشغيل السيرفر ──────────────────────────────────
if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

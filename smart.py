import os
import time
import json
import requests
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from twilio.rest import Client
import openai

# تحميل متغيرات البيئة
TWILIO_SID       = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN     = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM      = os.getenv("TWILIO_PHONE_NUMBER")  # whatsapp:+...
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")

# تهيئة عملاء
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

# صفحة رئيسية
@app.route('/')
def home():
    return 'بوت السعودة الذكي ✅'

# استقبال رسائل واتساب
@app.route('/bot', methods=['POST'])
def bot_webhook():
    # دعم form و json
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    sender = data.get('From') or data.get('from')
    msg = data.get('Body','').strip().lower()

    # تفاعل ذكي
    if msg == 'سعودة':
        reply = '👋 أهلًا! أرسل رقم الهوية وكلمة المرور بهذا الشكل: 1234567890,كلمة_المرور'
        send_whatsapp(sender, reply)
    elif ',' in msg:
        id_, pwd = [x.strip() for x in msg.split(',',1)]
        send_whatsapp(sender, '📩 استلمت بياناتك، جاري تنفيذ السعودة...')
        # استدعاء عملية التسجيل
        requests.post(f"{get_base_url()}/saudabot-login", json={"id": id_, "password": pwd, "sender": sender})
    else:
        send_whatsapp(sender, '❗ أرسل "سعودة" أو البيانات المطلوبة بالشكل الصحيح.')
    return 'OK'

# تنفيذ التسجيل على موقع التأمينات
@app.route('/saudabot-login', methods=['POST'])
def saudabot_login():
    data = request.get_json()
    user_id = data['id']; pwd = data['password']; sender = data['sender']
    # إعداد متصفح
    opts = Options(); opts.add_argument('--headless'); opts.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=opts)
    error_status = None; screenshot = None; analysis = None
    try:
        driver.get('https://www.gosi.gov.sa/GOSIOnline/')
        driver.find_element(By.LINK_TEXT,'تسجيل الدخول').click(); time.sleep(2)
        driver.find_element(By.XPATH,"//button[contains(text(),'أعمال')]").click(); time.sleep(2)
        driver.find_element(By.ID,'username').send_keys(user_id)
        driver.find_element(By.ID,'password').send_keys(pwd)
        driver.find_element(By.ID,'login-button').click(); time.sleep(3)
        # تحقق من نجاح الدخول
        page = driver.page_source
        if any(err in page for err in ['خطأ','غير صحيحة','غير موجود']):
            error_status = 'فشل الدخول'
            # التحليل باستخدام OpenAI
            analysis = analyze_error_text(extract_error_text(driver))
            screenshot = capture_screenshot(driver, user_id)
            send_whatsapp(sender, f"❌ {error_status}: {analysis}")
            send_whatsapp(sender, "📸 هذه لقطة من الموقع:", media=screenshot)
        else:
            error_status = 'نجاح'
            # متابعة الخطوات (إضافة مهنة)
            # مثال افتراضي:
            send_whatsapp(sender, f"✅ تم تسجيل {user_id} بنجاح. اختر: متابعة✅ أو إلغاء❌")
    except Exception as e:
        error_status = 'خطأ غير متوقع'
        analysis = str(e)
        screenshot = capture_screenshot(driver, user_id)
        send_whatsapp(sender, f"❌ {error_status}: {analysis}")
    finally:
        driver.quit()
        # حفظ السجل
        log_record = {'timestamp': time.ctime(), 'id': user_id, 'status': error_status}
        with open('logs.json','a') as f: f.write(json.dumps(log_record)+'\n')
    return jsonify({'status': error_status}), 200

# دوال مساعدة

def capture_screenshot(driver, uid):
    path = f"screenshots/{uid}_{int(time.time())}.png"
    os.makedirs('screenshots', exist_ok=True)
    driver.save_screenshot(path)
    return path


def extract_error_text(driver):
    # استخراج فقرة الخطأ
    texts = driver.find_elements(By.CSS_SELECTOR,'.error-message') or []
    return texts[0].text if texts else driver.title


def analyze_error_text(text):
    # تحليل نص الخطأ عبر GPT
    resp = openai.ChatCompletion.create(
        model='gpt-3.5-turbo', messages=[{'role':'user','content':f'حلل الخطأ التالي من صفحة سعودة: "{text}"'}]
    )
    return resp.choices[0].message.content.strip()


def send_whatsapp(to, body, media=None):
    msg_data = {'from_':f'whatsapp:{TWILIO_FROM}','to':to,'body':body}
    if media:
        msg_data['media_url'] = [upload_media(media)]
    twilio_client.messages.create(**msg_data)


def upload_media(path):
    # رفع مؤقت للصورة (يمكن تعديل)
    # هنا افتراضيًا نحفظها في static folder
    return get_base_url() + '/static/' + os.path.basename(path)


def get_base_url():
    return os.getenv('APP_URL','https://your-render-url.com')

# تشغيل
if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    app.run(host='0.0.0.0', port=port)

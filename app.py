import os from flask import Flask, request from twilio.twiml.messaging_response import MessagingResponse from selenium import webdriver from selenium.webdriver.chrome.options import Options from webdriver_manager.chrome import ChromeDriverManager import openai

تحميل متغيرات البيئة

from dotenv import load_dotenv load_dotenv()

app = Flask(name)

مفاتيح API

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") openai.api_key = OPENAI_API_KEY

IDENTITY = {} CODE_STAGE = {}

@app.route("/", methods=["POST"]) def whatsapp(): incoming_msg = request.values.get('Body', '').strip() from_number = request.values.get('From', '')

response = MessagingResponse()
msg = response.message()

if from_number not in IDENTITY:
    msg.body("👤 من فضلك أرسل رقم الهوية وكلمة المرور مفصولة بمسافة مثل: \n1234567890 secret")
    IDENTITY[from_number] = "pending"
elif IDENTITY[from_number] == "pending":
    if ' ' in incoming_msg:
        id_number, password = incoming_msg.split(' ', 1)
        IDENTITY[from_number] = {'id': id_number, 'password': password}
        msg.body("✅ تم استلام الهوية وكلمة المرور. الآن أرسل كود التحقق الذي وصلك")
        CODE_STAGE[from_number] = "waiting"
    else:
        msg.body("❗الرجاء إرسال الهوية وكلمة المرور بهذا الشكل: \n1234567890 secret")
elif CODE_STAGE.get(from_number) == "waiting":
    code = incoming_msg
    creds = IDENTITY[from_number]
    run_saudabot(creds['id'], creds['password'], code)
    msg.body("✅ تم تنفيذ السعودة بنجاح. ✅\n\n📷 سيتم إرسال صورة إثبات بعد قليل.")
    del IDENTITY[from_number]
    del CODE_STAGE[from_number]
else:
    msg.body("🤖 مرحبًا بك في بوت السعودة. أرسل رقم الهوية وكلمة المرور أولًا.")

return str(response)

def run_saudabot(id_number, password, code): chrome_options = Options() chrome_options.add_argument("--headless") chrome_options.add_argument("--no-sandbox") chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

try:
    driver.get("https://www.gosi.gov.sa/")

    #



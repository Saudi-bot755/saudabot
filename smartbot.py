from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import datetime

app = Flask(__name__)

# الحالة لتتبع المحادثة
session_state = {}

@app.route("/sms", methods=['POST'])
def sms_reply():
    sender = request.form.get('From')
    msg = request.form.get('Body').strip()
    resp = MessagingResponse()

    if sender not in session_state:
        session_state[sender] = {"step": 0}

    step = session_state[sender]["step"]

    if msg.lower() == "سعودة":
        session_state[sender]["step"] = 1
        resp.message("✅ أرسل رقم الهوية وكلمة المرور بالشكل التالي:\n1234567890, password123")
    
    elif step == 1:
        if "," in msg:
            try:
                nid, pwd = [x.strip() for x in msg.split(",", 1)]
                session_state[sender]["nid"] = nid
                session_state[sender]["pwd"] = pwd
                session_state[sender]["step"] = 2

                # تسجّل الطلب في ملف
                with open("requests_log.txt", "a") as f:
                    f.write(f"[{datetime.datetime.now()}] {sender} => {nid}, {pwd}\n")

                resp.message("📨 تم استلام البيانات بنجاح ✅\nالرجاء الانتظار جاري تسجيل الدخول...")

                # تقدر هنا تنادي API داخلي يسوي السعودة أو يربط بـ Selenium
                # مثال: send_to_saudabot(nid, pwd)

            except Exception as e:
                resp.message("❌ يوجد خطأ في التنسيق.\nيرجى كتابة البيانات كالتالي:\n1234567890, password123")
        else:
            resp.message("⚠️ يجب كتابة رقم الهوية وكلمة المرور مفصولة بـ (,)")

    else:
        resp.message("👋 مرحبًا بك في بوت السعودة.\nأرسل كلمة *سعودة* للبدء.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
import time
import json
import datetime
import re
import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
from pathlib import Path
from PIL import Image
import pytesseract
import openai

app = Flask(__name__)
TEMP_STORAGE = {}

# إعداد مفتاح OpenAI من متغير البيئة
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/")
def home():
    return "✅ البوت شغال بنجاح"

@app.route("/bot", methods=["POST"])
def bot_webhook():
    data = request.json
    msg = data.get("body", "").strip()
    sender = data.get("from")

    # التحقق من وجود رسالة
    if not msg:
        return jsonify({"status": "no_message"})

    # الرد على كلمة سعودة
    if msg == "سعودة":
        text = "✉️ أرسل رقم الهوية وكلمة المرور بالشكل التالي:\nالهوية*كلمة_المرور"
        return send_whatsapp(sender, text)

    # إذا كانت الرسالة تحتوي على هوية وكلمة مرور
    if "*" in msg:
        parts = [x.strip() for x in msg.split("*")]
        if len(parts) != 2:
            return send_whatsapp(sender, "❌ تأكد من إدخال الهوية وكلمة المرور بشكل صحيح.")

        national_id, password = parts

        if not national_id.isdigit() or len(national_id) != 10:
            return send_whatsapp(sender, "❌ رقم الهوية غير صحيح.")

        if not validate_password(password):
            return send_whatsapp(sender, "❌ كلمة المرور يجب أن تحتوي على حرف كبير، حرف صغير، رقم، ورمز.")

        TEMP_STORAGE[sender] = {"id": national_id, "password": password, "step": "waiting_code"}
        return send_whatsapp(sender, "🔐 أرسل الآن كود التحقق المكون من 4 أرقام")

    # التحقق من كود التحقق
    elif msg.isdigit() and len(msg) == 4:
        if sender not in TEMP_STORAGE:
            return send_whatsapp(sender, "❌ أرسل أولاً الهوية وكلمة المرور")

        TEMP_STORAGE[sender]["code"] = msg
        TEMP_STORAGE[sender]["step"] = "waiting_birth"
        return send_whatsapp(sender, "📅 أرسل تاريخ ميلادك بالهجري (مثال: 1415/05/20) أو اكتب 'ميلادي' لتحويل التاريخ")

    # تحويل الميلادي إلى هجري
    elif "ميلادي" in msg:
        return send_whatsapp(sender, "❗ أرسل تاريخ ميلادك بالهجري (مثال: 1415/05/20)")

    # إدخال تاريخ الميلاد
    elif re.match(r"^\d{4}/\d{2}/\d{2}$", msg):
        TEMP_STORAGE[sender]["birth"] = msg
        TEMP_STORAGE[sender]["step"] = "completed"
        return send_whatsapp(sender, "✅ تم استلام جميع البيانات بنجاح. يتم الآن تنفيذ عملية السعودة...")

    # رد ذكي باستخدام OpenAI
    else:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "أنت مساعد ذكي يرد على استفسارات السعودة فقط."},
                    {"role": "user", "content": msg},
                ]
            )
            reply = response.choices[0].message.content
            return send_whatsapp(sender, reply)
        except Exception as e:
            return send_whatsapp(sender, f"حدث خطأ أثناء الاتصال بـ OpenAI: {e}")

    return jsonify({"status": "done"})

def validate_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[^A-Za-z0-9]", password)
    )

def send_whatsapp(to, body):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("WHATSAPP_NUMBER")

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=body,
        from_=f"whatsapp:{from_number}",
        to=f"whatsapp:{to}"
    )
    return jsonify({"status": "sent"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", 
    port=int(os.environ.get("PORT", 10000)))

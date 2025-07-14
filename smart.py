import os
import json
import datetime
import re
from flask import Flask, request, jsonify
from twilio.rest import Client
import pytesseract
from PIL import Image
from pathlib import Path
import openai

app = Flask(__name__)
TEMP_STORAGE = {}

@app.route("/")
def home():
    return "✅ البوت شغال بنجاح"

@app.route("/bot", methods=["POST"])
def bot_webhook():
    if request.content_type != "application/json":
        return "Unsupported Media Type", 415

    data = request.get_json(force=True)
    msg = data.get("body", "").strip()
    sender = data.get("from")

    # التحقق من التنسيق: رقم الهوية * كلمة المرور
    if "*" in msg:
        parts = [x.strip() for x in msg.split("*")]
        if len(parts) != 2:
            return send_whatsapp(sender, "❌ التنسيق غير صحيح. ارسل الرقم وكلمة المرور بهذا الشكل: 1234567890, password123")

        national_id, password = parts

        if not national_id.isdigit() or len(national_id) != 10:
            return send_whatsapp(sender, "❌ رقم الهوية يجب أن يكون 10 أرقام.")

        if not validate_password(password):
            return send_whatsapp(sender, "❌ كلمة المرور غير قوية. يجب أن تحتوي على حرف كبير وحروف صغيرة وأرقام.")

        TEMP_STORAGE[sender] = {
            "id": national_id,
            "password": password,
            "step": "waiting_code"
        }

        return send_whatsapp(sender, "🔐 تم حفظ البيانات. أرسل كود التحقق الآن.")

    # التحقق من كود التحقق
    elif msg.isdigit() and len(msg) == 4:
        if sender not in TEMP_STORAGE or TEMP_STORAGE[sender]["step"] != "waiting_code":
            return send_whatsapp(sender, "❗ أرسل الهوية وكلمة المرور أولاً.")

        TEMP_STORAGE[sender]["code"] = msg
        TEMP_STORAGE[sender]["step"] = "waiting_birth"

        return send_whatsapp(sender, "📅 أرسل تاريخ الميلاد الهجري بصيغة: 1410/01/01")

    # التحقق من تاريخ الميلاد الهجري
    elif re.match(r"^14\d{2}/\d{2}/\d{2}$", msg):
        if sender not in TEMP_STORAGE or TEMP_STORAGE[sender]["step"] != "waiting_birth":
            return send_whatsapp(sender, "❗ أرسل كود التحقق أولاً.")

        TEMP_STORAGE[sender]["birth_date"] = msg
        TEMP_STORAGE[sender]["step"] = "processing"

        # استكمال التسجيل هنا...
        return send_whatsapp(sender, "🛠️ جارٍ التسجيل في التأمينات...")

    else:
        # الذكاء الاصطناعي للردود العامة
        response = ask_openai(msg)
        return send_whatsapp(sender, response)

    return jsonify({"status": "done"})

def send_whatsapp(to, message):
    print(f"[رسالة إلى {to}]: {message}")
    return jsonify({"status": "sent"})

def validate_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
    )

def ask_openai(prompt):
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي لبوت سعودة."},
                {"role": "user", "content": prompt},
            ]
        )
        return chat.choices[0].message.content
    except Exception as e:
        return "⚠️ حدث خطأ في الاتصال بالذكاء الاصطناعي."
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

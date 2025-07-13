from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import json
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "بوت السعودة يعمل ✅"

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip().lower()
    sender = request.values.get("From", "")

    resp = MessagingResponse()
    msg = resp.message()

    if "سعوده" in incoming_msg:
        msg.body("👋 أهلًا بك! الرجاء إرسال رقم الهوية وكلمة المرور بهذة الصيغة:
1234567890, كلمة_المرور")
    elif "," in incoming_msg:
        try:
            national_id, password = [x.strip() for x in incoming_msg.split(",")]
            data = {
                "id": national_id,
                "password": password,
                "sender": sender
            }
            r = requests.post("http://localhost:7000/start", json=data)
            if r.status_code == 200:
                msg.body("📩 تم استلام البيانات، وجاري تنفيذ عملية السعودة...")
            else:
                msg.body("⚠️ لم يتم استقبال البيانات بشكل صحيح، حاول لاحقًا.")
        except Exception as e:
            msg.body(f"❌ خطأ في معالجة البيانات: {e}")
    else:
        msg.body("❗ أرسل كلمة "سعوده" للبدء.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
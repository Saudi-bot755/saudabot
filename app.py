from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def bot():
    msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()

    if "سعودة" in msg:
        resp.message("أرسل رقم الهوية وكلمة المرور.")
    elif msg.startswith("هوية:") and "كلمة:" in msg:
        resp.message("جاري تسجيل الدخول للموقع...")
    elif msg == "متابعة":
        resp.message("تمت المتابعة ✅")
    elif msg == "الغاء":
        resp.message("تم إلغاء العملية ❌")
    else:
        resp.message("أرسل كلمة سعودة للبدء.")

    return str(resp)

app.run(host="0.0.0.0", port=5000)

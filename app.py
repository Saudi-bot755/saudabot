import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

# إعداد خيارات المتصفح بدون واجهة
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# تشغيل المتصفح
driver = webdriver.Chrome(options=chrome_options)

try:
    # الدخول إلى موقع التأمينات
    driver.get("https://www.gosi.gov.sa/GOSIOnline/")

    # الانتظار حتى يظهر زر "النفاذ الوطني"
    wait = WebDriverWait(driver, 20)
    element = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "النفاذ الوطني")))
    element.click()

    # في هذا المكان يمكنك إكمال خطوات تسجيل الدخول لاحقًا

    print("✅ تم الضغط على النفاذ الوطني بنجاح.")

except Exception as e:
    print("❌ حدث خطأ:", str(e))

finally:
    # إغلاق المتصفح
    driver.quit()	


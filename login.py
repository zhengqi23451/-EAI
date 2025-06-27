import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pytesseract
from PIL import Image
import base64
import io
import cv2
import numpy as np


expected_style = {
    'width': '320px', 'height': '48px', 'color': 'rgba(60, 141, 188, 1)', 'border-radius': '4px'
}

# 初始化 WebDriver
driver = webdriver.Chrome()
url = "http://192.168.2.130:9529/#/login"
driver.get(url)
driver.maximize_window()
time.sleep(3)

try:
    # 获取验证码图片
    captcha_img = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[3]/div/img')
    captcha_data = captcha_img.get_attribute("src").split(",")[1]
    image_bytes = base64.b64decode(captcha_data)

    # 预处理图片
    # 转换为 OpenCV 格式
    img = cv2.cvtColor(np.array(Image.open(io.BytesIO(image_bytes))), cv2.COLOR_RGB2GRAY)
    # 二值化
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # 降噪
    img = cv2.medianBlur(img, 3)
    processed_img = img
    cv2.imwrite("processed_captcha.png", processed_img)  # 保存处理后的图片
    time.sleep(1)
    # OCR 识别
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    custom_config = r'--psm 8 --oem 3'  # 单行识别模式
    text = pytesseract.image_to_string(processed_img, config=custom_config).strip()
    print("OCR 识别结果:", text)
    time.sleep(1)
    # 获取登录按钮样式
    login_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/form/div[2]/button')
    width = login_button.value_of_css_property('width')
    height = login_button.value_of_css_property("height")
    color = login_button.value_of_css_property("background-color")
    radius = login_button.value_of_css_property('border-radius')
    actual_style = {'width': width, 'height': height, 'color': color, 'border-radius': radius}
    print("按钮实际样式", actual_style)

    # 验证样式是否一致
    assert actual_style == expected_style, "样式不一致"
    print("样式一致！")

    # 输入账号、密码、验证码
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[1]/div/div[1]/input').send_keys("JH-00001")
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[2]/div/div/input').send_keys("1231234567")
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[3]/div/div/input').send_keys(text)
    time.sleep(1)

    # 点击登录
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div/form/div[2]/button').click()
    time.sleep(5)

    # 验证登录是否成功
    assert "首页" in driver.page_source, "登录失败，页面内容不匹配"
    print("登录成功！")

except Exception as e:
    print(f"测试失败：{e}")
#finally:
    #driver.quit()


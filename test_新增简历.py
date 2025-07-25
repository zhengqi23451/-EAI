import ast
import os
import time
import random
import allure
import pandas as pd
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from selenium.webdriver.chrome.options import Options
import base64
import io
import cv2
import numpy as np

#pytestmark = pytest.mark.skip(reason="暂时跳过此文件测试")


# 设置Tesseract路径（根据实际安装位置调整）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
df=pd.read_csv(r"C:\Users\Administrator\Desktop\test\address.csv")
row=df.loc[0, ['url', 'data']]
url = row['url']
data_str = row['data']
data = ast.literal_eval(data_str)
def highlight_element(driver, element):
    """高亮显示元素"""
    driver.execute_script("arguments[0].style.border='6px solid red';", element)
def reset_element(driver, element):
    """恢复元素样式"""
    driver.execute_script("arguments[0].style.border='';", element)
def to_rgb(color):
    """将各种颜色格式统一转换为 rgb(r, g, b) 格式"""
    if not color:
        return color

    if color.startswith("rgba"):
        # 提取 rgba 中的 rgb 部分，去除 alpha 通道
        parts = color.split(",")
        return f"rgb({parts[0][5:]},{parts[1]},{parts[2]})"
    elif color.startswith("rgb"):
        # 直接返回 rgb 格式
        return color
    elif color.startswith("#"):
        # 将十六进制颜色值转换为 rgb
        hex_color = color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgb({r}, {g}, {b})"
    else:
        return color  # 无法识别的格式原样返回


@pytest.fixture(scope="module", params=data)
def resolution(request):
    """分辨率fixture"""
    return request.param

@pytest.fixture(scope="module",params=["chrome","msedge" ,"360se", "360chrome"])
def driver(request,resolution):
    """初始化 WebDriver"""
    browser = request.param
    if browser == "chrome":
        options = Options()
        options.binary_location =r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
        driver = webdriver.Chrome(service=service,options=options)
    elif browser == "msedge":
        driver = webdriver.Edge()

    elif browser == "360se":
        # 360安全浏览器
        options = Options()
        options.binary_location =r"C:\Users\Administrator\AppData\Roaming\secoresdk\360se6\Application\360se.exe"
        service = Service(executable_path=r"C:\Users\Administrator\AppData\Roaming\secoresdk\360se6\Application\chromedriver.exe")
        driver = webdriver.Chrome(service=service,options=options)
    elif browser == "360chrome":
        # 360极速浏览器
        options = Options()
        options.binary_location =r"C:\Users\Administrator\AppData\Local\360Chrome\Chrome\Application\360chrome.exe"
        service = Service(executable_path=r"C:\Users\Administrator\AppData\Local\360Chrome\Chrome\Application\chromedriver.exe")
        driver = webdriver.Chrome(service=service,options=options)
    else:
        raise ValueError("Unsupported browser")
    width, height = resolution
    driver.set_window_size(width, height)
    yield driver
    driver.quit()


@pytest.fixture(scope="module")
def login(driver):
    """登录系统"""
    # 访问登录页
    driver.get(url)
    wait = WebDriverWait(driver, 20)
    try:
        # 验证码处理
        captcha_img = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[3]/div/img')))
        captcha_data = captcha_img.get_attribute("src").split(",")[1]
        image_bytes = base64.b64decode(captcha_data)

        img = cv2.cvtColor(np.array(Image.open(io.BytesIO(image_bytes))), cv2.COLOR_RGB2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        img = cv2.medianBlur(img, 3)

        text = pytesseract.image_to_string(img, config=r'--psm 8 --oem 3').strip()

        # 输入凭据
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[1]/div/div[1]/input'))).send_keys("JH-00001")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[2]/div/div/input'))).send_keys("1231234567")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/form/div[2]/div[3]/div/div/input'))).send_keys(text)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/form/div[2]/button'))).click()

        # 验证登录
        time.sleep(5)
        try:
            error = driver.find_element(By.CSS_SELECTOR, ".el-message__content").text
            if "验证码错误" in error:
                pytest.fail("验证码识别错误")
        except:
            pass
    except Exception as e:
        # 截图并附加到 Allure 报告
        allure.attach(driver.get_screenshot_as_png(), name="登录失败截图", attachment_type=allure.attachment_type.PNG)
        raise e


#进入新增简历界面
@pytest.fixture(scope="module")
def navigate_to_addjl(driver, login):
    """导航到审批页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        # 点击协同办公设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/ul/li[text()=" 人力资源 "]'))).click()
        if width==1366:
            #点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        #点击人力资源管理
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]//li//span[text()="人力资源管理"]'))).click()
        #人力资源工作
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]//li//span[text()="人力资源工作"]'))).click()
        #点击新增简历输入
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]//li/ul//span[text()="新增简历输入"]'))).click()
        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//div[@class="my-grid-box"]//span[text()="应聘资料输入"]')))
        if title.text !="应聘资料输入":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航到应聘资料输入页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,title)
        assert title.text == "应聘资料输入"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@pytest.mark.skip
@allure.feature("人力资源")
@allure.story("新简历输入")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_addjl):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 10)

    # 定义预期样式
    expected_styles = {
        # 关闭按钮样式
        'close_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 保存按钮样式
        'save_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 提交按钮样式
        'submit_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 事件缓急选择器样式
        'input_select': {
            'height': '24px',
            'border': '1px solid rgb(220, 223, 230)',
            'border-radius': '2px'
        }
    }
    time.sleep(5)
    try:
        # 关闭按钮样式
        close_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]')))
        actual_styles = {
            'background-color': to_rgb(close_button.value_of_css_property('background-color')),
            'color':to_rgb(close_button.value_of_css_property('color')),
            'border-radius': close_button.value_of_css_property('border-radius'),
            'width': close_button.value_of_css_property('width'),
            'height': close_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['close_button']:
            highlight_element(driver, close_button)
            allure.attach(driver.get_screenshot_as_png(), name="关闭按钮样式错误高亮截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, close_button)
        assert actual_styles == expected_styles['close_button'], f"关闭按钮样式不匹配: {actual_styles}"

        # 保存按钮样式
        save_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]')))
        actual_styles = {
            'background-color': to_rgb(save_button.value_of_css_property('background-color')),
            'color': to_rgb(save_button.value_of_css_property('color')),
            'border-radius': save_button.value_of_css_property('border-radius'),
            'width': save_button.value_of_css_property('width'),
            'height': save_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['save_button']:
            highlight_element(driver, save_button)
            allure.attach(driver.get_screenshot_as_png(), name="保存按钮样式错误高亮截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, save_button)
        assert actual_styles == expected_styles['save_button'], f"保存按钮样式不匹配: {actual_styles}"

        # 提交按钮样式
        submit_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[3]')))
        actual_styles = {
            'background-color': to_rgb(submit_button.value_of_css_property('background-color')),
            'color': to_rgb(submit_button.value_of_css_property('color')),
            'border-radius': submit_button.value_of_css_property('border-radius'),
            'width': submit_button.value_of_css_property('width'),
            'height': submit_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['submit_button']:
            highlight_element(driver, submit_button)
            allure.attach(driver.get_screenshot_as_png(), name="提交按钮样式错误高亮截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, submit_button)
        assert actual_styles == expected_styles['submit_button'], f"提交按钮样式不匹配: {actual_styles}"

    except Exception as e:
        # 截图并附加到 Allure 报告
        #allure.attach(driver.get_screenshot_as_png(), name="样式不匹配截图", attachment_type=allure.attachment_type.PNG)
        raise e


@allure.feature("人力资源")
@allure.story("新简历输入")
@allure.description("保存简历")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_addjl_save(driver,navigate_to_addjl):
    wait = WebDriverWait(driver, 10)
    try:
        #姓名
        wait.until(EC.presence_of_element_located((By.XPATH,"//div[contains(@class,'el-row')]//div[label[@for='name']]//input"))).send_keys("技术总监招聘")
        #身份证
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='id_card']]//input"))).send_keys("340222199209213153")
        #户口地址
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='hukou_address']]//input"))).send_keys("地球村")
        #民族
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='nation']]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='汉族']"))).click()
        #身高体重
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='height']]//input"))).send_keys(160)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='weight']]//input"))).send_keys(50)
        #婚姻
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='marriage']]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='未婚']"))).click()
        #政治面貌
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='political_status']]//input"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='群众']"))).click()
        #健康
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='health']]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='良好']"))).click()
        #血型
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='blood_type']]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='A型']"))).click()
        #公益献血
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='public_welfare']]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='暂无考虑']"))).click()
        #目标月薪
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='salary']]//input"))).send_keys(3000)
        #现住地址
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='current_address']]//input"))).send_keys("地球")
        #学历
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='education']]//input"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//span[text()='大专']"))).click()
        #专业
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='speciality']]//input"))).send_keys("土木工程")
        #毕业时间
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='edu_end_time']]//input"))).send_keys("2025-05-01")
        #毕业学校
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='school']]//input"))).send_keys("人文学院")
        #手机号
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='mobile']]//input"))).send_keys("13330693892")
        #紧急联系人
        #称谓
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='urgent_cont[0].appellation']]//input"))).send_keys("父亲")
        #姓名
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='urgent_cont[0].urgent_name']]//input"))).send_keys("father")
        #手机号
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='urgent_cont[0].urgent_mobile']]//input"))).send_keys("13918506585")

        #选择图片
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='grid-col flex-x-center el-col el-col-24']//span"))).click()
        time.sleep(20)

        # 选择普件
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='incident']]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='top-start']//li[span[text()='普件']]"))).click()
        # 点击提交
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='form-bottom-bar flex flex-x-center']/button[span[text()='提交']]"))).click()

        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class,'el-message')]/p[contains(text(),'保存成功')]")))
        if title!="保存成功":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="保存失败高亮截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "保存成功"

    except Exception as e:
        # 截图并附加到 Allure 报告
        #allure.attach(driver.get_screenshot_as_png(), name="保存失败截图", attachment_type=allure.attachment_type.PNG)
        raise e



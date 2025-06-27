import datetime
import time
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image
import base64
import io
import cv2
import numpy as np
from selenium.webdriver.common.keys import Keys


# 设置Tesseract路径（根据实际安装位置调整）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



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
data=[(2560,1600),(1920,1200),(2560,1440),(1920,1080),(1366,768)]
@pytest.fixture(scope="module", params=[(1920,1080),(1366,768)])
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
    driver.get("http://192.168.2.42:9529/#/login")
    wait = WebDriverWait(driver, 20)

    try:
        # 验证码处理
        captcha_img = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div[@class="login-container"]/div[@class="con-in"]/form/div[2]/div[@class="el-form-item is-required"]/div[@class="el-form-item__content"]/img[@class="cap_img"]')))
        captcha_data = captcha_img.get_attribute("src").split(",")[1]
        image_bytes = base64.b64decode(captcha_data)

        img = cv2.cvtColor(np.array(Image.open(io.BytesIO(image_bytes))), cv2.COLOR_RGB2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        img = cv2.medianBlur(img, 3)

        text = pytesseract.image_to_string(img, config=r'--psm 8 --oem 3').strip()

        # 输入凭据
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[@class="login-container"]/div[@class="con-in"]/form/div[2]/div[1]/div[@class="el-form-item__content"]/div[@class="el-input"]/input'))).send_keys("JH-00001")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[@class="login-container"]/div[@class="con-in"]/form/div[2]/div[2]/div[@class="el-form-item__content"]/div[@class="el-input"]/input'))).send_keys("1231234567")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[@class="login-container"]/div[@class="con-in"]/form/div[2]/div[3]/div[@class="el-form-item__content"]/div[@class="el-input"]/input'))).send_keys(text)
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
        allure.attach(driver.get_screenshot_as_png(), name="登录失败截图",
                      attachment_type=allure.attachment_type.PNG)
        raise e


@pytest.fixture(scope="module")
def navigate_to_salary_allocation(driver, login):
    """导航到技能测评页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        # 点击设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//ul[@class="menu-wrap el-menu--horizontal el-menu"]/li[contains(@class, "setting-menu")]/i'))).click()
        if width==1366:
            #点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        #点击人力资源设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/div/span'))).click()
        #点击薪资管理设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div/li/div/span[text()="薪资管理设置"]'))).click()
        #点击薪资分类管理
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div/li/ul/div/a/li/span[text()="薪资分类管理"]'))).click()
        #点击薪资配置设置
        wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='el-card__body']//span[text()='薪资配置设置']"))).click()
        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section//div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/span[@class="title"]')))
        if title.text!="薪资配置设置" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航薪资配置设置页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "薪资配置设置"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资分类管理-薪资配置设置")
@allure.description("设置薪资配置")
def test_set(driver,navigate_to_salary_allocation):
    wait = WebDriverWait(driver, 20)
    try:
        #点击薪资设置按钮
        set=wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section//div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button/span[text()="薪资设置"]')))
        set.click()
        #点击社保缴纳标准
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//form//div[label[@for='social_security']]/div[@class='el-form-item__content']//input"))).click()
        #选择C
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']/div[contains(@class,'el-scrollbar')]/div[1]//ul/li/span[text()='C']"))).click()
        time.sleep(0.5)
        #点击保存
        save=wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='薪资配置']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--success')]")))
        save.click()
        #提示
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "设置成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="设置薪资配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "设置成功"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资分类管理-薪资配置设置")
@allure.description("编辑薪资配置")
def test_modify(driver,navigate_to_salary_allocation):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击编辑
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-primary")]'))).click()
        #点击保存
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='薪资配置']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--success')]"))).click()
        # 提示
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "设置成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资配置修改失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "设置成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资分类管理-薪资配置设置")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_salary_allocation):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)

    # 定义预期样式
    expected_styles = {
        # 薪资设置按钮样式
        'set_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        #编辑按钮样式
        'modify_button':{
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        # 删除按钮样式
        'delete_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(245, 108, 108)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        }
    }
    time.sleep(1)

    try:
        # 测试新增按钮样式
        set_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section//div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button')))
        actual_styles = {
            'background-color': to_rgb(set_button.value_of_css_property('background-color')),
            'color': to_rgb(set_button.value_of_css_property('color')),
            'border-radius': set_button.value_of_css_property('border-radius'),
            'width': set_button.value_of_css_property('width'),
            'height': set_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['set_button']:
            highlight_element(driver,set_button)
            allure.attach(driver.get_screenshot_as_png(), name="薪资设置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,set_button)
        assert actual_styles == expected_styles['set_button'], f"薪资设置按钮样式不匹配: {actual_styles}"

        #编辑按钮样式
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-primary")]')))
        driver.execute_script("arguments[0].scrollIntoView();", modify_button)
        actual_styles = {
            'background-color': to_rgb(modify_button.value_of_css_property('background-color')),
            'color': to_rgb(modify_button.value_of_css_property('color')),
            'border-radius': modify_button.value_of_css_property('border-radius'),
            'width': modify_button.value_of_css_property('width'),
            'height': modify_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['modify_button']:
            highlight_element(driver,modify_button)
            allure.attach(driver.get_screenshot_as_png(), name="编辑按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify_button)
        assert actual_styles == expected_styles['modify_button'], f"编辑按钮样式不匹配: {actual_styles}"


        #删除按钮样式
        delete_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
        time.sleep(5)
        actual_styles = {
            'background-color': to_rgb(delete_button.value_of_css_property('background-color')),
            'color': to_rgb(delete_button.value_of_css_property('color')),
            'border-radius': delete_button.value_of_css_property('border-radius'),
            'width': delete_button.value_of_css_property('width'),
            'height': delete_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['delete_button']:
            highlight_element(driver,delete_button)
            allure.attach(driver.get_screenshot_as_png(), name="删除按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, delete_button)
        assert actual_styles == expected_styles['delete_button'], f"删除按钮样式不匹配: {actual_styles}"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资分类管理-薪资配置设置")
@allure.description("删除薪资配置")
def test_delete(driver,navigate_to_salary_allocation):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #获取当前记录数量
        m=wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="app"]/div/div[@class="main-container"]/section//div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/span[@class="result"]/span')))

        a=int(m.text)
        #点击删除
        delete=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", delete)

        delete.click()
        #点击确认
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-message-box']/div[@class='el-message-box__btns']/button[contains(@class,'el-button--primary')]"))).click()
        #当前记录数量
        time.sleep(0.5)
        b=int(m.text)

        if (a-b)!=1:
            highlight_element(driver, m)
            allure.attach(driver.get_screenshot_as_png(), name="薪资配置删除失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, m)
        assert (a-b)==1
    except Exception as e:
        raise e



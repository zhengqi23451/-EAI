import datetime
import time
from operator import contains

import pandas as pd
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

df=pd.read_csv(r"C:\Users\Administrator\Desktop\test\address.csv")
url = df.loc[0, 'url']
data=df.loc[0,'data']
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
def navigate_to_file_management(driver, login):
    """导航到档案管理设置页面"""
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
        #点击人力资源设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div[4]/li/div/span[text()="人力资源设置"]'))).click()
        #点击档案管理设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div[4]/li/ul/div/a/li/span[text()="档案管理设置"]'))).click()
        # 验证页面加载
        time.sleep(2)
        title = driver.current_url
        if title!="http://192.168.2.42:9529/#/sys/hr/manage/archives" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航档案管理设置页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title == "http://192.168.2.42:9529/#/sys/hr/manage/archives"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("新增档案文件")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_add_file(driver,navigate_to_file_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, "//button/span[text()='新增']")))
        add.click()
        #输入档案文件名称
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']/form/div[label[@for='archives_name']]/div[@class='el-form-item__content']//input"))).send_keys("test")
        #输入档案文件标识
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']/form/div[label[@for='file_type']]/div[@class='el-form-item__content']//input"))).send_keys("test")
        #点击保存
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='新增档案文件']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--success')]"))).click()
        #提示
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text == "新增成功":
            print("测试通过：新增成功")
        elif "Integrity constraint violation: 1062 Duplicate entry" in text.text:
            print("测试通过：正确提示重复数据错误")
            wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@aria-label='新增档案文件']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--primary')]"))).click()
            time.sleep(2)
        else:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增档案文件失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
            pytest.fail(f"新增失败，提示信息为：{text.text}")

    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("新增档案柜")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_add_filing_cabinet(driver,navigate_to_file_management):
    wait = WebDriverWait(driver, 60)
    time.sleep(3)
    try:
        #点击新增档案柜按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section//div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/button')))
        add.click()
        #输入档案柜名称
        wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='el-dialog__body']/form/div[label[@for='cabinet_name']]/div[@class='el-form-item__content']//input"))).send_keys("test")
        #输入档案柜编号
        wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='el-dialog__body']/form/div[label[@for='cabinet_code']]/div[@class='el-form-item__content']//input"))).send_keys(1)
        #输入档案柜位置
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']/form/div[label[@for='cabinet_address']]/div[@class='el-form-item__content']//input"))).send_keys('t')

        #点击保存
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='新增档案柜']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--success')]"))).click()
        #提示
        text = wait.until(EC.element_to_be_clickable((By.XPATH, '//p[@class="el-message__content"]')))

        if text.text == "新增成功":
            print("测试通过：新增成功")
        elif "Integrity constraint violation: 1062 Duplicate entry" in text.text:
            print("测试通过：正确提示重复数据错误")
            # 点击关闭
            wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@aria-label='新增档案柜']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--primary')]"))).click()
            time.sleep(2)
        else:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增档案柜失败截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
            pytest.fail(f"新增失败，提示信息为：{text.text}")

    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("修改档案文件")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_modify_file(driver,navigate_to_file_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击test文件
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//div[@class="el-card__body"]//span[text()="test"]'))).click()
        #点击修改
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,"//button/span[text()='修改']"))).click()
        #点击保存
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='修改档案文件']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--success')]"))).click()
        # 提示
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改档案文件失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
        time.sleep(5)
    except Exception as e:
        raise e



@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("修改档案柜")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_modify_cabinet(driver,navigate_to_file_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击编辑
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[3]/td[contains(@class,"col--last")]//button/span[text()="编辑"]'))).click()
        #点击保存
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='修改档案柜']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--success')]"))).click()
        # 提示
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="档案柜修改失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
        time.sleep(5)
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("分配档案员")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_allocation(driver,navigate_to_file_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击分配档案员
        wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[3]/td[contains(@class,"col--last")]//button/span[text()="分配档案员"]'))).click()
        #点击选择
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//tbody/tr[1]/td[2]//span/span"))).click()
        #点击确认
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//form/div/button/span[text()='确认']"))).click()
        # 提示
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="分配档案员失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
        time.sleep(5)
    except Exception as e:
        raise e



@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("档案设置保存")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_save(driver,navigate_to_file_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #打钩
        wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[3]/td[1]//span/span'))).click()

        #点击档案设置保存
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button/span[text()='档案设置保存']"))).click()
        # 提示
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "档案设置成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="档案设置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "档案设置成功"
        time.sleep(5)
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("人力资源设置")
@allure.story("档案管理设置")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_file_management):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    # 定义预期样式
    expected_styles = {
        # 新增按钮样式
        'add_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        #修改文件按钮样式
        'modify_file_button':{
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 新增档案柜按钮样式
        'add_filing_cabinet_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 修改档案柜按钮样式
        'modify_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        # 分配档案员按钮样式
        'allocation_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        # 档案设置保存按钮样式
        'save_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '88px',
            'height': '28px'
        }
    }
    time.sleep(1)

    try:
        # 测试新增按钮样式
        add_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="el-card__header"]//button[contains(@class,"el-button--success")]')))
        actual_styles = {
            'background-color': to_rgb(add_button.value_of_css_property('background-color')),
            'color': to_rgb(add_button.value_of_css_property('color')),
            'border-radius': add_button.value_of_css_property('border-radius'),
            'width': add_button.value_of_css_property('width'),
            'height': add_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['add_button']:
            highlight_element(driver,add_button)
            allure.attach(driver.get_screenshot_as_png(), name="新增按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,add_button)
        assert actual_styles == expected_styles['add_button'], f"新增按钮样式不匹配: {actual_styles}"

        # 修改文件按钮样式
        modify_file_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="el-card__header"]//button[contains(@class,"el-button--primary")]')))
        actual_styles = {
            'background-color': to_rgb(modify_file_button.value_of_css_property('background-color')),
            'color': to_rgb(modify_file_button.value_of_css_property('color')),
            'border-radius': modify_file_button.value_of_css_property('border-radius'),
            'width': modify_file_button.value_of_css_property('width'),
            'height': modify_file_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['modify_file_button']:
            highlight_element(driver,modify_file_button)
            allure.attach(driver.get_screenshot_as_png(), name="修改档案文件按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,modify_file_button)
        assert actual_styles == expected_styles['modify_file_button'], f"修改档案文件按钮样式不匹配: {actual_styles}"


        # 新增档案柜按钮样式
        add_filing_cabinet_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section//div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/button')))
        driver.execute_script("arguments[0].scrollIntoView(true);", add_filing_cabinet_button)
        time.sleep(3)
        actual_styles = {
            'background-color': to_rgb(add_filing_cabinet_button.value_of_css_property('background-color')),
            'color': to_rgb(add_filing_cabinet_button.value_of_css_property('color')),
            'border-radius': add_filing_cabinet_button.value_of_css_property('border-radius'),
            'width': add_filing_cabinet_button.value_of_css_property('width'),
            'height': add_filing_cabinet_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['add_filing_cabinet_button']:
            highlight_element(driver,add_filing_cabinet_button)
            allure.attach(driver.get_screenshot_as_png(), name="新增档案柜按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, add_filing_cabinet_button)
        assert actual_styles == expected_styles['add_filing_cabinet_button'], f"新增档案柜按钮样式不匹配: {actual_styles}"


        #编辑按钮样式
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[3]/td[contains(@class,"col--last")]//button[1]')))
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


        # 分配档案员按钮样式
        allocation_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[3]/td[contains(@class,"col--last")]//button[1]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", allocation_button)
        time.sleep(3)
        actual_styles = {
            'background-color': to_rgb(allocation_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_button.value_of_css_property('color')),
            'border-radius': allocation_button.value_of_css_property('border-radius'),
            'width': allocation_button.value_of_css_property('width'),
            'height': allocation_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_button']:
            highlight_element(driver,allocation_button)
            allure.attach(driver.get_screenshot_as_png(), name="分配档案员按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, allocation_button)
        assert actual_styles == expected_styles['allocation_button'], f"分配档案员按钮样式不匹配: {actual_styles}"

        # 档案设置保存按钮样式
        save_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class, 'flex') and contains(@class, 'flex-x-center') and contains(@class, 'flex-y-center')]/button")))
        driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
        time.sleep(3)
        actual_styles = {
            'background-color': to_rgb(save_button.value_of_css_property('background-color')),
            'color': to_rgb(save_button.value_of_css_property('color')),
            'border-radius': save_button.value_of_css_property('border-radius'),
            'width': save_button.value_of_css_property('width'),
            'height': save_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['save_button']:
            highlight_element(driver,save_button)
            allure.attach(driver.get_screenshot_as_png(), name="档案设置保存按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, save_button)
        assert actual_styles == expected_styles['save_button'], f"档案设置保存按钮样式不匹配: {actual_styles}"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

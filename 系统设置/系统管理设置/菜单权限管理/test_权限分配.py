import ast
import datetime
import time
import typing

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
def navigate(driver, login):
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        # 点击设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//ul[@class="menu-wrap el-menu--horizontal el-menu"]/li[contains(@class, "setting-menu")]/i'))).click()
        if width==1366:
            #点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        #点击系统管理设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="系统管理设置"]'))).click()
        #点击菜单权限设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="菜单权限管理"]'))).click()
        #点击权限分配
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="权限分配"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="app-container"]//div[text()="职务权限分配表"]')))
        if title.text!="职务权限分配表" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航公共表单页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "职务权限分配表"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("权限分配")
@allure.description("迁进迁出，对职务分组")
def test_move(driver,navigate):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #选择分组
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="role-group"]//li[last()]'))).click()
        #点击迁进迁出按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="el-card__header"]//button[span[text()="迁进迁出"]]')))
        driver.execute_script("arguments[0].click();", add)

        #点击确认按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="职务分组（迁进迁出）"]//div[@class="el-dialog__footer"]//button[span[text()="确认"]]'))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-message-box']/div[@class='el-message-box__btns']/button[contains(@class,'el-button--primary')]"))).click()
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "操作分组成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="迁进迁出职务分组失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "操作分组成功"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("权限分配")
@allure.description("权限保存")
def test_save(driver,navigate):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #选择分组
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="role-group"]//li[last()]'))).click()
        time.sleep(0.5)
        #点击权限保存按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="btn-box flex flex-x-center"]/button[span[text()="权限保存"]]')))
        driver.execute_script("arguments[0].click();", add)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "权限分配成功！":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="权限分配失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "权限分配成功！"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("权限分配")
@allure.description("样式比较")
def test_file_style(driver, navigate):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    # 定义预期样式
    expected_styles = {
        # 折叠按钮样式
        'fold_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 迁进迁出按钮样式
        'move_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 权限保存按钮样式
        'save_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        }
    }
    time.sleep(1)

    try:
        # 测试折叠按钮样式
        fold_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@id="app"]//div[@class="el-card__header"]//button[1]')))
        actual_styles = {
            'background-color': to_rgb(fold_button.value_of_css_property('background-color')),
            'color': to_rgb(fold_button.value_of_css_property('color')),
            'border-radius': fold_button.value_of_css_property('border-radius'),
            'width': fold_button.value_of_css_property('width'),
            'height': fold_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['fold_button']:
            highlight_element(driver, fold_button)
            allure.attach(driver.get_screenshot_as_png(), name="折叠按钮样式匹配失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, fold_button)
        assert actual_styles == expected_styles['fold_button'], f"查询按钮样式不匹配: {actual_styles}"

        time.sleep(1)

        # 测试迁进迁出按钮样式
        move_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@id="app"]//div[@class="el-card__header"]//button[span[text()="迁进迁出"]]')))
        actual_styles = {
            'background-color': to_rgb(move_button.value_of_css_property('background-color')),
            'color': to_rgb(move_button.value_of_css_property('color')),
            'border-radius': move_button.value_of_css_property('border-radius'),
            'width': move_button.value_of_css_property('width'),
            'height': move_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['move_button']:
            highlight_element(driver, move_button)
            allure.attach(driver.get_screenshot_as_png(), name="迁进迁出按钮样式匹配失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, move_button)
        assert actual_styles == expected_styles['move_button'], f"迁进迁出按钮样式不匹配: {actual_styles}"


        # 测试权限保存按钮样式
        save_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@id="app"]//div[@class="btn-box flex flex-x-center"]/button[span[text()="权限保存"]]')))
        actual_styles = {
            'background-color': to_rgb(save_button.value_of_css_property('background-color')),
            'color': to_rgb(save_button.value_of_css_property('color')),
            'border-radius': save_button.value_of_css_property('border-radius'),
            'width': save_button.value_of_css_property('width'),
            'height': save_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['save_button']:
            highlight_element(driver,save_button)
            allure.attach(driver.get_screenshot_as_png(), name="权限保存按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,save_button)
        assert actual_styles == expected_styles['save_button'], f"权限保存按钮样式不匹配: {actual_styles}"


    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

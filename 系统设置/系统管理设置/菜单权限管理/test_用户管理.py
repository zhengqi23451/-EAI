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
def navigate_to_user_management(driver, login):
    """导航到资源管理页面"""
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
        #点击用户管理
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="用户管理"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="用户管理"]')))
        if title.text!="用户管理" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航用户管理页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "用户管理"
    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("姓名查询")
def test_search_name(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #查询框
        p=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="name"]]//input')))
        p.send_keys("李静月")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[6]//span/span')))
        if text.text != "李静月":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="姓名查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "李静月"

    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("手机号查询")
def test_search_phone(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #输入手机号
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//div[label[@for="mobile"]]//input'))).send_keys("15215819198")

        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[7]//span/span')))
        if text.text != "15215819198":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="手机号查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "15215819198"

    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("工号查询")
def test_search_work(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #输入工号
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[label[@for="user_number"]]//input'))).send_keys("JH-01087")

        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[5]//span/span')))
        if text.text != "JH-01087":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="工号查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "JH-01087"

    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("所属职务查询")
def test_search_attribute(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击所属职务
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[label[@for="fk_role_id"]]//input'))).click()
        #选择董事办
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-cascader-panel")]//ul/li/span[text()="董事办"]'))).click()
        #选择董事长秘书
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-cascader-menu__wrap")]//ul/li[span[text()="董事长秘书"]]/label/span'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[10]//span')))
        if text.text != "董事长秘书":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="所属职务查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "董事长秘书"

    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("用户状态查询")
def test_search_type(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击用户状态
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//div[label[@for="status"]]//input'))).click()
        #选择禁用
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-select-dropdown")]//li/span[text()="禁用"]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[11]//span')))
        if text.text != "禁用":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="用户状态查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "禁用"

    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("发送密码")
def test_send_password(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    try:
        # 点击发送密码按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button[1]'))).click()
        time.sleep(1)
        # 输入姓名查询
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="选择人员"]//div[@class="el-dialog__body"]//div[label[@for="name"]]//input'))).send_keys("应俊")
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"search-btns-dialog")]//button[span[text()="查询"]]'))).click()
        # 选择确定
        time.sleep(1)
        element=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//tbody/tr[1]/td[2]//span/span')))
        driver.execute_script("arguments[0].click();", element)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"search-btns-dialog")]//button[span[text()="确认"]]'))).click()
        time.sleep(1)
        # 查询
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "发送密码成功！":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="发送密码失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "发送密码成功！"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("显示密码")
def test_display_password(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    try:
        # 点击显示密码按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button[2]'))).click()
        time.sleep(1)
        # 输入登录密码
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="请输入登录密码"]//input'))).send_keys('1231234567')

        # 选择确定
        time.sleep(1)
        element=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]')))
        driver.execute_script("arguments[0].click();", element)

        time.sleep(1)
        # 查询
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[3]//span/span')))
        if text.text == "******":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="显示密码失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text != "******"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("新增用户")
def test_add_user(driver,navigate_to_user_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        # 点击新增按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button[3]'))).click()
        time.sleep(1)
        # 选择职务
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增用户"]//div[label[@for="role_id"]]//input'))).click()
        #选择科技部
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//div[contains(@class,"el-cascader-panel")]//ul/li/span[text()="科技部"]'))).click()
        #选择web前端
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//div[contains(@class,"el-cascader-panel")]//ul/li/span[text()="web前端"]'))).click()
        #输入用户名
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//div[label[@for="username"]]//input'))).send_keys("test")
        # 输入手机号
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//div[label[@for="mobile"]]//input'))).send_keys("15088972541")
        # 输入姓名
        name=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增用户"]//div[label[@for="name"]]//input')))
        name.send_keys("郑琦")


        # 输入密码
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//div[label[@for="password"]]//input'))).send_keys("123456")
        # 输入确认密码
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//div[label[@for="password_confirmation"]]//input'))).send_keys("123456")
        #点击保存
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()


        time.sleep(1)
        # 查询
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text == "新增成功":
            print("测试通过：新增成功")
        elif "该手机号码已存在" in text.text:
            print("测试通过：正确提示重复数据错误")
            # 点击关闭
            wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@aria-label='新增用户']/div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--primary')]"))).click()
            time.sleep(2)
        else:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增用户失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
            pytest.fail(f"新增失败，提示信息为：{text.text}")

    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("修改用户")
def test_modify(driver, navigate_to_user_management):
    wait = WebDriverWait(driver, 30)  # 增加等待时间
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #查询框
        p=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="name"]]//input')))
        p.send_keys("郑琦")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)

        # 定位编辑按钮
        modify = wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-primary")]')))
        driver.execute_script("arguments[0].scrollIntoView();", modify)
        modify.click()

        #输入密码
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="修改用户"]//div[@class="el-dialog__body"]//div[label[@for="password"]]//input'))).send_keys("123456")
        #二次确认
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="修改用户"]//div[@class="el-dialog__body"]//div[label[@for="password_confirmation"]]//input'))).send_keys("123456")

        # 点击保存
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__footer']/div/button/span[text()='保存']")))
        save_button.click()

        # 检查提示信息
        text = wait.until(EC.element_to_be_clickable((By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改用户失败截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e



#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("用户管理")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_user_management):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)

    # 定义预期样式
    expected_styles = {
        # 查询按钮样式
        'search_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 重置按钮样式
        'reset_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 发送密码按钮样式
        'send_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 显示密码按钮样式
        'display_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 新增按钮样式
        'add_button': {
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
        }
    }
    time.sleep(1)

    try:
        # 测试查询按钮样式
        search_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//div[contains(@class,"search-btns")]/button[contains(@class,"el-button--success")]')))
        actual_styles = {
            'background-color': to_rgb(search_button.value_of_css_property('background-color')),
            'color': to_rgb(search_button.value_of_css_property('color')),
            'border-radius': search_button.value_of_css_property('border-radius'),
            'width': search_button.value_of_css_property('width'),
            'height': search_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['search_button']:
            highlight_element(driver, search_button)
            allure.attach(driver.get_screenshot_as_png(), name="查询按钮样式匹配失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, search_button)
        assert actual_styles == expected_styles['search_button'], f"查询按钮样式不匹配: {actual_styles}"

        time.sleep(1)

        # 测试重置按钮样式
        reset_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//div[contains(@class,"search-btns")]/button[contains(@class,"el-button--primary")]')))
        actual_styles = {
            'background-color': to_rgb(reset_button.value_of_css_property('background-color')),
            'color': to_rgb(reset_button.value_of_css_property('color')),
            'border-radius': reset_button.value_of_css_property('border-radius'),
            'width': reset_button.value_of_css_property('width'),
            'height': reset_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['reset_button']:
            highlight_element(driver, reset_button)
            allure.attach(driver.get_screenshot_as_png(), name="重置按钮样式匹配失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, reset_button)
        assert actual_styles == expected_styles['reset_button'], f"重置按钮样式不匹配: {actual_styles}"


        # 测试发送密码按钮样式
        send_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button[1]')))
        actual_styles = {
            'background-color': to_rgb(send_button.value_of_css_property('background-color')),
            'color': to_rgb(send_button.value_of_css_property('color')),
            'border-radius': send_button.value_of_css_property('border-radius'),
            'width': send_button.value_of_css_property('width'),
            'height': send_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['send_button']:
            highlight_element(driver,send_button)
            allure.attach(driver.get_screenshot_as_png(), name="发送密码按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,send_button)
        assert actual_styles == expected_styles['send_button'], f"发送密码按钮样式不匹配: {actual_styles}"

        # 测试显示密码按钮样式
        display_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button[2]')))
        actual_styles = {
            'background-color': to_rgb(display_button.value_of_css_property('background-color')),
            'color': to_rgb(display_button.value_of_css_property('color')),
            'border-radius': display_button.value_of_css_property('border-radius'),
            'width': display_button.value_of_css_property('width'),
            'height': display_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['display_button']:
            highlight_element(driver,display_button)
            allure.attach(driver.get_screenshot_as_png(), name="显示密码按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,display_button)
        assert actual_styles == expected_styles['display_button'], f"显示密码按钮样式不匹配: {actual_styles}"

        # 测试新增按钮样式
        add_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button[3]')))
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

        #编辑按钮样式
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]')))
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

    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e
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
def navigate_to_salary_type(driver, login):
    """导航到岗位薪资类别页面"""
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
        #点击岗位薪资类别
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div/li/ul/div/a/li/span[text()="岗位薪资类别"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="岗位薪资级别标准设置"]')))
        if title.text!="岗位薪资级别标准设置" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航岗位薪资级别标准设置页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "岗位薪资级别标准设置"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("职务名称查询")
def test_search_position(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #查询框
        p=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="role_name"]]//input')))
        p.send_keys("UI美工")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[3]//span')))
        if text.text != "UI美工":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="职务名称查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "UI美工"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("所属部门查询")
def test_search_department(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击部门
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[label[@for="fk_dep_id"]]//input'))).click()
        #选择科技部
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-select-dropdown")]//ul/li/span[text()="科技部"]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[2]//span')))
        if text.text != "科技部":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="部门查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "科技部"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("岗位名称查询")
def test_search_job(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击岗位名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[label[@for="fk_job_id"]]//input'))).click()
        #选择高层管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-select-dropdown")]//ul/li/span[text()="高层管理"]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[4]//span')))
        if text.text != "高层管理":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="岗位名称查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "高层管理"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("岗位属性查询")
def test_search_attribute(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击岗位属性
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[label[@for="fk_job_kid"]]//input'))).click()
        #选择行政类
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-select-dropdown")]//ul/li/span[text()="行政类"]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[7]//span')))
        if text.text != "行政类":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="岗位属性查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "行政类"

    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("薪资类别查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_type(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击薪资类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[label[@for="category_name"]]//input'))).click()
        #选择高层管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start" and @class="el-select-dropdown el-popper"]//li[1]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[6]//span/span')))
        if text.text != "test":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资类别查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "test"

    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("修改岗位薪资级别标准")
def test_modify(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击岗位薪资设置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="岗位薪资设置"]'))).click()
        #点击职务
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//form/div[label[@for="role_arr"]]//input'))).click()
        #选择董事办
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-cascader-panel")]//ul/li/span[text()="董事办"]'))).click()
        #选择董事长
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-cascader-panel")]//ul/li[span[text()="董事长"]]/label/span'))).click()
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"el-dialog__footer")]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改岗位薪资级别标准失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_salary_type):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
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
        # 岗位薪资设置按钮样式
        'modify1_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '88px',
            'height': '28px'
        },
        # 薪资类别分配按钮样式
        'allocation_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '88px',
            'height': '28px'
        },
        # 折叠按钮样式
        'fold_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        #编辑按钮样式
        'modify2_button':{
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        # 薪资类别分配-新增按钮样式
        'allocation_add_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 薪资类别分配-修改按钮样式
        'allocation_modify_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 薪资类别分配-删除按钮样式
        'allocation_delete_button': {
            'background-color': 'rgb(245, 108, 108)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 薪资类别分配-分配按钮样式
        'allocation_all_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
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


        # 测试岗位薪资设置按钮样式
        modify1_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//button[span[text()="岗位薪资设置"]]')))
        actual_styles = {
            'background-color': to_rgb(modify1_button.value_of_css_property('background-color')),
            'color': to_rgb(modify1_button.value_of_css_property('color')),
            'border-radius': modify1_button.value_of_css_property('border-radius'),
            'width': modify1_button.value_of_css_property('width'),
            'height': modify1_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['modify1_button']:
            highlight_element(driver,modify1_button)
            allure.attach(driver.get_screenshot_as_png(), name="岗位薪资设置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,modify1_button)
        assert actual_styles == expected_styles['modify1_button'], f"岗位薪资设置按钮样式不匹配: {actual_styles}"

        # 测试薪资类别分配按钮样式
        allocation_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//button[span[text()="薪资类别分配"]]')))
        actual_styles = {
            'background-color': to_rgb(allocation_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_button.value_of_css_property('color')),
            'border-radius': allocation_button.value_of_css_property('border-radius'),
            'width': allocation_button.value_of_css_property('width'),
            'height': allocation_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_button']:
            highlight_element(driver,allocation_button)
            allure.attach(driver.get_screenshot_as_png(), name="薪资类别分配按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,allocation_button)
        assert actual_styles == expected_styles['allocation_button'], f"薪资类别分配按钮样式不匹配: {actual_styles}"

        # 测试折叠按钮样式
        fold_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//button[span[text()="折叠"]]')))
        actual_styles = {
            'background-color': to_rgb(fold_button.value_of_css_property('background-color')),
            'color': to_rgb(fold_button.value_of_css_property('color')),
            'border-radius': fold_button.value_of_css_property('border-radius'),
            'width': fold_button.value_of_css_property('width'),
            'height': fold_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['fold_button']:
            highlight_element(driver,fold_button)
            allure.attach(driver.get_screenshot_as_png(), name="折叠按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,fold_button)
        assert actual_styles == expected_styles['fold_button'], f"折叠按钮样式不匹配: {actual_styles}"


        #编辑按钮样式
        modify2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]')))
        driver.execute_script("arguments[0].scrollIntoView();", modify2_button)
        actual_styles = {
            'background-color': to_rgb(modify2_button.value_of_css_property('background-color')),
            'color': to_rgb(modify2_button.value_of_css_property('color')),
            'border-radius': modify2_button.value_of_css_property('border-radius'),
            'width': modify2_button.value_of_css_property('width'),
            'height': modify2_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['modify2_button']:
            highlight_element(driver,modify2_button)
            allure.attach(driver.get_screenshot_as_png(), name="编辑按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify2_button)
        assert actual_styles == expected_styles['modify2_button'], f"编辑按钮样式不匹配: {actual_styles}"


        #进入薪资类别分配页面
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="薪资类别分配"]'))).click()
        time.sleep(3)

        #新增按钮
        allocation_add_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", allocation_add_button)
        actual_styles = {
            'background-color': to_rgb(allocation_add_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_add_button.value_of_css_property('color')),
            'border-radius': allocation_add_button.value_of_css_property('border-radius'),
            'width': allocation_add_button.value_of_css_property('width'),
            'height': allocation_add_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_add_button']:
            highlight_element(driver,allocation_add_button)
            allure.attach(driver.get_screenshot_as_png(), name="新增按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, allocation_add_button)
        assert actual_styles == expected_styles['allocation_add_button'], f"新增按钮样式不匹配: {actual_styles}"

        #修改按钮
        allocation_modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="修改"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", allocation_modify_button)
        actual_styles = {
            'background-color': to_rgb(allocation_modify_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_modify_button.value_of_css_property('color')),
            'border-radius': allocation_modify_button.value_of_css_property('border-radius'),
            'width': allocation_modify_button.value_of_css_property('width'),
            'height': allocation_modify_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_modify_button']:
            highlight_element(driver,allocation_modify_button)
            allure.attach(driver.get_screenshot_as_png(), name="修改按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, allocation_modify_button)
        assert actual_styles == expected_styles['allocation_modify_button'], f"修改按钮样式不匹配: {actual_styles}"

        #删除按钮
        allocation_delete_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="删除"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", allocation_delete_button)
        actual_styles = {
            'background-color': to_rgb(allocation_delete_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_delete_button.value_of_css_property('color')),
            'border-radius': allocation_delete_button.value_of_css_property('border-radius'),
            'width': allocation_delete_button.value_of_css_property('width'),
            'height': allocation_delete_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_delete_button']:
            highlight_element(driver,allocation_delete_button)
            allure.attach(driver.get_screenshot_as_png(), name="删除按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, allocation_delete_button)
        assert actual_styles == expected_styles['allocation_delete_button'], f"删除按钮样式不匹配: {actual_styles}"

        #分配按钮
        allocation_all_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//div[@class="left flex flex-y-center"]//button[span[text()="分配"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", allocation_all_button)
        actual_styles = {
            'background-color': to_rgb(allocation_all_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_all_button.value_of_css_property('color')),
            'border-radius': allocation_all_button.value_of_css_property('border-radius'),
            'width': allocation_all_button.value_of_css_property('width'),
            'height': allocation_all_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_all_button']:
            highlight_element(driver,allocation_all_button)
            allure.attach(driver.get_screenshot_as_png(), name="分配按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, allocation_all_button)
        assert actual_styles == expected_styles['allocation_all_button'], f"分配按钮样式不匹配: {actual_styles}"

    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e



@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("薪资类别分配新增")
def test_allocation_add(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:

        #点击新增按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="新增"]]'))).click()
        #输入新增类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]/form/div[label[@for="name"]]//input'))).send_keys("test")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增类别"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资类别分配新增失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("薪资类别分配修改")
def test_allocation_modify(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:

        #选择类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-card__body"]//div[@class="vxe-tree--node-item is--current"]'))).click()
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="修改"]]'))).click()

        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改类别"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资类别分配修改失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("薪资类别分配删除")
def test_allocation_delete(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:

        #计算类别
        nodes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='vxe-tree--node-wrapper node--level-1']")))
        ago = len(nodes)
        #选择最后一个类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="删除"]]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)
        #计算现在有多少类别
        nodes=wait.until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='vxe-tree--node-wrapper node--level-1']")))
        now=len(nodes)

        if (ago-now)!=1:
            highlight_element(driver, nodes)
            allure.attach(driver.get_screenshot_as_png(), name="薪资类别分配修改失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, nodes)
        assert (ago-now)==1
    except Exception as e:
        print("删除失败")
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("岗位薪资类别")
@allure.description("薪资类别分配设置")
def test_allocation_set(driver,navigate_to_salary_type):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #选择最后一个类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        #点击分配按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="left flex flex-y-center"]//button[span[text()="分配"]]'))).click()
        time.sleep(1)
        #选择董事长
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//tbody/tr[1]/td[2]//span/span'))).click()
        time.sleep(1)
        #点击确定按钮
        target_element=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//form//button[span[text()="确认"]]')))
        driver.execute_script("arguments[0].click();", target_element)

        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "薪资类别设置成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资类别设置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "薪资类别设置成功"
    except Exception as e:
        raise e
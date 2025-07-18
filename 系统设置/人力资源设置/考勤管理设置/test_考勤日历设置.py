import datetime
import time

import pandas as pd
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
        allure.attach(driver.get_screenshot_as_png(), name="登录失败截图",
                      attachment_type=allure.attachment_type.PNG)
        raise e

#进入考勤日历界面
@pytest.fixture(scope="module")
def navigate_to_calendar(driver, login):
    """导航到考勤日历页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        if width==1366:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[1]/div[2]/ul/li[11]/i'))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[1]/div[2]/div/i'))).click()
        else:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[1]/div[2]/ul/li[10]/i'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div[1]/div/ul/div[2]/li/div/span'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div[1]/div/ul/div[2]/li/ul/div[1]/li/div/span'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="app"]/div/div[2]/div/div[1]/div/ul/div[2]/li/ul/div[1]/li/ul/div[1]/a/li/span'))).click()
        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[1]/div[1]/span[1]')))
        if title.text!="考勤日历设置" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航考勤日历设置页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "考勤日历设置"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("考勤管理设置")
@allure.story("考勤日历设置")
@allure.description("日期查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_date(driver,navigate_to_calendar):
    wait = WebDriverWait(driver, 10)
    try:
        date=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[1]/div[1]/div/div/div/input')))
        date.send_keys("2025-5-1")
        date.send_keys(Keys.RETURN)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]'))).click()
        time.sleep(1)
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr/td[2]/div/div/span/span')))
        if text.text != "2025-05-01":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="考勤日历日期查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "2025-05-01"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("考勤管理设置")
@allure.story("考勤日历设置")
@allure.description("是否假期查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_holiday(driver,navigate_to_calendar):
    wait = WebDriverWait(driver, 10)
    try:

        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]'))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[1]/div[2]/div/div/div/div/input'))).click()

        # 等待选项加载完成
        option_locator = (By.XPATH, "//li[@class='el-select-dropdown__item' and contains(., '公休日')]")
        option = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(option_locator)
        )

        # 点击包含“公休日”的选项
        option.click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]'))).click()
        time.sleep(1)

        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[6]/div/div')))
        if text.text != "公休日":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="考勤日历假期查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "公休日"
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("考勤管理设置")
@allure.story("考勤日历设置")
@allure.description("跳转今日")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_turn_today(driver,navigate_to_calendar):
    wait = WebDriverWait(driver, 20)
    try:
        driver.execute_script("location.reload();")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[1]/div[2]/button[1]/span'))).click()

        today=datetime.date.today()
        today=today.strftime("%Y-%m-%d")
        data=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[7]/td[2]/div/div/span/span')))


        if data.text != today:
            highlight_element(driver, data)
            allure.attach(driver.get_screenshot_as_png(), name="考勤日历假期跳至今日失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, data)
        assert data.text == today
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("考勤管理设置")
@allure.story("考勤日历设置")
@allure.description("修改考勤日历")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_modify(driver,navigate_to_calendar):
    wait = WebDriverWait(driver, 20)
    try:
        driver.execute_script("location.reload();")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[10]/div/div/button/span'))).click()
        time.sleep(0.5)

        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button/span[text()='保存']"))
        )
        save_button.click()

        text=wait.until(EC.visibility_of_element_located((By.XPATH, "//p[@class='el-message__content' and text()='更新成功']")))

        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="考勤日历假期查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("考勤管理设置")
@allure.story("考勤日历设置")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_calendar):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)

    # 定义预期样式
    expected_styles = {

        # 查询按钮样式
        'search_button': {
            'background-color': 'rgba(0, 150, 136, 1)',
            'color': 'rgba(255, 255, 255, 1)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 重置按钮样式
        'reset_button': {
            'background-color': 'rgba(60, 141, 188, 1)',
            'color': 'rgba(255, 255, 255, 1)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 文件类型选择器样式
        'file_type_select': {
            'height':'24px',
            'border': '1px solid rgb(220, 223, 230)',
            'border-radius': '2px'
        },
        #编辑按钮样式
        'modify_button':{
            'background-color': 'rgba(0, 0, 0, 0)',
            'color': 'rgba(64, 128, 255, 1)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        # 跳至今天按钮样式
        'turn_today_button': {
            'background-color': 'rgba(60, 141, 188, 1)',
            'color': 'rgba(255, 255, 255, 1)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 同步日历数据按钮样式
        'sync_calendar_button': {
            'background-color': 'rgba(0, 150, 136, 1)',
            'color': 'rgba(255, 255, 255, 1)',
            'border-radius': '2px',
            'width': '88px',
            'height': '28px'
        }
    }
    time.sleep(1)

    try:

        # 测试查询按钮样式
        search_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]')))
        actual_styles = {
            'background-color': search_button.value_of_css_property('background-color'),
            'color': search_button.value_of_css_property('color'),
            'border-radius': search_button.value_of_css_property('border-radius'),
            'width': search_button.value_of_css_property('width'),
            'height': search_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['search_button']:
            highlight_element(driver,search_button)
            allure.attach(driver.get_screenshot_as_png(), name="查询按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, search_button)
        assert actual_styles == expected_styles['search_button'], f"查询按钮样式不匹配: {actual_styles}"

        time.sleep(1)

        # 测试重置按钮样式
        reset_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]')))
        actual_styles = {
            'background-color': reset_button.value_of_css_property('background-color'),
            'color': reset_button.value_of_css_property('color'),
            'border-radius': reset_button.value_of_css_property('border-radius'),
            'width': reset_button.value_of_css_property('width'),
            'height': reset_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['reset_button']:
            highlight_element(driver,reset_button)
            allure.attach(driver.get_screenshot_as_png(), name="重置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,reset_button)
        assert actual_styles == expected_styles['reset_button'], f"重置按钮样式不匹配: {actual_styles}"

        #编辑按钮样式
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[10]/div/div/button')))
        actual_styles = {
            'background-color': modify_button.value_of_css_property('background-color'),
            'color': modify_button.value_of_css_property('color'),
            'border-radius': modify_button.value_of_css_property('border-radius'),
            'width': modify_button.value_of_css_property('width'),
            'height': modify_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['modify_button']:
            highlight_element(driver,modify_button)
            allure.attach(driver.get_screenshot_as_png(), name="编辑按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify_button)
        assert actual_styles == expected_styles['modify_button'], f"编辑按钮样式不匹配: {actual_styles}"

        #跳至今日按钮样式
        turn_today_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[1]/div[2]/button[1]')))
        actual_styles = {
            'background-color': turn_today_button.value_of_css_property('background-color'),
            'color': turn_today_button.value_of_css_property('color'),
            'border-radius': turn_today_button.value_of_css_property('border-radius'),
            'width': turn_today_button.value_of_css_property('width'),
            'height': turn_today_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['turn_today_button']:
            highlight_element(driver,turn_today_button)
            allure.attach(driver.get_screenshot_as_png(), name="跳至今日按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, turn_today_button)
        assert actual_styles == expected_styles['turn_today_button'], f"跳至今日按钮样式不匹配: {actual_styles}"

        #同步日历数据按钮样式
        sync_calendar_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[1]/div[2]/button[2]')))
        actual_styles = {
            'background-color': sync_calendar_button.value_of_css_property('background-color'),
            'color': sync_calendar_button.value_of_css_property('color'),
            'border-radius': sync_calendar_button.value_of_css_property('border-radius'),
            'width': sync_calendar_button.value_of_css_property('width'),
            'height': sync_calendar_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['sync_calendar_button']:
            highlight_element(driver,sync_calendar_button)
            allure.attach(driver.get_screenshot_as_png(), name="同步日历数据按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, sync_calendar_button)
        assert actual_styles == expected_styles['sync_calendar_button'], f"同步日历数据按钮样式不匹配: {actual_styles}"

    except Exception as e:
        # 截图并附加到 Allure 报告

        raise e

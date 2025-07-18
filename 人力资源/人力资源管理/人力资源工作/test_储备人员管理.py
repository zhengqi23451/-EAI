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

#进入我的提交界面

@pytest.fixture(scope="module")
def navigate(driver, login):
    """导航到我的提交页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        # 点击人力资源
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/ul/li[text()=" 人力资源 "]'))).click()
        if width == 1366:
            # 点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        # 点击组织架构管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="sidebar-container"]//li//span[text()="人力资源管理"]'))).click()
        # 点击部门管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="sidebar-container"]//li//span[text()="人力资源工作"]'))).click()
        # 点击部门结构管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="sidebar-container"]//li/ul//span[text()="储备人员管理"]'))).click()
        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH,'//section//div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/span[@class="title"]')))
        if title.text!="储备人员管理":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,title)
        assert title.text == "储备人员管理"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@pytest.mark.skip
@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate):
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
        # 折叠按钮样式
        'fold_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 浏览按钮样式
        'see_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(0, 185, 130)',
            'border-radius': '3px',
            'width': '26px',
            'height': '18px'
        }
    }

    time.sleep(1)
    try:

        time.sleep(1)
        # 测试查询按钮样式
        search_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]')))
        actual_styles = {
            'background-color': to_rgb(search_button.value_of_css_property('background-color')),
            'color': to_rgb(search_button.value_of_css_property('color')),
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
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]')))
        actual_styles = {
            'background-color': to_rgb(reset_button.value_of_css_property('background-color')),
            'color': to_rgb(reset_button.value_of_css_property('color')),
            'border-radius': reset_button.value_of_css_property('border-radius'),
            'width': reset_button.value_of_css_property('width'),
            'height': reset_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['reset_button']:
            highlight_element(driver,reset_button)
            allure.attach(driver.get_screenshot_as_png(), name="重置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,reset_button)
        assert actual_styles == expected_styles['reset_button'], f"重置按钮样式不匹配: {actual_styles}"

        # 测试折叠按钮样式
        fold_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="right flex flex-y-center"]//button[contains(@class,"el-button--primary")]')))
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

        # 测试浏览按钮样式
        see_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[last()]//button')))
        actual_styles = {
            'background-color': to_rgb(see_button.value_of_css_property('background-color')),
            'color': to_rgb(see_button.value_of_css_property('color')),
            'border-radius': see_button.value_of_css_property('border-radius'),
            'width': see_button.value_of_css_property('width'),
            'height': see_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['see_button']:
            highlight_element(driver,see_button)
            allure.attach(driver.get_screenshot_as_png(), name="浏览按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,see_button)
        assert actual_styles == expected_styles['see_button'], f"浏览按钮样式不匹配: {actual_styles}"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("姓名查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_name(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="name"]]//input'))).send_keys("test")


        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[6]//span/span')))
        n = text.text
        if "test" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="文件名称查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "test" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("部门查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_department(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="fk_dep_id"]]//input'))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="科技部"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[2]//span/span')))
        n = text.text
        if "科技部" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "科技部" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("岗位查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_job(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="fk_job_id"]]//input'))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="中层管理"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[4]//span/span')))
        n = text.text
        if "中层管理" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "中层管理" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("职务查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_role(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="fk_role_id"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="科技部"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="全栈工程师"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[3]//span/span')))
        n = text.text
        if "全栈工程师" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "全栈工程师" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("性别查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_incident(driver, navigate):
    """测试按文件名查询"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="sex"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="男"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()

        # 定位滚动条容器
        #scroll_x_handle = driver.find_element(By.CLASS_NAME, "vxe-table--scroll-x-handle")

        # 执行 JavaScript 来滚动水平滚动条
        # 例如，向右滚动 500 像素
        #driver.execute_script("arguments[0].scrollLeft += 1000;", scroll_x_handle)
        time.sleep(2)
        #if width == 1366:
            #text = wait.until(EC.presence_of_element_located((By.XPATH, '//tbody/tr[1]/td[16]//span/span')))
        #else:
        text=wait.until(EC.presence_of_element_located((By.XPATH, '//tbody/tr[1]/td[7]//span/span')))
        n = text.text
        #driver.execute_script("arguments[0].scrollLeft -= 1000;", scroll_x_handle)
        if "男" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "男" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@pytest.mark.skip
@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("年龄查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_age(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="age"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="中层管理"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[3]//span/span')))
        n = text.text
        if "中层管理" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "中层管理" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("学历查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_edu(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="education"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="大专"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[8]//span/span')))
        n = text.text
        if "大专" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "大专" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("地区查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_area(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="province_city_district"]]//input'))).send_keys("河南省")

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[10]//span/span')))
        n = text.text
        if "河南省" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "河南省" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("来源事项查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_source_matter(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="source_matter"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="辞退后"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[14]//span/span')))
        n = text.text
        if "辞退后" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "辞退后" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("储备事项查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_by_reserve_matter(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #部门查询测试
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]//div[label[@for="reserve_matter"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@x-placement="bottom-start"]//li/span[text()="可再次录用"]'))).click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//form//button[contains(@class,"el-button--primary")]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[15]//span/span')))
        n = text.text
        if "可再次录用" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "可再次录用" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e


@pytest.mark.skip("数据没头像")
@allure.epic("人力资源管理")
@allure.feature("人力资源工作")
@allure.story("储备人员管理")
@allure.description("修改储备人员信息")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_modify(driver, navigate):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:

        wait.until(EC.presence_of_element_located((By.XPATH, '//tbody/tr[1]/td[last()]//span'))).click()

        wait.until(EC.presence_of_element_located((By.XPATH, '//form//button[span[text()="保存"]]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.XPATH, '//p[@class="el-message__content"]')))
        n = text.text
        if "保存成功" not in n :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "保存成功" in n
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e
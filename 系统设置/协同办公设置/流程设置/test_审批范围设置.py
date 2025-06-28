import time
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

#进入审批范围界面
@pytest.fixture(scope="module")
def navigate_to_scope_approval(driver, login):
    """导航到审批范围页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 10)
    try:
        # 点击设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//ul[@class="menu-wrap el-menu--horizontal el-menu"]/li[contains(@class, "setting-menu")]/i'))).click()
        if width==1366:
            #点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        #点击协同办公设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="协同办公设置"]'))).click()
        #点击流程设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="流程设置"]'))).click()
        #点击审批范围设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="审批范围设置"]'))).click()

        # 验证页面加载
        time.sleep(2)
        text=wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="left flex flex-y-center"]/span[@class="title"]')))
        if text.text!="表单审批范围列表" :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="导航审批范围页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "表单审批范围列表"
    except Exception as e:
        raise e

@allure.epic("协同办公设置")
@allure.feature("流程设置")
@allure.story("审批范围设置")
@allure.description("根据单据名称查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_name(driver,navigate_to_scope_approval):
    wait=WebDriverWait(driver,20)

    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[label[@for="file_name"]]//input'))).send_keys("薪资")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="search-btns el-row"]//button[span[text()="查询"]]'))).click()
        time.sleep(3)
        title=wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[2]//span/span')))
        if "薪资" not in title.text :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="单据名称查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert "薪资" in title.text
    except Exception as e:
        raise e

@allure.epic("协同办公设置")
@allure.feature("流程设置")
@allure.story("审批范围设置")
@allure.description("设置审批范围")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_setup(driver, navigate_to_scope_approval):
    wait = WebDriverWait(driver, 20)  # 增加等待时间到 20 秒
    try:

        # 点击设置按钮3
        operation_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[18]//button/span')))
        driver.execute_script("arguments[0].scrollIntoView(true);", operation_button)
        time.sleep(1)  # 确保页面滚动完成
        operation_button.click()

        # 点击保存按钮
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-dialog__footer"]//button[contains(@class,"el-button--success")]')))
        save_button.click()

        # 验证设置成功

        title = wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="el-message__content"]')))
        if title.text != "设置成功":
            highlight_element(driver, title)
            allure.attach(driver.get_screenshot_as_png(), name="审批范围设置失败截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "设置成功"
    except Exception as e:
        print(f"Error: {e}")
        allure.attach(driver.get_screenshot_as_png(), name="失败截图", attachment_type=allure.attachment_type.PNG)
        raise e


@allure.epic("协同办公设置")
@allure.feature("流程设置")
@allure.story("审批范围设置")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_scope_approval):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 10)

    # 定义预期样式
    expected_styles = {
        # 搜索输入框样式
        'search_input': {
            'height': '24px',
            'border': '1px solid rgb(220, 223, 230)',
            'border-radius': '2px',
        },
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
        #设置按钮样式
        'setup_button':{
            'background-color': 'rgba(0, 0, 0, 0)',
            'color': 'rgba(64, 128, 255, 1)',
            'border-radius': '3px',
            'width': '26px',
            'height': '18px'
        }
    }
    time.sleep(1)

    try:


        # 测试查询按钮样式
        search_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="search-btns el-row"]//button[span[text()="查询"]]')))
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
            (By.XPATH, '//div[@class="search-btns el-row"]//button[span[text()="重置"]]')))
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

        #设置按钮样式
        setup_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//tbody/tr[1]/td[18]//button')))
        actual_styles = {
            'background-color': setup_button.value_of_css_property('background-color'),
            'color': setup_button.value_of_css_property('color'),
            'border-radius': setup_button.value_of_css_property('border-radius'),
            'width': setup_button.value_of_css_property('width'),
            'height': setup_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['setup_button']:
            highlight_element(driver,setup_button)
            allure.attach(driver.get_screenshot_as_png(), name="审批按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, setup_button)
        assert actual_styles == expected_styles['setup_button'], f"审批按钮样式不匹配: {actual_styles}"
    except Exception as e:
        # 截图并附加到 Allure 报告

        raise e

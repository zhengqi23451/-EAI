import time
from cProfile import label

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
        allure.attach(driver.get_screenshot_as_png(), name="文件类型查询失败截图",
                      attachment_type=allure.attachment_type.PNG)
        raise e


#进入临时文档界面

@pytest.fixture(scope="module")
def navigate_to_temporary(driver, login):
    """导航到临时文档页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[1]/div[2]/ul/li[1]'))).click()
        if width==1366:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[1]/div[2]/div/i'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div[1]/div/ul/div/li/div'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[2]/div/div[1]/div/ul/div/li/ul/div/li/div'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="app"]/div/div[2]/div/div[1]/div/ul/div/li/ul/div/li/ul/div[2]/a/li/span'))).click()
        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[1]/div[1]/span[1]')))
        if title.text!="临时文档" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="文件类型查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "临时文档"
    except Exception as e:
        raise e


@allure.feature("协同办公")
@allure.story("临时文档")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_temporary):
    """测试文件相关组件的样式"""
    driver.refresh()
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
            'width': '80px',
            'height': '28px'
        },
        # 重置按钮样式
        'reset_button': {
            'background-color': 'rgba(60, 141, 188, 1)',
            'color': 'rgba(255, 255, 255, 1)',
            'border-radius': '2px',
            'width': '80px',
            'height': '28px'
        },
        # 文件类型选择器样式
        'file_type_select': {
            'height':'24px',
            'border': '1px solid rgb(220, 223, 230)',
            'border-radius': '2px'
        },
        #继续按钮样式
        'continue_button':{
            'background-color': 'rgba(0, 0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '26px',
            'height': '18px'
        },
        #删除按钮样式
        'delete_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(245, 108, 108)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        #事件缓急标签样式
        'event_label':{
            'width': '80px',
            'height': '28px'
        },
        #事情缓急选择器样式
        'event_select':{
            'width': '100px',
            'height': '28px'
        },
        #关闭按钮样式
        'close_button':{
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '80px',
            'height': '28px'
        },
        #保存按钮样式
        'save_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '80px',
            'height': '28px'
        },
        #提交按钮样式
        'submit_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '80px',
            'height': '28px'
        }
    }
    time.sleep(1)
    try:
        # 测试文件名输入框样式
        file_name_input = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[1]/div[1]/div/div/div/input')))
        actual_styles = {
            'height': file_name_input.value_of_css_property('height'),
            'border': file_name_input.value_of_css_property('border'),
            'border-radius': file_name_input.value_of_css_property('border-radius'),
        }
        if actual_styles != expected_styles['search_input'] :
            highlight_element(driver,file_name_input)
            allure.attach(driver.get_screenshot_as_png(), name="文件名输入框样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, file_name_input)
        assert actual_styles == expected_styles['search_input'], f"文件名输入框样式不匹配: {actual_styles}"

        time.sleep(1)
        # 测试文件类型选择器样式
        file_type_select = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[1]/div[2]/div/div/div/div[1]/input')))
        actual_styles = {
            'height': file_type_select.value_of_css_property('height'),
            'border': file_type_select.value_of_css_property('border'),
            'border-radius': file_type_select.value_of_css_property('border-radius')
        }
        if actual_styles != expected_styles['file_type_select'] :
            highlight_element(driver,file_type_select)
            allure.attach(driver.get_screenshot_as_png(), name="文件类型选择器样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, file_type_select)
        assert actual_styles == expected_styles['file_type_select'], f"文件类型选择器样式不匹配: {actual_styles}"

        time.sleep(1)
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
        if actual_styles != expected_styles['search_button'] :
            highlight_element(driver,search_button)
            allure.attach(driver.get_screenshot_as_png(), name="查询按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,search_button)
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
        if actual_styles != expected_styles['reset_button'] :
            highlight_element(driver,reset_button)
            allure.attach(driver.get_screenshot_as_png(), name="重置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,reset_button)
        assert actual_styles == expected_styles['reset_button'], f"重置按钮样式不匹配: {actual_styles}"

        # 测试删除按钮样式
        delete_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[10]/div/div/button[2]')))
        actual_styles = {
            'background-color': to_rgb(delete_button.value_of_css_property('background-color')),
            'color': to_rgb(delete_button.value_of_css_property('color')),
            'border-radius': delete_button.value_of_css_property('border-radius'),
            'width': delete_button.value_of_css_property('width'),
            'height': delete_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['delete_button'] :
            highlight_element(driver,delete_button)
            allure.attach(driver.get_screenshot_as_png(), name="删除按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,delete_button)
        assert actual_styles == expected_styles['delete_button'], f"删除按钮样式不匹配: {actual_styles}"

        #进入继续页面
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[10]/div/div/button[1]/span'))).click()

        # 测试事件缓急标签样式
        event_label = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/div/label')))
        actual_styles = {
            'width': event_label.value_of_css_property('width'),
            'height': event_label.value_of_css_property('height')
        }
        if actual_styles != expected_styles['event_select'] :
            highlight_element(driver,event_label)
            allure.attach(driver.get_screenshot_as_png(), name="事件缓急标签样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,event_label)
        assert actual_styles == expected_styles['event_label'], f"事件缓急标签样式不匹配: {actual_styles}"

        # 测试事件缓急选择器样式
        event_select = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/div/div/div/div/input')))
        actual_styles = {
            'width': event_select.value_of_css_property('width'),
            'height': event_select.value_of_css_property('height')
        }
        if actual_styles != expected_styles['event_select'] :
            highlight_element(driver,event_select)
            allure.attach(driver.get_screenshot_as_png(), name="事件缓急标签样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,event_select)
        assert actual_styles == expected_styles['event_select'], f"事件缓急标签样式不匹配: {actual_styles}"

        # 测试关闭按钮样式
        close_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]')))
        actual_styles = {
            'background-color': to_rgb(close_button.value_of_css_property('background-color')),
            'color': to_rgb(close_button.value_of_css_property('color')),
            'border-radius': close_button.value_of_css_property('border-radius'),
            'width': close_button.value_of_css_property('width'),
            'height': close_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['close_button'] :
            highlight_element(driver,close_button)
            allure.attach(driver.get_screenshot_as_png(), name="关闭按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,close_button)
        assert actual_styles == expected_styles['close_button'], f"关闭按钮样式不匹配: {actual_styles}"

        # 测试保存按钮样式
        save_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]')))
        actual_styles = {
            'background-color': to_rgb(save_button.value_of_css_property('background-color')),
            'color': to_rgb(save_button.value_of_css_property('color')),
            'border-radius': save_button.value_of_css_property('border-radius'),
            'width': save_button.value_of_css_property('width'),
            'height': save_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['save_button'] :
            highlight_element(driver,save_button)
            allure.attach(driver.get_screenshot_as_png(), name="保存按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,save_button)
        assert actual_styles == expected_styles['save_button'], f"保存按钮样式不匹配: {actual_styles}"

        # 测试提交按钮样式
        submit_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[3]')))
        actual_styles = {
            'background-color': to_rgb(submit_button.value_of_css_property('background-color')),
            'color': to_rgb(submit_button.value_of_css_property('color')),
            'border-radius': submit_button.value_of_css_property('border-radius'),
            'width': submit_button.value_of_css_property('width'),
            'height': submit_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['submit_button'] :
            highlight_element(driver,submit_button)
            allure.attach(driver.get_screenshot_as_png(), name="提交按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,submit_button)
        assert actual_styles == expected_styles['submit_button'], f"提交按钮样式不匹配: {actual_styles}"

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]'))).click()
    except Exception as e:
        raise e


@allure.feature("协同办公")
@allure.story("临时文档")
@allure.description("根据文件名称查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_search_by_name(driver, navigate_to_temporary):
    """测试按文件名查询"""
    wait = WebDriverWait(driver, 10)
    try:
        # 文件名查询测试
        file_name = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[1]/div[1]/div/div/div/input')))
        file_name.send_keys("新")

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]'))).click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]'))).click()
        text = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[2]/div/div/span/span')))
        n = text.text
        if "新" not in n:
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="文件名称查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,text)
        assert "新" in n
    except Exception as e:
        # 截图并附加到 Allure 报告

        raise e

@allure.feature("协同办公")
@allure.story("临时文档")
@allure.description("根据文件类型查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_search_by_type(driver, navigate_to_temporary):
    """测试按文件类型查询"""
    wait = WebDriverWait(driver, 10)
    try:
        # 文件类型查询测试
        file_type = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[1]/div[2]/div/div/div/div[1]/input')))
        file_type.click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//ul[contains(@class, "el-select-dropdown__list")]/li/span[text()="销售日志"]'))).click()
        time.sleep(1)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]'))).click()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]'))).click()
        time.sleep(1)
        text = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             '//*[@id="app"]/div/div[3]/section/div/div/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[2]/div/div/span/span')))
        n = text.text
        if "销售日志" not in n:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="文件类型查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "销售日志" in n

    except Exception as e:
        # 截图并附加到 Allure 报告

        raise e


@allure.feature("协同办公")
@allure.story("临时文档")
@allure.description("编辑临时文档并保存")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_continue(driver,navigate_to_temporary):
    driver.refresh()
    wait = WebDriverWait(driver, 10)
    try:
        #继续和保存
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.el-button.font-primary.el-button--text.el-button--mini"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[2]'))).click()
        text=wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "el-message__content"))).text
        if text!="保存成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="临时文档保存失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text=="保存成功"
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//*[@id="app"]/div/div[3]/section/div/form/div[2]/button[1]'))).click()
        time.sleep(3)
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

#删除
@allure.feature("协同办公")
@allure.story("临时文档")
@allure.description("删除临时文档")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_delete(driver,navigate_to_temporary):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.el-button.font-danger.el-button--text.el-button--mini"))).click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.el-button.el-button--default.el-button--small.el-button--primary"))).click()
        text = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "el-message__content")))
        if text.text != "删除成功！":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="临时文档删除失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "删除成功！"
    except Exception as e:
        # 截图并附加到 Allure 报告

        raise e
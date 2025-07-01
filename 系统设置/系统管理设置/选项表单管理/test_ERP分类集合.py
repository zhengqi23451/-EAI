import datetime
import time
import typing

from selenium.common import TimeoutException
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
def navigate_to_ERP_Classification(driver, login):
    """导航到类别管理页面"""
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="选项表单管理"]'))).click()
        #点击类别管理
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="ERP分类集合"]'))).click()

        # 验证页面加载
        time.sleep(2)
        if driver.current_url!="http://192.168.2.42:9529/#/sys/manage/options/erpCategory" :
            allure.attach(driver.get_screenshot_as_png(), name="导航ERP分类集合页面失败截图",attachment_type=allure.attachment_type.PNG)
        assert driver.current_url == "http://192.168.2.42:9529/#/sys/manage/options/erpCategory"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("新增分类")
def test_add(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="el-card__header"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].click();", add)
        #点击所属父级
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]/form/div[label[@for="menu_sign"]]//input'))).click()
        #选择仓库物理管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//li[span[text()="仓库物理管理"]]'))).click()
        #输入分类名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增分类"]//div[@class="el-dialog__body"]//div[label[@for="cate_name"]]//input'))).send_keys("t1")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增分类"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增分类失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("修改分类")
def test_modify(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        # 选择最后一个分类
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        # 选择
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]//div[@class="vxe-tree--node-child-wrapper"]/div[2]//span'))).click()
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="修改"]]'))).click()

        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改分类"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改类别失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("新增配置")
def test_add2(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//section//div[@class="left flex flex-y-center"]/button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].click();", add)
        #输入分类名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增配置"]//div[@class="el-dialog__body"]//div[label[@for="cate_name"]]//input'))).send_keys("t1")
        #输入分类标识
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增配置"]//div[@class="el-dialog__body"]//div[label[@for="cate_sign"]]//input'))).send_keys("t1")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增配置"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("修改配置")
def test_modify2(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-primary")]'))).click()
        #点击保存按钮
        save=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改配置"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]')))
        driver.execute_script("arguments[0].click();", save)
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_ERP_Classification):
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
            'width': '50px',
            'height': '28px'
        },
        # 修改按钮样式
        'modify_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '50px',
            'height': '28px'
        },
        # 删除按钮样式
        'delete_button': {
            'background-color': 'rgb(245, 108, 108)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '50px',
            'height': '28px'
        },
        # 折叠按钮样式
        'fold_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '50px',
            'height': '28px'
        },
        # 新增2按钮样式
        'add2_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 编辑按钮样式
        'modify2_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        #删除配置样式
        'delete2_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(245, 108, 108)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
    }
    time.sleep(1)
    try:
        #新增按钮
        add_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", add_button)
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
            reset_element(driver, add_button)
        assert actual_styles == expected_styles['add_button'], f"新增按钮样式不匹配: {actual_styles}"

        #修改按钮
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="修改"]]')))
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
            allure.attach(driver.get_screenshot_as_png(), name="修改按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify_button)
        assert actual_styles == expected_styles['modify_button'], f"修改按钮样式不匹配: {actual_styles}"

        #删除按钮
        delete_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="删除"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", delete_button)
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

        #折叠按钮
        fold_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[i[@class="el-icon-sort"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", fold_button)
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
            reset_element(driver, fold_button)
        assert actual_styles == expected_styles['fold_button'], f"折叠按钮样式不匹配: {actual_styles}"

        #新增配置按钮
        add2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//div[@class="left flex flex-y-center"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", add2_button)
        actual_styles = {
            'background-color': to_rgb(add2_button.value_of_css_property('background-color')),
            'color': to_rgb(add2_button.value_of_css_property('color')),
            'border-radius': add2_button.value_of_css_property('border-radius'),
            'width': add2_button.value_of_css_property('width'),
            'height': add2_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['add2_button']:
            highlight_element(driver,add2_button)
            allure.attach(driver.get_screenshot_as_png(), name="新增配置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, add2_button)
        assert actual_styles == expected_styles['add2_button'], f"新增配置按钮样式不匹配: {actual_styles}"

        #修改2按钮
        modify2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]')))
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
            allure.attach(driver.get_screenshot_as_png(), name="修改按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify2_button)
        assert actual_styles == expected_styles['modify2_button'], f"修改按钮样式不匹配: {actual_styles}"

        #删除按钮
        delete2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
        driver.execute_script("arguments[0].scrollIntoView();", delete2_button)
        actual_styles = {
            'background-color': to_rgb(delete2_button.value_of_css_property('background-color')),
            'color': to_rgb(delete2_button.value_of_css_property('color')),
            'border-radius': delete2_button.value_of_css_property('border-radius'),
            'width': delete2_button.value_of_css_property('width'),
            'height': delete2_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['delete2_button']:
            highlight_element(driver,delete2_button)
            allure.attach(driver.get_screenshot_as_png(), name="删除按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, delete2_button)
        assert actual_styles == expected_styles['delete2_button'], f"删除按钮样式不匹配: {actual_styles}"

    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("删除配置")
def test_delete2(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #计算类别
        nodes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr")))
        ago = len(nodes)
        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-danger")]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)
        #计算现在有多少类别
        try:
            nodes=WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH,"//tbody/tr")))
            now=len(nodes)
        except TimeoutException:
            now=0

        if (ago-now)!=1:
            highlight_element(driver, nodes)
            allure.attach(driver.get_screenshot_as_png(), name="删除配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, nodes)
        assert (ago-now)==1
    except Exception as e:
        print("删除失败")
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("删除分类")
def test_delete(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #计算类别
        nodes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "(//div[@class='vxe-tree--node-wrapper node--level-1'])[last()]//div[@class='vxe-tree--node-wrapper node--level-2']")))
        ago = len(nodes)

        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="删除"]]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)
        #计算现在有多少类别
        try:
            nodes=WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH,"(//div[@class='vxe-tree--node-wrapper node--level-1'])[last()]//div[@class='vxe-tree--node-wrapper node--level-2']")))
            now=len(nodes)
        except TimeoutException:
            now=0

        if (ago-now)!=1:
            highlight_element(driver, nodes)
            allure.attach(driver.get_screenshot_as_png(), name="删除分类失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, nodes)
        assert (ago-now)==1
    except Exception as e:
        print("删除失败")
        raise e





import datetime
import time
import typing

from selenium.common import TimeoutException
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
def navigate_to_ERP_Classification(driver, login):
    """导航到类别管理页面"""
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="选项表单管理"]'))).click()
        #点击类别管理
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="ERP分类集合"]'))).click()

        # 验证页面加载
        time.sleep(2)
        if driver.current_url!="http://192.168.2.42:9529/#/sys/manage/options/erpCategory" :
            allure.attach(driver.get_screenshot_as_png(), name="导航ERP分类集合页面失败截图",attachment_type=allure.attachment_type.PNG)
        assert driver.current_url == "http://192.168.2.42:9529/#/sys/manage/options/erpCategory"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("新增分类")
def test_add(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="el-card__header"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].click();", add)
        #点击所属父级
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]/form/div[label[@for="menu_sign"]]//input'))).click()
        #选择仓库物理管理
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//li[span[text()="仓库物理管理"]]'))).click()
        #输入分类名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增分类"]//div[@class="el-dialog__body"]//div[label[@for="cate_name"]]//input'))).send_keys("t1")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增分类"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增分类失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("修改分类")
def test_modify(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        # 选择最后一个分类
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        # 选择
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]//div[@class="vxe-tree--node-child-wrapper"]/div[2]//span'))).click()
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="修改"]]'))).click()

        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改分类"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改类别失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("新增配置")
def test_add2(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//section//div[@class="left flex flex-y-center"]/button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].click();", add)
        #输入分类名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增配置"]//div[@class="el-dialog__body"]//div[label[@for="cate_name"]]//input'))).send_keys("t1")
        #输入分类标识
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增配置"]//div[@class="el-dialog__body"]//div[label[@for="cate_sign"]]//input'))).send_keys("t1")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增配置"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("修改配置")
def test_modify2(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-primary")]'))).click()
        #点击保存按钮
        save=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改配置"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]')))
        driver.execute_script("arguments[0].click();", save)
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_ERP_Classification):
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
            'width': '50px',
            'height': '28px'
        },
        # 修改按钮样式
        'modify_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '50px',
            'height': '28px'
        },
        # 删除按钮样式
        'delete_button': {
            'background-color': 'rgb(245, 108, 108)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '50px',
            'height': '28px'
        },
        # 折叠按钮样式
        'fold_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '50px',
            'height': '28px'
        },
        # 新增2按钮样式
        'add2_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 编辑按钮样式
        'modify2_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        #删除配置样式
        'delete2_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(245, 108, 108)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
    }
    time.sleep(1)
    try:
        #新增按钮
        add_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", add_button)
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
            reset_element(driver, add_button)
        assert actual_styles == expected_styles['add_button'], f"新增按钮样式不匹配: {actual_styles}"

        #修改按钮
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="修改"]]')))
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
            allure.attach(driver.get_screenshot_as_png(), name="修改按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify_button)
        assert actual_styles == expected_styles['modify_button'], f"修改按钮样式不匹配: {actual_styles}"

        #删除按钮
        delete_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[span[text()="删除"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", delete_button)
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

        #折叠按钮
        fold_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//section//div[@class="el-card__header"]//button[i[@class="el-icon-sort"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", fold_button)
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
            reset_element(driver, fold_button)
        assert actual_styles == expected_styles['fold_button'], f"折叠按钮样式不匹配: {actual_styles}"

        #新增配置按钮
        add2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//div[@class="left flex flex-y-center"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", add2_button)
        actual_styles = {
            'background-color': to_rgb(add2_button.value_of_css_property('background-color')),
            'color': to_rgb(add2_button.value_of_css_property('color')),
            'border-radius': add2_button.value_of_css_property('border-radius'),
            'width': add2_button.value_of_css_property('width'),
            'height': add2_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['add2_button']:
            highlight_element(driver,add2_button)
            allure.attach(driver.get_screenshot_as_png(), name="新增配置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, add2_button)
        assert actual_styles == expected_styles['add2_button'], f"新增配置按钮样式不匹配: {actual_styles}"

        #修改2按钮
        modify2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]')))
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
            allure.attach(driver.get_screenshot_as_png(), name="修改按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, modify2_button)
        assert actual_styles == expected_styles['modify2_button'], f"修改按钮样式不匹配: {actual_styles}"

        #删除按钮
        delete2_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
        driver.execute_script("arguments[0].scrollIntoView();", delete2_button)
        actual_styles = {
            'background-color': to_rgb(delete2_button.value_of_css_property('background-color')),
            'color': to_rgb(delete2_button.value_of_css_property('color')),
            'border-radius': delete2_button.value_of_css_property('border-radius'),
            'width': delete2_button.value_of_css_property('width'),
            'height': delete2_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['delete2_button']:
            highlight_element(driver,delete2_button)
            allure.attach(driver.get_screenshot_as_png(), name="删除按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, delete2_button)
        assert actual_styles == expected_styles['delete2_button'], f"删除按钮样式不匹配: {actual_styles}"

    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("删除配置")
def test_delete2(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #计算类别
        nodes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr")))
        ago = len(nodes)
        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-danger")]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)
        #计算现在有多少类别
        try:
            nodes=WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH,"//tbody/tr")))
            now=len(nodes)
        except TimeoutException:
            now=0

        if (ago-now)!=1:
            highlight_element(driver, nodes)
            allure.attach(driver.get_screenshot_as_png(), name="删除配置失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, nodes)
        assert (ago-now)==1
    except Exception as e:
        print("删除失败")
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("选项表单管理")
@allure.story("ERP分类集合")
@allure.description("删除分类")
def test_delete(driver,navigate_to_ERP_Classification):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #计算类别
        nodes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "(//div[@class='vxe-tree--node-wrapper node--level-1'])[last()]//div[@class='vxe-tree--node-wrapper node--level-2']")))
        ago = len(nodes)

        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="删除"]]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)
        #计算现在有多少类别
        try:
            nodes=WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH,"(//div[@class='vxe-tree--node-wrapper node--level-1'])[last()]//div[@class='vxe-tree--node-wrapper node--level-2']")))
            now=len(nodes)
        except TimeoutException:
            now=0

        if (ago-now)!=1:
            highlight_element(driver, nodes)
            allure.attach(driver.get_screenshot_as_png(), name="删除分类失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, nodes)
        assert (ago-now)==1
    except Exception as e:
        print("删除失败")
        raise e






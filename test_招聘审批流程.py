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

def highlight_element(driver, element):
    """高亮显示元素"""
    driver.execute_script("arguments[0].style.border='6px solid red';", element)
def reset_element(driver, element):
    """恢复元素样式"""


# 设置Tesseract路径（根据实际安装位置调整）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.binary_location =r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    service = Service(executable_path=r"C:\Program Files\Google\Chrome\Application\chromedriver.exe")
    driver = webdriver.Chrome(service=service,options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


# 登录固件
@pytest.fixture(scope="function")
def login(driver,request):
    username = request.param.get("username")
    password = request.param.get("password")
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[@class="login-container"]/div[@class="con-in"]/form/div[2]/div[1]/div[@class="el-form-item__content"]/div[@class="el-input"]/input'))).send_keys(username)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[@class="login-container"]/div[@class="con-in"]/form/div[2]/div[2]/div[@class="el-form-item__content"]/div[@class="el-input"]/input'))).send_keys(password)
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
        allure.attach(driver.get_screenshot_as_png(), name="登录失败截图",attachment_type=allure.attachment_type.PNG)
        raise e

    return request.param


@pytest.fixture(scope="function")
def navigate_to_approval(driver, login):
    """导航到审批页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        # 点击协同办公设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/ul/li[text()=" 协同办公 "]'))).click()
        if width<=1366:
            #点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        #点击我的工作
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]//li//span[text()="我的工作"]'))).click()
        #点击我的审批
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]//li/ul//span[text()="我的审批"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//section//div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/span[@class="title"]')))
        if title.text !="我的审批":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航到审批页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,title)
        assert title.text == "我的审批"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e



# 定义审批操作函数

def approve_candidate(driver, title):
    wait = WebDriverWait(driver, 20)
    print("组长及以上")
    try:
        # 点击审批按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[1]/td[last()]//span"))).click()
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 输入审批意见
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[div[contains(text(), '{title}')]]//textarea"))).send_keys("同意")
        time.sleep(1)
        # 选择同意
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='middle']//div[contains(@class,'el-select')]//input"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='top-start']//li[span[text()='同意']]"))).click()
        # 点击下一步
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='middle']/button[span[text()='下一步']]"))).click()
        time.sleep(2)
        return "审批成功"
    except Exception as e:
        raise  e


#人事经理的操作
def approve_f(driver):
    wait = WebDriverWait(driver, 20)
    print("人事经理专属操作")
    #点击审批按钮
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[1]/td[last()]//span"))).click()
    #综合测评
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[1]/td[4]//label[1]/span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[2]/td[4]//label[1]/span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[3]/td[4]//label[1]/span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[4]/td[4]//label[1]/span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[5]/td[4]//label[1]/span/span"))).click()
    time.sleep(1)
    #就职信息和岗位配置信息
    #点击选择按钮
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='flex']/button"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//div[label[@for='role_name']]//input"))).send_keys("锯料/技工")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//button[span[text()='查询']]"))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//tbody/tr[1]/td[2]//span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__body']//button[span[text()='确认']]"))).click()
    time.sleep(1)
    #签约性质
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='nature_contract']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='合同工']]"))).click()
    #假日状况
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='holiday']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='单休（周日）']]"))).click()
    #税金方式
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='taxes']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='税前结算']]"))).click()
    #考勤类型
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='attendance']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='白天班']]"))).click()
    #薪资架构
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='salary_structure']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='计时工资']]"))).click()
    #结算方式
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='settlement']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='按月结算']]"))).click()

    #人力资源部门面试
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='profession_knowledge']]//input"))).send_keys("无")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='work_experience']]//input"))).send_keys("5")
    #职称
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='job_title']]//input"))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='暂无']]"))).click()
    #水平
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='level']]//input"))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='暂无']]"))).click()
    #工作区域
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='work_area']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='在公司工作']]"))).click()
    #残疾状况
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='disability_status']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='无残疾']]"))).click()
    #有无案底
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='have_record']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='无犯罪记录']]"))).click()
    #现状工作
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='current_work']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='已离岗']]"))).click()
    #到岗时间
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='duty_time']]//input"))).send_keys("2025-07-01")
    #试用期限
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='probation_time']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='1个月']]"))).click()
    #已缴社保
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='duty_time']]//input"))).send_keys("12")
    #住宿要求
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='dormitory_type']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='双人间']]"))).click()
    #车位需求
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='parking_type']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='不需要']]"))).click()
    #要求加班
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='work_overtime']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='愿意加班']]"))).click()
    #社保要求
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='social_security']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='需要参保']]"))).click()
    #办保时间
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='social_security_start']]//label[2]/span[1]"))).click()
    #打卡配置
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='attendance_cate']]//button"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='选择打卡配置']//div[@class='el-dialog__body']//tbody/tr[1]/td[2]//span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='选择打卡配置']//div[@class='el-dialog__body']//form//button[span[text()='确认']]"))).click()
    #使用软件
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[label[@for='using_software']]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//li[span[text()='OA办公系统']]"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='using_software']"))).click()
    #员工薪资标准
    #转正前
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='vxe-table--render-wrapper']//tbody/tr[1]/td[last()]//button"))).click()
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='选择薪资等级']//tbody/tr[1]/td[2]//span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='选择薪资等级']//form//button[span[text()='确认']]"))).click()

    #转正后
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='vxe-table--render-wrapper']//tbody/tr[2]/td[last()]//button"))).click()
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='选择薪资等级']//tbody/tr[2]/td[2]//span/span"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='选择薪资等级']//form//button[span[text()='确认']]"))).click()

    #选择同意
    wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='middle']//div[contains(@class,'el-select')]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@x-placement='top-start']//li[span[text()='同意']]"))).click()
    #点击下一步
    wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='middle']/button[span[text()='下一步']]"))).click()
    time.sleep(5)
    return "审批成功"

@pytest.mark.skip('暂未完成')
def add_jl(driver,title):
    wait = WebDriverWait(driver, 20)
    driver.get("http://192.168.2.42:9529/#/hr/manpower/resume")
    #姓名

    #性别

    #输入审批意见
    wait.until(EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{title}')]/following-sibling::div//textarea"))).send_keys("同意")
    #选择同意
    wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='middle']//div[contains(@class,'el-select')]//input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@x-placement='top-start']//li[span[text()='同意']]"))).click()
    #点击下一步
    wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='middle']/button[span[text()='下一步']]"))).click()




# 测试用例
@pytest.mark.parametrize("login", [
    #人事助理
    #{"username": "JH-03502", "password": "307306"},
    #人事经理
    {"username": "JH-03173", "password": "123456"},
    #组长
    {"username": "JH-01048", "password": "123456","title":"车间/主任审批意见"},
    #部门经理
    {"username": "JH-00849", "password": "350715","title":"生产部经理审批意见"},
    #部门副总（暂无）
    #{"username": "JH-03173", "password": "123456"},
    #总经理
    {"username": "JH-01562", "password": "520308","title":"总经理审批意见"},
    #董事长
    {"username": "JH-00001", "password": "1231234567","title":"董事长审批意见"},
], indirect=True)
def test_approve(driver, login,navigate_to_approval):
    print(f"Login data: {login}")
    if login['username']=='JH-03173':
        approve_result =approve_f(driver)
    else:
        title = login.get("title", "")
        approve_result = approve_candidate(driver, title)
    assert approve_result == "审批成功"


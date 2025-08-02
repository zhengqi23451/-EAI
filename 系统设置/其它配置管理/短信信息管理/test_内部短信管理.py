from conftest import *

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
        allure.attach(driver.get_screenshot_as_png(), name="登录失败截图",attachment_type=allure.attachment_type.PNG)
        raise e


@pytest.fixture(scope="module")
def navigate(driver, login):
    """导航到接口缓存配置页面"""
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="其他配置管理"]'))).click()
        #点击网站配置管理
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="短信信息管理"]'))).click()
        #点击申请号码管理
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="内部短信管理"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="内部短信管理"]')))
        if title.text!="内部短信管理" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航内部短信管理页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "内部短信管理"
    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("其它配置管理")
@allure.feature("短信信息管理")
@allure.story("内部短信管理")
@allure.description("短信编号查询")
def test_search_document_no(driver,navigate):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #查询框
        wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="document_no"]]//input'))).send_keys("SMS25022840138")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[2]//span/span')))
        if text.text != "SMS25022840138":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="类别查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "SMS25022840138"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("其它配置管理")
@allure.feature("短信信息管理")
@allure.story("内部短信管理")
@allure.description("提交人查询")
def test_search_created_by(driver,navigate):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #查询框
        p=wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="created_by"]]//input')))
        p.send_keys("应俊")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[4]//span/span')))
        if "应俊" not in text.text:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="提交人查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "应俊" in text.text
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("其它配置管理")
@allure.feature("短信信息管理")
@allure.story("内部短信管理")
@allure.description("提交时间查询")
def test_search_data(driver,navigate):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #查询框
        wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="created_at"]]//input'))).send_keys("2025-02-27")

        #点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[5]//span/span')))
        if "2025-02-27" not in text.text:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="提交时间查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert "2025-02-27" in text.text
    except Exception as e:
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("其它配置管理")
@allure.feature("短信信息管理")
@allure.story("内部短信管理")
@allure.description("样式比较")
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

        #浏览按钮样式
        'browse_button':{
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(0, 185, 130)',
            'border-radius': '3px',
            'width': '26px',
            'height': '18px'
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
            highlight_element(driver,search_button)
            allure.attach(driver.get_screenshot_as_png(), name="查询按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
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
            highlight_element(driver,reset_button)
            allure.attach(driver.get_screenshot_as_png(), name="重置按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,reset_button)
        assert actual_styles == expected_styles['reset_button'], f"重置按钮样式不匹配: {actual_styles}"


        #编辑按钮样式
        browse_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button')))
        actual_styles = {
            'background-color': to_rgb(browse_button.value_of_css_property('background-color')),
            'color': to_rgb(browse_button.value_of_css_property('color')),
            'border-radius': browse_button.value_of_css_property('border-radius'),
            'width': browse_button.value_of_css_property('width'),
            'height': browse_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['browse_button']:
            highlight_element(driver,browse_button)
            allure.attach(driver.get_screenshot_as_png(), name="浏览按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, browse_button)
        assert actual_styles == expected_styles['browse_button'], f"浏览按钮样式不匹配: {actual_styles}"
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e



@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("其它配置管理")
@allure.feature("短信信息管理")
@allure.story("内部短信管理")
@allure.description("浏览短信内容")
def test_browse(driver,navigate):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击浏览按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button'))).click()

        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="grid-title flex flex-x-sb flex-y-center"]//span')))
        if text.text != "短信浏览":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="浏览按钮失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "短信浏览"
    except Exception as e:
        raise e




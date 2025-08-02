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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[label[@for="file_name"]]//input'))).send_keys("修改人员资料")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="search-btns el-row"]//button[span[text()="查询"]]'))).click()
        time.sleep(3)
        title=wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[2]//span/span')))
        if "修改人员资料" not in title.text :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="单据名称查询失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert "修改人员资料" in title.text
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

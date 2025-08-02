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

#进入奖罚界面
@pytest.fixture(scope="module")
def navigate_reward(driver, login):
    """导航到奖罚页面"""
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
        #点击工作表单设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="工作表单设置"]'))).click()
        #点击奖罚内容设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="奖罚内容设置"]'))).click()

        # 验证页面加载
        time.sleep(2)
        text=wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="left flex flex-y-center"]/span[@class="title"]')))
        if text.text!="奖罚内容设置" :
            highlight_element(driver,text)
            allure.attach(driver.get_screenshot_as_png(), name="导航奖罚内容设置页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "奖罚内容设置"
    except Exception as e:
        raise e

@allure.epic("协同办公设置")
@allure.feature("工作表单设置")
@allure.story("奖罚内容设置")
@allure.description("新增一级选项")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_add(driver,navigate_reward):
    wait=WebDriverWait(driver,20)
    time.sleep(3)
    try:
        #点击新增一级选项按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="right flex flex-y-center"]/button'))).click()
        #输入选项名称
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[label[@for="content_info"]]//input'))).send_keys("test")

        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="新增"]/div[@class="el-dialog__footer"]//button[contains(@class,"el-button--success")]'))).click()
        title=wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="el-message__content"]')))
        if title.text!="添加成功":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="新增一级选项失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text=="添加成功"
    except Exception as e:
        raise e

@allure.epic("协同办公设置")
@allure.feature("工作表单设置")
@allure.story("奖罚内容设置")
@allure.description("奖罚内容编辑")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_modify(driver,navigate_reward):
    wait=WebDriverWait(driver,20)
    time.sleep(3)
    try:
        #点击编辑按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[last()]//button[span[text()="编辑"]]'))).click()

        #点击保存按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="修改奖罚内容"]/div[@class="el-dialog__footer"]//button[contains(@class,"el-button--success")]'))).click()
        title=wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="el-message__content"]')))
        if title.text!="更新成功":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="修改奖罚内容失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text=="更新成功"
    except Exception as e:
        raise e

@allure.epic("协同办公设置")
@allure.feature("工作表单设置")
@allure.story("奖罚内容设置")
@allure.description("新增二级选项")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_add2(driver,navigate_reward):
    wait=WebDriverWait(driver,20)
    time.sleep(3)
    try:
        #点击新增二级按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[last()]//button[3]'))).click()
        #输入选项名称
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[label[@for="content_info"]]//input'))).send_keys("test")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="新增"]/div[@class="el-dialog__footer"]//button[contains(@class,"el-button--success")]'))).click()
        title=wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="el-message__content"]')))
        if title.text!="添加成功":
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="新增二级选项失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text=="添加成功"
    except Exception as e:
        raise e

@allure.epic("协同办公设置")
@allure.feature("工作表单设置")
@allure.story("奖罚内容设置")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_reward):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)

    # 定义预期样式
    expected_styles = {
        # 新增按钮样式
        'add_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '107px',
            'height': '28px'
        },
        #编辑按钮样式
        'modify_button':{
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(64, 128, 255)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        },
        # 删除按钮样式
        'delete_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(245, 108, 108)',
            'border-radius': '3px',
            'width': '43px',
            'height': '19px'
        }
    }
    time.sleep(1)

    try:
        # 测试新增按钮样式
        add_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="right flex flex-y-center"]/button')))
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
            (By.XPATH, '//tbody/tr[1]/td[last()]//button[span[text()="编辑"]]')))
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

        #删除按钮样式
        delete_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[last()]//button[span[text()="删除"]]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
        time.sleep(5)
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
    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@allure.epic("协同办公设置")
@allure.feature("工作表单设置")
@allure.story("奖罚内容设置")
@allure.description("奖罚内容删除")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_delete(driver,navigate_reward):
    wait=WebDriverWait(driver,20)
    time.sleep(3)
    try:
        ago=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="left flex flex-y-center"]//span/span')))
        ago=int(ago.text)
        #点击删除按钮
        driver.execute_script("window.scrollBy(1000, 0);")
        d=wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[last()]//button[span[text()="删除"]]')))
        d.click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-message-box']/div[@class='el-message-box__btns']/button[contains(@class,'el-button--primary')]"))).click()
        time.sleep(3)
        now = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="left flex flex-y-center"]//span/span')))
        now=int(now.text)
        if ago<=now:
            allure.attach(driver.get_screenshot_as_png(), name="奖罚内容删除失败截图",attachment_type=allure.attachment_type.PNG)
        assert ago>now
    except Exception as e:
        raise e




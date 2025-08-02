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


@pytest.fixture(scope="module")
def navigate_to_number_management(driver, login):
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="系统管理设置"]'))).click()
        #点击网站配置管理
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="网站配置管理"]'))).click()
        #点击申请号码管理
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="申请号码管理"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="申请号码管理"]')))
        if title.text!="申请号码管理" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航申请号码管理页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "申请号码管理"
    except Exception as e:
        raise e

#@pytest.mark.skip(reason="暂未测试")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("类别查询")
def test_search_type(driver,navigate_to_number_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #查询框
        wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="field_type"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@x-placement="bottom-start"]//li[span[text()="邮箱"]]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[2]//span/span')))
        if text.text != "邮箱":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="类别查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "邮箱"

    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("数据值查询")
def test_search_value(driver,navigate_to_number_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    value="123@qq.com"
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #查询框
        p=wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="field_value"]]//input')))
        p.send_keys(value)
        #点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[3]//span/span')))
        if value not in text.text:
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="数据值查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert value in text.text
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("是否停用查询")
def test_search_status(driver,navigate_to_number_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #查询框
        wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="status"]]//input'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@x-placement="bottom-start"]//li[span[text()="停用"]]'))).click()

        #点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@id="app"]//tbody/tr[1]/td[7]//span/span')))
        if text.text != "停用":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="是否停用查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "停用"

    except Exception as e:
        raise e



@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("新增申请信息")
def test_add(driver,navigate_to_number_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增菜单按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="right flex flex-y-center"]//button[span[text()="新增"]]'))).click()
        time.sleep(2)
        #点击类型下拉框
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-dialog__body"]//div[label[@for="field_type"]]//input'))).click()
        #选择邮箱
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@x-placement="bottom-start"]//li[span[text()="邮箱"]]'))).click()
        #输入数据值
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-dialog__body"]//div[label[@for="field_value"]]//input'))).send_keys("test@qq.com")
        #点击保存按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "添加成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增申请信息失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "添加成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("修改申请信息")
def test_modify(driver,navigate_to_number_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]'))).click()
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改申请信息"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="修改申请信息失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("删除申请信息")
def test_delete(driver,navigate_to_number_management):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击重置按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #查询框
        wait.until(EC.element_to_be_clickable((By.XPATH, '//section//form/div[@class="el-row"]//div[label[@for="field_value"]]//input'))).send_keys("test")
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)

        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "删除成功！":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="删除申请信息失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "删除成功！"
        #点击重置按钮
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
    except Exception as e:
        print("删除失败")
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("网站配置管理")
@allure.story("申请号码管理")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_number_management):
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
        # 新增按钮样式
        'add_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
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

        # 测试新增按钮样式
        add1_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//section//div[@class="right flex flex-y-center"]/button[span[text()="新增"]]')))
        actual_styles = {
            'background-color': to_rgb(add1_button.value_of_css_property('background-color')),
            'color': to_rgb(add1_button.value_of_css_property('color')),
            'border-radius': add1_button.value_of_css_property('border-radius'),
            'width': add1_button.value_of_css_property('width'),
            'height': add1_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['add_button']:
            highlight_element(driver,add1_button)
            allure.attach(driver.get_screenshot_as_png(), name="add按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,add1_button)
        assert actual_styles == expected_styles['add_button'], f"add按钮样式不匹配: {actual_styles}"

        #编辑按钮样式
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]')))
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
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
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


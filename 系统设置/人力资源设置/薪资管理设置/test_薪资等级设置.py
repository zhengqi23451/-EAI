
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
def navigate_to_salary_level(driver, login):
    """导航到技能测评页面"""
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    wait = WebDriverWait(driver, 20)
    try:
        # 点击设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//ul[@class="menu-wrap el-menu--horizontal el-menu"]/li[contains(@class, "setting-menu")]/i'))).click()
        if width==1366:
            #点击扩展列表
            wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="menu-bar"]/div[@class="flex flex-x-center flex-y-center fold-box"]/i'))).click()
        #点击人力资源设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/div/span'))).click()
        #点击薪资管理设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div/li/div/span[text()="薪资管理设置"]'))).click()
        #点击薪资等级设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div/li/ul/div/a/li/span[text()="薪资等级设置"]'))).click()

        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="table-info-bar flex flex-x-sb flex-y-center"]//span[text()="薪资等级"]')))
        if title.text!="薪资等级" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航薪资等级页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "薪资等级"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资等级设置")
@allure.description("税前金额查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_money(driver,navigate_to_salary_level):
    wait = WebDriverWait(driver, 20)
    try:
        #查询框
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form[contains(@class,"search-form")]/div[@class="el-row"]/div[1]/div/div[@class="el-form-item__content"]/div/input'))).send_keys("3100")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        #税前金额查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[15]//span/span')))
        if text.text != "3,100.00":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="税前金额查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "3,100.00"

    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资等级设置")
@allure.description("薪资等级查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_level(driver,navigate_to_salary_level):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    # 点击重置按钮
    wait.until(EC.element_to_be_clickable((By.XPATH,'//form//div[contains(@class,"search-btns")]/button[contains(@class,"el-button--primary")]'))).click()
    try:
        # 查询框
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[contains(@class,"app-container")]/form[contains(@class,"search-form")]/div[@class="el-row"]/div[2]/div/div[@class="el-form-item__content"]/div/input'))).send_keys("A2-3")
        # 点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(2)
        # 薪资等级查询
        text = wait.until(EC.presence_of_element_located((By.XPATH, '//tbody/tr[1]/td[2]//span/span')))

        time.sleep(3)
        if text.text != "A2-3":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资等级查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "A2-3"
        # 点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//form//div[contains(@class,"search-btns")]/button[contains(@class,"el-button--primary")]'))).click()

    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资等级设置")
@allure.description("新增薪资等级")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_add(driver,navigate_to_salary_level):
    wait = WebDriverWait(driver, 20)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button')))
        add.click()
        #薪资等级输入人t1-1
        wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='el-dialog__body']//form//div[label[@for='grade_name']]/div[@class='el-form-item__content']//input"))).send_keys("t1-1")
        #点击绩效考核
        wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='el-dialog__body']//form//div[label[@for='achievements_proportion']]/div[@class='el-form-item__content']//input"))).click()
        #选择10%
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@x-placement='bottom-start']//ul/li/span[text()='10']"))).click()

        #点击保存
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__footer']/div/button/span[text()='保存']"))).click()
        #提示
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增薪资等级失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资等级设置")
@allure.description("编辑薪资等级设置")
def test_modify(driver, navigate_to_salary_level):
    wait = WebDriverWait(driver, 30)  # 增加等待时间
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    time.sleep(3)
    try:
        # 查询框
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[contains(@class,"app-container")]/form[contains(@class,"search-form")]/div[@class="el-row"]/div[2]/div/div[@class="el-form-item__content"]/div/input'))).send_keys("t")
        # 点击查询按钮
        wait.until(EC.element_to_be_clickable((By.XPATH,'//form//div[contains(@class,"search-btns")]/button[contains(@class,"el-button--success")]'))).click()
        time.sleep(2)

        if width==1366:
            a=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="vxe-table--scroll-x-virtual"]/div[@class="vxe-table--scroll-x-right-corner"]')))
            # 获取元素的位置信息
            location = a.location
            size = a.size

            # 计算点击位置（元素左边10像素的位置）
            click_x = location['x'] - 10
            click_y = location['y'] + (size['height'] / 2)  # 垂直居中

            # 移动到计算出的位置并点击
            actions = ActionChains(driver)
            actions.move_by_offset(click_x, click_y).click().perform()

        # 定位编辑按钮
        modify = wait.until(EC.element_to_be_clickable((By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]//button[contains(@class,"font-primary")]')))
        modify.click()
        name=wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-dialog__body"]//form//div[label[@for="grade_name"]]//input')))
        name.click()
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
        name.send_keys("t1-1")
        num=wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-dialog__body"]//form//div[label[@for="grade_num"]]//input')))
        driver.execute_script("arguments[0].value = '';",num)
        num.send_keys("1")

        time.sleep(5)
        # 点击保存
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='el-dialog__footer']/div/button/span[text()='保存']")))
        save_button.click()

        # 检查提示信息
        text = wait.until(EC.element_to_be_clickable((By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资等级设置修改失败截图", attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资等级设置")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_salary_level):
    """测试文件相关组件的样式"""
    wait = WebDriverWait(driver, 20)

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
            'width': '67px',
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
            highlight_element(driver, search_button)
            allure.attach(driver.get_screenshot_as_png(), name="查询按钮样式匹配失败截图",
                          attachment_type=allure.attachment_type.PNG)
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
            highlight_element(driver, reset_button)
            allure.attach(driver.get_screenshot_as_png(), name="重置按钮样式匹配失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, reset_button)
        assert actual_styles == expected_styles['reset_button'], f"重置按钮样式不匹配: {actual_styles}"


        # 测试新增按钮样式
        add_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="right flex flex-y-center"]/button')))
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
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]')))
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
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
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


@allure.epic("人力资源设置")
@allure.feature("薪资管理设置")
@allure.story("薪资等级设置")
@allure.description("删除薪资等级")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_delete(driver,navigate_to_salary_level):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:

        #点击删除
        delete=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
        delete.click()
        #点击确认
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-message-box']/div[@class='el-message-box__btns']/button[contains(@class,'el-button--primary')]"))).click()
        # 提示
        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "删除成功！":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="薪资等级删除失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "删除成功！"
    except Exception as e:
        raise e




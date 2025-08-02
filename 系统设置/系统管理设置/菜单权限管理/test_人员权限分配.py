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
def navigate_to_permission_assignment(driver, login):
    """导航到人员权限分配页面"""
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="el-scrollbar__view"]//span[text()="菜单权限管理"]'))).click()
        #点击人员权限分配
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="el-scrollbar__view"]//span[text()="人员权限分配"]'))).click()

        # 验证页面加载
        time.sleep(2)

        if driver.current_url!="http://192.168.2.42:9529/#/sys/manage/menu/personPermission" :

            allure.attach(driver.get_screenshot_as_png(), name="导航人员权限分配页面失败截图",attachment_type=allure.attachment_type.PNG)

        assert driver.current_url == "http://192.168.2.42:9529/#/sys/manage/menu/personPermission"
    except Exception as e:
        raise e



@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("人员权限分配")
@allure.description("样式比较")
def test_file_style(driver, navigate_to_permission_assignment):
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
            'width': '76px',
            'height': '28px'
        },
        # 修改按钮样式
        'modify_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 删除按钮样式
        'delete_button': {
            'background-color': 'rgb(245, 108, 108)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 新增人员权限按钮样式
        'allocation_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '88px',
            'height': '28px'
        }
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

        #新增人员权限按钮
        allocation_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//div[@class="left flex flex-y-center"]//button[span[text()="新增人员权限"]]')))
        driver.execute_script("arguments[0].scrollIntoView();", allocation_button)
        actual_styles = {
            'background-color': to_rgb(allocation_button.value_of_css_property('background-color')),
            'color': to_rgb(allocation_button.value_of_css_property('color')),
            'border-radius': allocation_button.value_of_css_property('border-radius'),
            'width': allocation_button.value_of_css_property('width'),
            'height': allocation_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['allocation_button']:
            highlight_element(driver,allocation_button)
            allure.attach(driver.get_screenshot_as_png(), name="新增人员权限按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, allocation_button)
        assert actual_styles == expected_styles['allocation_button'], f"新增人员权限按钮样式不匹配: {actual_styles}"

    except Exception as e:
        # 截图并附加到 Allure 报告
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("人员权限分配")
@allure.description("人员权限新增")
def test_add(driver,navigate_to_permission_assignment):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="app"]//div[@class="el-card__header"]//button[span[text()="新增"]]')))
        driver.execute_script("arguments[0].click();", add)
        #点击分类名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]/form/div[label[@for="name"]]//input'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//span[text()="人力资源"]'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//span[text()="组织架构管理"]'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//span[text()="部门管理"]'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@x-placement="bottom-start"]//span[text()="组织架构图"]'))).click()
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="新增权限"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "添加成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="权限新增失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "添加成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("人员权限分配")
@allure.description("权限修改")
def test_modify(driver,navigate_to_permission_assignment):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        # 选择最后一个类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        #点击修改按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="修改"]]'))).click()

        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@aria-label="修改权限"]//div[@class="el-dialog__footer"]//button[span[text()="保存"]]'))).click()
        time.sleep(1)
        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "修改成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="权限修改失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "修改成功"
    except Exception as e:
        raise e

@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("人员权限分配")
@allure.description("权限删除")
def test_delete(driver,navigate_to_permission_assignment):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #计算类别
        nodes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='vxe-tree--node-wrapper node--level-1']")))
        ago = len(nodes)
        #选择最后一个类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        #点击删除按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//section//div[@class="el-card__header"]//button[span[text()="删除"]]'))).click()
        #点击确定按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-message-box"]//div[@class="el-message-box__btns"]//button[contains(@class,"el-button--primary")]'))).click()
        time.sleep(1)
        #计算现在有多少类别
        nodes=wait.until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='vxe-tree--node-wrapper node--level-1']")))
        now=len(nodes)

        if (ago-now)!=1:
            highlight_element(driver, nodes)
            allure.attach(driver.get_screenshot_as_png(), name="权限删除失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, nodes)
        assert (ago-now)==1
    except Exception as e:
        print("删除失败")
        raise e


@pytest.mark.parametrize("driver",['chrome'],indirect=True)
@allure.epic("系统管理设置")
@allure.feature("菜单权限管理")
@allure.story("人员权限分配")
@allure.description("新增人员权限")
def test_allocation_set(driver,navigate_to_permission_assignment):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #选择最后一个类别
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '(//div[@class="vxe-tree--node-wrapper node--level-1"])[last()]'))).click()
        #点击新增人员权限按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="left flex flex-y-center"]//button[span[text()="新增人员权限"]]'))).click()
        time.sleep(1)
        #增加权限
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@class="el-dialog__body"]//tbody/tr[1]/td[5]//span'))).click()
        time.sleep(1)

        #查询
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))
        if text.text != "修改成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增人员权限失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "修改成功"
    except Exception as e:
        raise e



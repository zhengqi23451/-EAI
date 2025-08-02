from conftest import  *

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


#进入部门设置界面

@pytest.fixture(scope="module")
def navigate_to_department(driver, login):
    """导航到考勤分类页面"""
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
        #点击组织架构设置
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div[2]/li/div/span[text()="组织架构设置"]'))).click()
        #点击部门设置
        wait.until(EC.element_to_be_clickable((By.XPATH,'//div[@class="sidebar-container"]/div[@class="el-scrollbar"]/div[@class="scrollbar-wrapper el-scrollbar__wrap"]/div/ul/div[2]/li/ul/div[2]/li/ul/div[2]/a/li/span[text()="部门设置"]'))).click()
        # 验证页面加载
        time.sleep(2)
        title = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[@class="main-container"]/section/div/div/div[@class="table-info-bar flex flex-x-sb flex-y-center"]/div[@class="left flex flex-y-center"]/span[@class="title"]')))
        if title.text!="部门设置" :
            highlight_element(driver,title)
            allure.attach(driver.get_screenshot_as_png(), name="导航部门设置页面失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver, title)
        assert title.text == "部门设置"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("部门名称查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_name(driver,navigate_to_department):
    wait = WebDriverWait(driver, 20)
    try:
        #查询框
        name = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form[contains(@class,"search-form")]/div[@class="el-row"]/div[1]/div/div[@class="el-form-item__content"]/div/input')))
        name.send_keys("test")
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()

        #部门结构下的数据是test
        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[2]/div/div/div[@class="vxe-cell--tree-node"]/div[@class="vxe-tree-cell"]/span')))
        if text.text != "test":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="部门名称查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "test"
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("部门状态查询")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_search_state(driver,navigate_to_department):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击部门状态下拉框
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[@class="el-row"]/div[2]/div/div[@class="el-form-item__content"]/div/div/input'))).click()
        #选择禁用
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class, "el-select-dropdown")]/div[contains(@class, "el-scrollbar")]/div[contains(@class, "el-select-dropdown__wrap")]/ul/li/span[text()="禁用"]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
        time.sleep(1)

        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[1]/td[11]/div/div[@class="vxe-cell--wrapper"]/span')))
        if text.text != "禁用":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="部门状态查询失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "禁用"
        #点击重置按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[1]'))).click()
        #点击查询按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(@class,"app-container")]/form/div[contains(@class,"search-btns")]/button[2]'))).click()
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("新增部门")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_add(driver,navigate_to_department):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击新增按钮
        add=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(@class, "el-button--success")]/span[contains(text(), "新增")]')))
        add.click()

        #点击上级部门下拉框
        e=wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//form[@class='el-form']//div[@class='el-form-item__content']/div/div[contains(@class,'el-input--suffix')]/input")))
        e.click()
        #点击选择董事长
        ele = wait.until(EC.element_to_be_clickable(
            (By.XPATH,'//div[@class="el-cascader-panel"]//li[contains(@class,"el-cascader-node")]/label/span/span[@class="el-radio__inner"]')))
        ele.click()
        #点击标签将选择框关闭
        e.click()
        #输入部门名称
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//form[@class='el-form']/div[2]/div/div/input"))).send_keys("test")
        #点击保存
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-dialog__footer']/div/button[contains(@class,'el-button--success')]/span[text()='保存']"))).click()

        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "新增成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="新增部门失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "新增成功"
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("编辑部门")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_modify(driver,navigate_to_department):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击编辑按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[6]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-primary")]'))).click()
        #点击保存按钮
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-dialog__footer']/div/button[contains(@class,'el-button--success')]/span[text()='保存']"))).click()

        text=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="部门修改失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "更新成功"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("删除部门")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_delete(driver,navigate_to_department):
    wait = WebDriverWait(driver, 20)
    time.sleep(3)
    try:
        #点击删除//*[@id="app"]/div/div[3]/section/div/div[1]/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[33]/td[12]/div/div/button[3]/span
        element=wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//tbody/tr[34]/td[contains(@class,"col--last")]/div/div/button[contains(@class,"font-danger")]')))
        #driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()
        #点击确认
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-message-box']/div[@class='el-message-box__btns']/button[contains(@class,'el-button--primary')]"))).click()

        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "删除成功！":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="考勤分类删除失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "删除成功！"
    except Exception as e:
        raise e

@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("编辑排序")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_move(driver, navigate_to_department):
    wait = WebDriverWait(driver, 30)
    time.sleep(3)
    try:
        # 点击编辑排序
        element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(@class, "el-button--primary")]/span[contains(text(), "编辑排序")]')))
        #driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()
        # 点击董事办
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='el-dialog__body']//div[contains(@class,'el-tree') and contains(@class,'el-tree-node')]/div[contains(@class,'el-tree-node__content')]/span[text()='董事办']"))).click()

        # 找到需要拖动的元素和目标位置
        source_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'el-tree-node__children')]/div[3]/div")))  # 第一个元素
        target_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'el-tree-node__children')]/div[5]/div")))  # 第三个元素

        time.sleep(0.5)
        # 使用JavaScript进行拖拽
        driver.execute_script("""
            function simulateDragDrop(sourceNode, destinationNode) {
                var EVENT_TYPES = {
                    DRAG_END: 'dragend',
                    DRAG_START: 'dragstart',
                    DROP: 'drop',
                    DRAG_OVER: 'dragover',
                    DRAG_ENTER: 'dragenter',
                    DRAG_LEAVE: 'dragleave'
                };

                function createCustomEvent(type) {
                    var event = new CustomEvent("CustomEvent");
                    event.initCustomEvent(type, true, true, null);
                    event.dataTransfer = {
                        data: {},
                        setData: function(type, val) {
                            this.data[type] = val;
                        },
                        getData: function(type) {
                            return this.data[type];
                        }
                    };
                    return event;
                }

                function dispatchEvent(node, type, event) {
                    if (node.dispatchEvent) {
                        return node.dispatchEvent(event);
                    }
                    if (node.fireEvent) {
                        return node.fireEvent("on" + type, event);
                    }
                }

                var event = createCustomEvent(EVENT_TYPES.DRAG_START);
                dispatchEvent(sourceNode, EVENT_TYPES.DRAG_START, event);

                // 调整目标元素的位置
                var targetRect = destinationNode.getBoundingClientRect();
                var targetX = targetRect.left + targetRect.width / 2;
                var targetY = targetRect.top - 10; // 向上偏移10像素

                var dragOverEvent = createCustomEvent(EVENT_TYPES.DRAG_OVER);
                dragOverEvent.clientX = targetX;
                dragOverEvent.clientY = targetY;
                dispatchEvent(destinationNode, EVENT_TYPES.DRAG_OVER, dragOverEvent);

                var dropEvent = createCustomEvent(EVENT_TYPES.DROP);
                dropEvent.dataTransfer = event.dataTransfer;
                dropEvent.clientX = targetX;
                dropEvent.clientY = targetY;
                dispatchEvent(destinationNode, EVENT_TYPES.DROP, dropEvent);

                var dragEndEvent = createCustomEvent(EVENT_TYPES.DRAG_END);
                dragEndEvent.dataTransfer = event.dataTransfer;
                dispatchEvent(sourceNode, EVENT_TYPES.DRAG_END, dragEndEvent);
            }

            var source = arguments[0];
            var target = arguments[1];
            simulateDragDrop(source, target);
            """, source_element, target_element)

        text = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//p[@class="el-message__content"]')))

        if text.text != "排序号更新成功":
            highlight_element(driver, text)
            allure.attach(driver.get_screenshot_as_png(), name="排序号更新失败截图",
                          attachment_type=allure.attachment_type.PNG)
            reset_element(driver, text)
        assert text.text == "排序号更新成功"
    except Exception as e:
        raise e


@allure.epic("人力资源设置")
@allure.feature("组织架构设置")
@allure.story("部门设置")
@allure.description("样式比较")
@pytest.mark.parametrize("driver",['chrome'],indirect=True)
def test_file_style(driver, navigate_to_department):
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
        # 新增1按钮样式
        'add1_button': {
            'background-color': 'rgb(0, 150, 136)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 编辑排序按钮样式
        'sort_button': {
            'background-color': 'rgb(60, 141, 188)',
            'color': 'rgb(255, 255, 255)',
            'border-radius': '2px',
            'width': '76px',
            'height': '28px'
        },
        # 折叠按钮样式
        'fold_button': {
            'background-color': 'rgb(60, 141, 188)',
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
        # 新增按钮样式
        'add_button': {
            'background-color': 'rgb(0, 0, 0)',
            'color': 'rgb(0, 185, 130)',
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

        # 测试新增1按钮样式
        add1_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div[1]/div[1]/div[2]/button[1]')))
        actual_styles = {
            'background-color': to_rgb(add1_button.value_of_css_property('background-color')),
            'color': to_rgb(add1_button.value_of_css_property('color')),
            'border-radius': add1_button.value_of_css_property('border-radius'),
            'width': add1_button.value_of_css_property('width'),
            'height': add1_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['add1_button']:
            highlight_element(driver,add1_button)
            allure.attach(driver.get_screenshot_as_png(), name="add1按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,add1_button)
        assert actual_styles == expected_styles['add1_button'], f"add1按钮样式不匹配: {actual_styles}"

        # 测试编辑排序按钮样式
        sort_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div[1]/div[1]/div[2]/button[2]')))
        actual_styles = {
            'background-color': to_rgb(sort_button.value_of_css_property('background-color')),
            'color': to_rgb(sort_button.value_of_css_property('color')),
            'border-radius': sort_button.value_of_css_property('border-radius'),
            'width': sort_button.value_of_css_property('width'),
            'height': sort_button.value_of_css_property('height')
        }
        if actual_styles != expected_styles['sort_button']:
            highlight_element(driver,sort_button)
            allure.attach(driver.get_screenshot_as_png(), name="编辑排序按钮样式匹配失败截图",attachment_type=allure.attachment_type.PNG)
            reset_element(driver,sort_button)
        assert actual_styles == expected_styles['sort_button'], f"编辑排序按钮样式不匹配: {actual_styles}"

        # 测试折叠按钮样式
        fold_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div[1]/div[1]/div[2]/button[3]')))
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
            reset_element(driver,fold_button)
        assert actual_styles == expected_styles['fold_button'], f"折叠按钮样式不匹配: {actual_styles}"




        #编辑按钮样式
        modify_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div[1]/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[12]/div/div/button[2]')))
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
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div[1]/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[12]/div/div/button[3]')))
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

        #新增按钮样式
        add_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app"]/div/div[3]/section/div/div[1]/div[2]/div/div[3]/div[1]/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td[12]/div/div/button[1]')))
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

    except Exception as e:
        # 截图并附加到 Allure 报告

        raise e

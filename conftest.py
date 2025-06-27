# conftest.py
import pytest
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # 每个测试结束后执行
    if hasattr(pytest, 'driver') and pytest.driver:
        pytest.driver.delete_all_cookies()
        pytest.driver.execute_script("window.localStorage.clear();")


def pytest_configure(config):
    config.option.allure_report_dir = "allure-results"
    config.option.allure_language = "zh"
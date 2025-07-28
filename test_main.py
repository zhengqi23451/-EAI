import pytest
import allure

@allure.step("最小测试")
def test_min():
    assert 1 == 1
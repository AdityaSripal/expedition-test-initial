import pytest
import yaml
from functools import reduce
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


attributes = {"ID": By.ID, "TAG_NAME": By.TAG_NAME, "NAME": By.NAME, "CLASS_NAME": By.CLASS_NAME, "XPATH": By.XPATH}
special_keys = {"RETURN": Keys.RETURN, "NULL": Keys.NULL, "TAB": Keys.TAB}

def pytest_collect_file(parent, path):
    if path.ext == ".yml" and path.basename.startswith("test"):
        return YamlFile(path, parent)

def preprocess(driver, raw):
    args = reduce(lambda x, y: dict(x, **y), raw, {"uid_type": "ID"}) # turns list of 1 pair dictionaries into 1 dictionary
    if "driver" in args:
        driver = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, args["driver"])))
        del args["driver"]
    return driver, args

def url(driver, args):
    link = args["url"]
    driver.get(link)

def input(driver, args):
    field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((attributes[args["uid_type"]], args["uid"])))
    field.clear()
    field.send_keys(args["content"])
    if "key" in args:
        field.send_keys(special_keys[args["key"]])

def click(driver, args):
    button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((attributes[args["uid_type"]], args["uid"])))
    #button.send_keys(Keys.NULL)
    button.click()

function_dispatch = {"url": url, "input": input, "click": click}

class YamlFile(pytest.File):
    def collect(self):
        raw = yaml.safe_load(self.fspath.open())
        self.driver = webdriver.Chrome()
        for name, actions in raw.items():
            yield Action(name, self, self.driver, actions)

class Action(pytest.Item):
    def __init__(self, name, parent, driver, actions):
        super(Action, self).__init__(name, parent)
        self.actions = actions
        self.driver = driver
        driver.get("https://10.5.172.196/")

    def runtest(self):
        for item in self.actions:
            dispatch, args = item.popitem()
            function = function_dispatch[dispatch]
            driver, args_dict = preprocess(self.driver, args)
            function(driver, args_dict)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException, ElementNotInteractableException)
import time


options_list = driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li//div[@class='zsRT0d']")
for i in options_list:
    print(i.text)



combined_origin_list = [str(i) + " (" + str(j) + ")" for i, j in zip(origin_options, airport_codes)]
print(combined_origin_list)
return combined_origin_list


    # Airport codes
#    available_airports = driver.find_elements(By.CLASS_NAME, "yfemgb")
#    print(len(available_airports))
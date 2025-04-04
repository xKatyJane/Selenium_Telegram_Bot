from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException, ElementNotInteractableException)
import time
import re

service = Service(executable_path="/Users/katia/Selenium_Chromedriver/chromedriver")
driver = webdriver.Chrome(service=service)

def get_google_flights():
    driver.get("https://www.google.com/travel/flights")

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='lssxud']//button)[2]")))
    button = driver.find_element(By.XPATH, "(//div[@class='lssxud']//button)[2]")
    button.click()

def origin():
    global origin_options

    # Input: origin
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[1]")))
    origin_input = driver.find_element(By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[1]")
    origin_input.clear()
    origin_input.send_keys("Paris")

    # Open buttons to see details of each location
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='DFGgtd']//button")))
    opening_buttons = driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']//button")
    print(len(opening_buttons))
    for button in opening_buttons[1:]:
        button.click()

    # Collecting origin options
        origin_options = []
        options_list = driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li//div[@class='CwL3Ec']/div[1]")
        for i in options_list:
            origin_options.append(i.text)

        # Grouping int main destinations and subcategories
        grouped_origin_options = {}
        current_main_origin =  None

        pattern = r"[A-Za-z\s]+([A-Z]{3})$"

        for option in origin_options:
            if "," in option:
                current_main_origin = option
                grouped_origin_options[current_main_origin] = []
            elif re.search(pattern, option):
                option = option[:-3] + ", " + option[-3:]
                if current_main_origin:
                    grouped_origin_options[current_main_origin].append(option)
        
        for main, subcategories in grouped_origin_options.items():
            print(f"{main}:")
            for sub in subcategories:
                print(f"  - {sub}")
            print()
        main_origin_options = list(grouped_origin_options.keys())
        print(main_origin_options)

        chosen_main_origin = main_origin_options[1]

        origin_specific_options = [chosen_main_origin]
        for sub in grouped_origin_options[chosen_main_origin]:
            origin_specific_options.append(sub)
        print(origin_specific_options)

    # Plane
    
    origin_divs = driver.find_elements(By.CLASS_NAME, "CwL3Ec")
    print(len(origin_divs))
    airport_divs = [div for div in origin_divs if len(div.find_elements(By.TAG_NAME, 'div')) == 2]
    print(len(airport_divs))

    
    #print(len(available_airports))
    #available_airports = driver.find_elements(By.CLASS_NAME, "yfemgb")


    # Collecting airport codes
    airport_codes = []
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='DFGgtd']/li//div[@class='P1pPOe']")))
    sel_airport_codes = driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li//div[@class='P1pPOe']")
    for code in sel_airport_codes:
        airport_codes.append(code.text)
    print(airport_codes)

def origin_decision(origin_options):
    user_origin_decision = origin_options[3]
    option_buttoon = driver.find_element(By.XPATH, f"//*[contains(text(), '{user_origin_decision}')]")
    option_buttoon.click()
    
def destination():

    # Input the destination
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[2]")))
    destination_input = driver.find_element(By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[2]")
    destination_input.clear()
    destination_input.send_keys("Miami")











get_google_flights()
origin()
#origin_decision(origin_options)
#destination()

time.sleep(5)
driver.quit()
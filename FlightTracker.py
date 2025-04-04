from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException, ElementNotInteractableException)
import time
import re
import FlightHawkBot


class FlightTracker():

    def __init__(self, context):
        self.context = context
        self.flight_type_choice = context.user_data.get("flight_type_choice", None)
        self.origin_main_choice = context.user_data.get("origin_main_choice", None)
        self.origin_specific_choice = context.user_data.get("origin_specific_choice", None)
#        self.grouped_origin_options = context.user_data['grouped_origin_options', None]
        self.driver = None
#        options = webdriver.ChromeOptions()
#        options.add_argument("--headless")
#        self.driver = webdriver.Chrome(service=self.service)
#        self.service = Service(executable_path="/Users/katia/Selenium_Chromedriver/chromedriver")
#        self.driver.get("https://www.google.com/travel/flights")
        
        # Functions

#        self.get_google_flights()
#        self.origin_main(context)
#        self.origin_specific(main_origin_options)
#        self.origin_decision(origin_options)

    def get_google_flights(self):

        options = webdriver.ChromeOptions()
        self.service = Service(executable_path="/Users/katia/Selenium_Chromedriver/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get("https://www.google.com/travel/flights")

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='lssxud']//button)[2]")))
        button = self.driver.find_element(By.XPATH, "(//div[@class='lssxud']//button)[2]")
        button.click()
        
    def origin_main(self, context):
        global grouped_origin_options, main_origin_options

        # Flight type: one way, return, multi-city
        flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
        if flight_type_choice == "One Way":
            print(flight_type_choice)

        # Input: origin
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[1]")))
        origin_input = self.driver.find_element(By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[1]")
        origin_input.clear()
        origin_input.send_keys(self.origin_main_choice)

        # Open buttons to see details of each location
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='DFGgtd']//button")))
        opening_buttons = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']//button")
        for button in opening_buttons[1:]:
            button.click()

        # Collecting origin options
        origin_options = []
#        options_list = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li//div[@class='zsRT0d']")
        options_list = self.driver.find_elements(By.XPATH, "//div[@class='CwL3Ec']/div[1]")
        for i in options_list:
            origin_options.append(i.text)

        # Grouping into main destinations and subcategories
        grouped_origin_options = {}
        current_main_origin =  None

        # Finding the main destinations (contain ",") and airports (contain 3 capitalized letters in the end)
        pattern = r"[A-Za-z\s]+([A-Z]{3})$"
        for option in origin_options:
            if "," in option:
                current_main_origin = option
                grouped_origin_options[current_main_origin] = []
            elif re.search(pattern, option):
                option = option[:-3] + ", " + option[-3:]
                if current_main_origin:
                    grouped_origin_options[current_main_origin].append(option)
        main_origin_options = [str(key) for key in grouped_origin_options.keys()]
        context.user_data["grouped_origin_options"] = grouped_origin_options

        return main_origin_options

    def origin_specific(self, context):

        origin_specific_choice = context.user_data.get("origin_specific_choice", "Default Value")
        print(origin_specific_choice)
        for key in grouped_origin_options:
            if key == origin_specific_choice:
                origin_specific_options = [key] + grouped_origin_options.get(origin_specific_choice, [])
        print(origin_specific_options)
        return origin_specific_options
#        chosen_main_origin = main_origin_options[1]

#        origin_specific_options = [chosen_main_origin]
#        for sub in grouped_origin_options[chosen_main_origin]:
#            origin_specific_options.append(sub)
        
#        print(origin_specific_options)



    def origin_decision(self, origin_options):
        user_origin_decision = origin_options[3]
        option_buttoon = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{user_origin_decision}')]")
        option_buttoon.click()
        
    def destination(self):

        # Input the destination
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[2]")))
        destination_input = self.driver.find_element(By.XPATH, "(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[2]")
        destination_input.clear()
        destination_input.send_keys("Miami")








#if __name__ == "__main__":
#    app = FlightTracker()
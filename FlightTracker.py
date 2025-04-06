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

        if "driver" in context.user_data:
            self.driver = context.user_data["driver"]
        else:
            options = webdriver.ChromeOptions()
            self.service = Service(executable_path="/Users/katia/Selenium_Chromedriver/chromedriver")
            self.driver = webdriver.Chrome(service=self.service, options=options)
            context.user_data["driver"] = self.driver



        self.flight_type_choice = context.user_data.get("flight_type_choice", None)
        self.origin_preliminary_choice = context.user_data.get("origin_preliminary_choice", None)
        self.origin_main_choice = context.user_data.get("origin_main_choice", None)
        self.origin_specific_choice = context.user_data.get("origin_specific_choice", None)
#        self.grouped_origin_options = context.user_data['grouped_origin_options', None]
#        self.driver = None
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

#        options = webdriver.ChromeOptions()
#        self.service = Service(executable_path="/Users/katia/Selenium_Chromedriver/chromedriver")
#        self.driver = webdriver.Chrome(service=self.service)
        if self.driver.current_url != "https://www.google.com/travel/flights":
            self.driver.get("https://www.google.com/travel/flights")

            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='lssxud']//button)[2]")))
            button = self.driver.find_element(By.XPATH, "(//div[@class='lssxud']//button)[2]")
            button.click()

    def flight_type(self, context):
        # Flight type: one way, return, multi-city
        flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
        if flight_type_choice == "One Way":
            print(flight_type_choice)

    def main_choice(self, context, input_box, input_value):
        global grouped_origin_options, main_origin_options

        # Input: origin
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, f"(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[{input_box}]")))
        origin_input = self.driver.find_element(By.XPATH, f"(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[{input_box}]")
        origin_input.clear()
        origin_input.send_keys(input_value)

        # Open buttons to see details of each location
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='DFGgtd']//button")))
        opening_buttons = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']//button")
        for button in opening_buttons[1:]:
            button.click()

        # Collecting origin options
        origin_options = []
#        options_list = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li//div[@class='zsRT0d']")
        options_list = self.driver.find_elements(By.XPATH, f"//div[@class='CwL3Ec']/div[1]")
        for i in options_list:
            origin_options.append(i.text)

        # Grouping into main destinations and subcategories
        grouped_origin_options = {}
        current_main_origin =  None

        # Finding the main destinations (contain ",") and airports (contain 3 capitalized letters in the end)
        pattern = r"[A-Za-z\s]+([A-Z]{3})$"
        for option in origin_options:
            if option == origin_options[0] or "," in option:
                current_main_origin = option
                grouped_origin_options[current_main_origin] = []
            elif re.search(pattern, option):
                option = option[:-3] + ", " + option[-3:]
                if current_main_origin:
                    grouped_origin_options[current_main_origin].append(option)
        main_origin_options = [str(key) for key in grouped_origin_options.keys()]
        context.user_data["grouped_origin_options"] = grouped_origin_options

        return main_origin_options

    def specific_choice(self, context, main_choice):
        specific_options = []
        for key in grouped_origin_options:
            if key == main_choice:
                specific_options = [key] + grouped_origin_options.get(main_choice, [])
        return specific_options

    def confirm_decision(self, context, specific_choice):
    #    origin_specific_choice = context.user_data.get("origin_specific_choice", "Default Value")

        pattern = r"[A-Za-z\s]+([A-Z]{3})$"
        if re.search(pattern, specific_choice):
            specific_choice_search = specific_choice[:-5]
        else: 
            specific_choice_search = specific_choice
        print(specific_choice_search)

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{specific_choice_search}')]")))
        origin_specific_choice_element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{specific_choice_search}')]")
        origin_specific_choice_element.click()





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
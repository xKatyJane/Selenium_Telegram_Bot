from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException, ElementNotInteractableException)
import time
import re
import FlightHawkBot
from FlightDataManager import FlightDataManager
from datetime import datetime, timedelta


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
        self.destination_preliminary_choice = context.user_data.get("destination_preliminary_choice", None)
        self.destination_main_choice = context.user_data.get("destination_main_choice", None)
        self.destination_specific_choice = context.user_data.get("destination_specific_choice", None)
        self.date_choice = context.user_data.get("date_choice", None)
        self.return_date_choice = context.user_data.get("return_date_choice", None)
#        self.grouped_origin_options = context.user_data['grouped_origin_options', None]
#        self.driver = None
#        options = webdriver.ChromeOptions()
#        options.add_argument("--headless")
#        self.driver = webdriver.Chrome(service=self.service)
#        self.service = Service(executable_path="/Users/katia/Selenium_Chromedriver/chromedriver")
#        self.driver.get("https://www.google.com/travel/flights")
        


        


    def get_google_flights(self):
        ''' Gets the Google Flights URL '''

#        if self.driver.current_url != "https://www.google.com/travel/flights":
        if not self.driver.current_url.startswith("https://www.google.com/travel/flights"):
            self.driver.get("https://www.google.com/travel/flights")
            try:
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='lssxud']//button)[2]")))
                button = self.driver.find_element(By.XPATH, "(//div[@class='lssxud']//button)[2]")
                button.click()
            except:
                pass
        else:
            pass

    def flight_type(self, context):
        ''' Chooses flight type (one way, round trip or multi-city) '''

        # Flight type: one way, return, multi-city
        flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='Maqf5d']/div[1]")))
        flight_type_choice_dropdown = self.driver.find_element(By.XPATH, "//div[@class='Maqf5d']/div[1]")
        flight_type_text_on_dropdown = flight_type_choice_dropdown.text
        if flight_type_text_on_dropdown == flight_type_choice:
            pass
        else:
            flight_type_choice_dropdown.click()
            if flight_type_choice == "Round trip":
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='Maqf5d']//ul/li[1]")))
                flight_type_option_round_trip = self.driver.find_element(By.XPATH, "//div[@class='Maqf5d']//ul/li[1]")
                flight_type_option_round_trip.click()
            elif flight_type_choice == "One way":
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='Maqf5d']//ul/li[2]")))
                flight_type_option_one_way = self.driver.find_element(By.XPATH, "//div[@class='Maqf5d']//ul/li[2]")
                flight_type_option_one_way.click()
        WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        self.driver.find_element(By.TAG_NAME, 'body').click()

    def main_choice(self, context, input_box, input_value):
        ''' Enters user's origin / destination choice into the entry field, collects a list of options, groups them into main options and subcategories '''
        global grouped_origin_destination_options, main_origin_destination_options

        # Locating input element
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[{input_box}]")))
        origin_destination_input = self.driver.find_element(By.XPATH, f"(//div[contains(@class, 'wUiEcc')]/div/div/div/input)[{input_box}]")
        origin_destination_input.clear()
        origin_destination_input.send_keys(input_value)
        
        # Opening buttons to see details of each location
        try:
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='DFGgtd']//button")))
            opening_buttons = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']//button")
            for button in opening_buttons[1:]:
                button.click()
        except:
            try:
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rZ2Tg']")))
                no_locations_found_alert = self.driver.find_element(By.XPATH, "//div[@class='rZ2Tg']")
                if no_locations_found_alert:
                    WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    self.driver.find_element(By.TAG_NAME, 'body').click()
                    main_origin_destination_options = []
                    grouped_origin_destination_options = {}
                    return
            except:
                pass
            

        grouped_origin_destination_options = {}
        # Collecting origin / destination options
        origin_destination_options = []
        options_list = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li")
        
        for i in options_list:
            data_type = i.get_attribute("data-type")
            if data_type == "3":
                current_main_option = i.text.split("\n")[0]
                grouped_origin_destination_options[current_main_option] = []
            elif data_type == "1" and current_main_option:
                try:
                    if i.text.split("\n")[1].split()[1] == "km":
                        option = i.text.split("\n")[0]
                        option = option[:-3] + ", " + option[-3:]
                        grouped_origin_destination_options[current_main_option].append(option)
                except:
                    pass
#        for main_category, subcategories in grouped_origin_destination_options.items():
#            print(f"Main Category: {main_category}")
#            for subcategory in subcategories:
#                print(f"  - Subcategory: {subcategory}")

        main_origin_destination_options = [str(key) for key in grouped_origin_destination_options.keys()]
        context.user_data["grouped_origin_destination_options"] = grouped_origin_destination_options

        return main_origin_destination_options

    def specific_choice(self, context, main_choice):
        specific_options = []
        for key in grouped_origin_destination_options:
            if key == main_choice:
                specific_options = [key] + grouped_origin_destination_options.get(main_choice, [])
        return specific_options

    def confirm_decision(self, context, specific_choice):
        ''' Clicks on the selected origin and destination '''

        pattern = r"[A-Za-z\s]+([A-Z]{3})$"
        if re.search(pattern, specific_choice):
            specific_choice_search = specific_choice[:-5]
        else: 
            specific_choice_search = specific_choice

        specific_choice_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{specific_choice_search}')]")))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", specific_choice_element)
        specific_choice_element.click()

    def date(self, context):
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")))
        date_input = self.driver.find_element(By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")
        date_input.clear()
        date_input.send_keys(self.date_choice)
        date_input.send_keys(Keys.RETURN)
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='xFFcie']/button")))
        search_button = self.driver.find_element(By.XPATH, "//div[@class='xFFcie']/button")
        search_button.click()

    def return_date(self, context):
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")))
        date_input = self.driver.find_element(By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")
        date_input.clear()
        date_input.send_keys(self.date_choice)
        date_input.send_keys(Keys.RETURN)
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Return']")))
        return_date_input = self.driver.find_element(By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Return']")
        return_date_input.clear()
        return_date_input.send_keys(self.return_date_choice)
        return_date_input.send_keys(Keys.RETURN)
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='xFFcie']/button")))
        search_button = self.driver.find_element(By.XPATH, "//div[@class='xFFcie']/button")
        search_button.click()

    def fetch_flight_data(self, context):
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='Rk10dc']/li[@class='pIav2d']//div[@class='yR1fYc']")))
        found_flight_infos = self.driver.find_elements(By.XPATH, "//ul[@class='Rk10dc']/li[@class='pIav2d']//div[@class='yR1fYc']")
        print(len(found_flight_infos))
        flight_infos = [e for e in found_flight_infos if e.is_displayed()]
        print(len(flight_infos))

        flight_info = []
        for index in range(len(flight_infos)):
            try:
                i = flight_infos[index]
                i_text = i.text
                flight_data_manager = FlightDataManager(i_text, context)
                price_data_str = flight_data_manager.price_data_str(context)
                if price_data_str == "Price unavailable":
                    continue
                else:
                    price_str = re.search(r'\d+(?:[.,]?\d+)?', price_data_str)
                    price_str = price_str.group(0).replace(",", "")
                    price = int(price_str)
                    currency = re.sub(r'[\d.,\s]', '', price_data_str)
                departure_time = flight_data_manager.departure_time()
                arrival_time = flight_data_manager.arrival_time()
                airline = flight_data_manager.airline()
                flight_duration = flight_data_manager.flight_duration()
                airports = flight_data_manager.airports()
                nr_of_stops = flight_data_manager.nr_of_stops()
                departure_date = flight_data_manager.departure_date(context)
                arrival_date = flight_data_manager.arrival_date(context)

                flight = {
                    "airports": airports,
                    "departure_date": departure_date,
                    "departure_time": departure_time,
                    "arrival_date": arrival_date,
                    "arrival_time": arrival_time,
                    "airline": airline,
                    "flight_duration": flight_duration,
                    "nr_of_stops": nr_of_stops,
                    "price": price,
                    "currency": currency
                }
                flight_info.append(flight)
            except StaleElementReferenceException:
                print("⚠️ Skipped a stale element.")

        for idx, flight in enumerate(flight_info, start=1):
            print(f"\n✈️  Flight {idx}")
            print(f"  Airports:         {flight['airports']}")
            print(f"  Departure Date:   {flight['departure_date']}")
            print(f"  Departure Time:   {flight['departure_time']}")
            print(f"  Arrival Date:     {flight['arrival_date']}")
            print(f"  Arrival Time:     {flight['arrival_time']}")
            print(f"  Airline:          {flight['airline']}")
            print(f"  Duration:         {flight['flight_duration']}")
            print(f"  Number of Stops:  {flight['nr_of_stops']}")
            print(f"  Price:            {flight['price']}")
            print(f"  Currency:         {flight['currency']}")
        
        return flight_info
        














#if __name__ == "__main__":
#    app = FlightTracker()
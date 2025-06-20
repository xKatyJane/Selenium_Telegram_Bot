from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException, ElementNotInteractableException)
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
from FlightDataManager import FlightDataManager
from datetime import datetime, timedelta


class FlightTracker():

    def __init__(self, context):
        self.context = context

        if "driver" in context.user_data:
            self.driver = context.user_data["driver"]
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--headless")
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
        
    def get_google_flights(self):
        ''' Gets the Google Flights URL '''

        if not self.driver.current_url.startswith("https://www.google.com/travel/flights"):
            self.driver.get("https://www.google.com/travel/flights")
            try:
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='lssxud']//button)[2]")))
                button = self.driver.find_element(By.XPATH, "(//div[@class='lssxud']//button)[2]")
                button.click()
            except:
                pass
    
    def flight_type(self, context):
        ''' Chooses flight type (one way or round trip) '''

        # Flight type: one way or round trip
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
            
        # Collecting origin / destination options
        grouped_origin_destination_options = {}
        origin_destination_options = []
        time.sleep(0.5)
        options_list = self.driver.find_elements(By.XPATH, "//ul[@class='DFGgtd']/li")
        
        for i in options_list:
            data_type = i.get_attribute("data-type")
            if data_type == "3":
                if "," in i.text:
                    current_main_option = i.text.split("\n")[0]
                else:
                    current_main_option = i.text.replace("\n", ", ")
                grouped_origin_destination_options[current_main_option] = []
            elif data_type == "1" and current_main_option:
                try:
                    if i.text.split("\n")[1].split()[1] == "km":
                        option = i.text.split("\n")[0]
                        option = option[:-3] + ", " + option[-3:]
                        grouped_origin_destination_options[current_main_option].append(option)
                except:
                    pass

        main_origin_destination_options = [str(key) for key in grouped_origin_destination_options.keys()]
        context.user_data["grouped_origin_destination_options"] = grouped_origin_destination_options

        return main_origin_destination_options

    def specific_choice(self, context, main_choice):
        ''' Groups origin / destination options into main categories and subcategories '''

        specific_options = []
        for key in grouped_origin_destination_options:
            if key == main_choice:
                specific_options = [key] + grouped_origin_destination_options.get(main_choice, [])
        return specific_options

    def confirm_decision(self, context, specific_choice):
        ''' Clicks on the selected origin and destination '''

        pattern = r"[A-Za-z\s]+([A-Z]{3})$"
        specific_choice = specific_choice.strip()
        if re.search(pattern, specific_choice):
            specific_choice_search = specific_choice[:-5]
        else: 
            specific_choice_search = specific_choice
        
        try:
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{specific_choice_search}')]")))
            specific_choice_element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{specific_choice_search}')]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", specific_choice_element)
            self.driver.execute_script("arguments[0].click();", specific_choice_element)
        except:
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//ul[@class='DFGgtd']/li[1]")))
            first_option = self.driver.find_element(By.XPATH, "//ul[@class='DFGgtd']/li[1]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_option)
            self.driver.execute_script("arguments[0].click();", first_option)

    def date(self, context):
        ''' Enters the chosen date, for one way flight '''

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")))
        date_input = self.driver.find_element(By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")
        self.driver.execute_script("arguments[0].value = '';", date_input)
        date_input.send_keys(self.date_choice)
        self.driver.execute_script("arguments[0].blur();", date_input)
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='xFFcie']/button")))
        search_button = self.driver.find_element(By.XPATH, "//div[@class='xFFcie']/button")
        self.driver.execute_script("arguments[0].click();", search_button)

    def date_change(self, context, date, is_return_flight: bool):

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//div[@class='rIZzse']//input[@aria-label='{date}']")))
        date_input = self.driver.find_element(By.XPATH, f"//div[@class='rIZzse']//input[@aria-label='{date}']")
        self.driver.execute_script("arguments[0].value = '';", date_input)
        if is_return_flight == False:
            date_input.send_keys(self.date_choice)
        elif is_return_flight == True:
            date_input.send_keys(self.return_date_choice)
        self.driver.execute_script("arguments[0].blur();", date_input)
    
    def return_date(self, context):
        ''' Enters the departure and return date choices, for round trip flight '''

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")))
        date_input = self.driver.find_element(By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Departure']")
        self.driver.execute_script("arguments[0].value = '';", date_input)
        date_input.send_keys(self.date_choice)
        self.driver.execute_script("arguments[0].blur();", date_input)
        time.sleep(1)

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Return']")))
        return_date_input = self.driver.find_element(By.XPATH, "//div[@class='rIZzse']//input[@aria-label='Return']")
        self.driver.execute_script("arguments[0].value = '';", return_date_input)
        return_date_input.send_keys(self.return_date_choice)
        self.driver.execute_script("arguments[0].blur();", return_date_input)
        time.sleep(1)

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='xFFcie']/button")))
        search_button = self.driver.find_element(By.XPATH, "//div[@class='xFFcie']/button")
        self.driver.execute_script("arguments[0].click();", search_button)

    def fetch_flight_data(self, context):
        ''' Fetches flights data '''

        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//li[@class='ZVk93d']//button")))
            see_more_flights = self.driver.find_element(By.XPATH, "//li[@class='ZVk93d']//button")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_more_flights)
            self.driver.execute_script("arguments[0].click();", see_more_flights)
        except:
            pass
        time.sleep(3)
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='Rk10dc']/li[@class='pIav2d']//div[@class='yR1fYc']")))
            found_flight_infos = self.driver.find_elements(By.XPATH, "//ul[@class='Rk10dc']/li[@class='pIav2d']//div[@class='yR1fYc']")
            flight_infos = [e for e in found_flight_infos if e.is_displayed()]
        except:
            return None

        flight_info = []
        for index in range(len(flight_infos)):
            try:
                i = flight_infos[index]
                i_text = i.text
                flight_data_manager = FlightDataManager(i_text, context)
                price_data_str = flight_data_manager.price_data_str(context)
                if price_data_str == "Price unavailable" or not price_data_str:
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

        return flight_info
    
    def fetch_return_flight_data(self, context):

        chosen_departure_flight = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{chosen_departure_flight}')]")))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen_departure_flight)

    def confirm_dep_flight_for_round_trip(self, selected_index, context):
        ''' Identifies the div with the data chosen by the user (departure flight) to click it and see the return flight data '''

        # Finding all divs
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='Rk10dc']/li[@class='pIav2d']//div[@class='yR1fYc']")))
        found_flight_infos = self.driver.find_elements(By.XPATH, "//ul[@class='Rk10dc']/li[@class='pIav2d']//div[@class='yR1fYc']")

        # Defining data and index to be matched
        flights = context.user_data.get("flights", "Default Value")
        selected_flight = flights[selected_index]
        flight_duration = selected_flight['flight_duration']
        price = selected_flight['price']

        # Finding the div with matching data
        matching_div = None
        for div in found_flight_infos:
            div_text = div.text
            if (
                flight_duration in div_text and
                str(price) in div_text
            ):
                matching_div = div
                break

        if matching_div:
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(matching_div))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", matching_div)
            matching_div.click()
        else:
            print("No matching div found, so couldn't expand the flight data.")

    def come_back_to_dep_flight(self, context):
        ''' Clicks on the button so go back to the departure flight '''

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='Su03E']")))
        change_button = self.driver.find_element(By.XPATH, "//div[@class='Su03E']")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", change_button)
        change_button.click()

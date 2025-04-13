from datetime import datetime, timedelta
from telegram.ext import Application, ContextTypes

class FlightDataManager():
    def __init__(self, flight_info_data, context):
        self.flight_info_data = flight_info_data
        self.context = context
        self.flight_type_choice = context.user_data.get("flight_type_choice", None)
        self.date_choice = context.user_data.get("date_choice", None)
        self.date_choice_datetime = datetime.strptime(self.date_choice, "%d %B %Y")
        self.flight_data_lines = flight_info_data.split("\n")

    def price_data_str(self, context):
        if self.flight_type_choice == "One way":
            if self.flight_data_lines[-1].strip().startswith("Avoids as much CO2e"):
                price_data_str = self.flight_data_lines[-2].strip()
            else:
                price_data_str = self.flight_data_lines[-1].strip()
        elif self.flight_type_choice == "Round trip":
            if self.flight_data_lines[-1].strip().startswith("Avoids as much CO2e"):
                price_data_str = self.flight_data_lines[-3].strip()
            else:
                price_data_str = self.flight_data_lines[-2].strip()

        return price_data_str
    
    def departure_time(self):
        departure_time = " ".join(self.flight_data_lines[0].split("\u202f")).strip()
        return departure_time
    
    def arrival_time(self):
        global arrival_time
        arrival_time = " ".join(self.flight_data_lines[2].split("\u202f")).strip()
        return arrival_time
    
    def airline(self):
        if self.flight_data_lines[3].strip() == "Self transfer":
            airline = self.flight_data_lines[4]
        else:
            airline = self.flight_data_lines[3]
        return airline
    
    def flight_duration(self):
        if self.flight_data_lines[3].strip() == "Self transfer":
            flight_duration = self.flight_data_lines[5].strip()
        else:
            flight_duration = self.flight_data_lines[4].strip()
        return flight_duration
    
    def airports(self):
        if self.flight_data_lines[3].strip() == "Self transfer":
            airports = self.flight_data_lines[6].strip()
        else:
            airports = self.flight_data_lines[5].strip()
            airports = airports.replace("-", " to ")
        return airports
    
    def nr_of_stops(self):
        if self.flight_data_lines[3].strip() == "Self transfer":
            nr_of_stops_str = self.flight_data_lines[7]
        else:
            nr_of_stops_str = self.flight_data_lines[6]

        if nr_of_stops_str == "Nonstop":
            nr_of_stops_str = 0
        else:
            nr_of_stops_str = nr_of_stops_str.split()[0].strip()
        nr_of_stops = int(nr_of_stops_str)
        return nr_of_stops
    
    def departure_date(self, context):
        date_choice_datetime = datetime.strptime(self.date_choice, "%d %B %Y")
        departure_date = self.date_choice_datetime.strftime("%d %B %Y")
        return departure_date
    
    def arrival_date(self, context):
        if arrival_time.endswith("AM") or arrival_time.endswith("PM"):
            arrival_date = self.date_choice_datetime.strftime("%d %B %Y")
        else:
            for i in range(1, 4):
                if arrival_time.endswith(f"+{i}"):
                    arrival_date_datetime = self.date_choice_datetime + timedelta(days=i)
                    arrival_date = arrival_date_datetime.strftime("%d %B %Y")
                    break
                elif arrival_time.endswith(f"-{i}"):
                    arrival_date_datetime = self.date_choice_datetime - timedelta(days=i)
                    arrival_date = arrival_date_datetime.strftime("%d %B %Y")
                    break
        return arrival_date
        







'''    def fetch_flight_data(self):
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
                flight_data_lines = i_text.split("\n")
                if self.flight_type_choice == "One way":
                    if flight_data_lines[-1].strip().startswith("Avoids as much CO2e"):
                        price_data_str = flight_data_lines[-2].strip()
                    else:
                        price_data_str = flight_data_lines[-1].strip()
                elif self.flight_type_choice == "Round trip":
                    if flight_data_lines[-1].strip().startswith("Avoids as much CO2e"):
                        price_data_str = flight_data_lines[-3].strip()
                    else:
                        price_data_str = flight_data_lines[-2].strip()
                if price_data_str == "Price unavailable":
                    continue
                else:
                    price_str = re.search(r'\d+(?:[.,]?\d+)?', price_data_str)
                    price_str = price_str.group(0).replace(",", "")
                    price = float(price_str)
                    currency = re.sub(r'[\d.,\s]', '', price_data_str)
                departure_time = " ".join(flight_data_lines[0].split("\u202f")).strip()
                arrival_time = " ".join(flight_data_lines[2].split("\u202f")).strip()
                if flight_data_lines[3].strip() == "Self transfer":
                    airline = flight_data_lines[4]
                    flight_duration = flight_data_lines[5].strip()
                    airports = flight_data_lines[6].strip()
                    nr_of_stops_str = flight_data_lines[7]
                else:
                    airline = flight_data_lines[3]
                    flight_duration = flight_data_lines[4].strip()
                    airports = flight_data_lines[5].strip()
                    nr_of_stops_str = flight_data_lines[6]
                if nr_of_stops_str == "Nonstop":
                    nr_of_stops_str = 0
                else:
                    nr_of_stops_str = nr_of_stops_str.split()[0].strip()
                nr_of_stops = int(nr_of_stops_str)
                date_choice_datetime = datetime.strptime(self.date_choice, "%d %B %Y")
                departure_date = date_choice_datetime.strftime("%d %B %Y")
                if arrival_time.endswith("AM") or arrival_time.endswith("PM"):
                    arrival_date = date_choice_datetime.strftime("%d %B %Y")
                else:
                    for i in range(1, 4):
                        if arrival_time.endswith(f"+{i}"):
                            arrival_date_datetime = date_choice_datetime + timedelta(days=i)
                            arrival_date = arrival_date_datetime.strftime("%d %B %Y")
                            break
                        elif arrival_time.endswith(f"-{i}"):
                            arrival_date_datetime = date_choice_datetime - timedelta(days=i)
                            arrival_date = arrival_date_datetime.strftime("%d %B %Y")
                            break

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
                print("⚠️ Skipped a stale element.")'''
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
            if self.flight_data_lines[-1].strip().startswith("Avoids as much CO2e") or self.flight_data_lines[-1].strip().endswith("emissions"):
                price_data_str = self.flight_data_lines[-3].strip()
            elif self.flight_data_lines[-1].strip() == "Price unavailable":
                price_data_str = self.flight_data_lines[-1].strip()
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
        if self.flight_data_lines[3].strip() == "Self transfer" or self.flight_data_lines[3].strip().startswith("Separate"):
            airline = self.flight_data_lines[4]
        else:
            airline = self.flight_data_lines[3]
        if "Operated" in airline:
            airline = airline.replace("Operated", ", Operated")
        return airline
    
    def flight_duration(self):
        if self.flight_data_lines[3].strip() == "Self transfer" or self.flight_data_lines[3].strip().startswith("Separate"):
            flight_duration = self.flight_data_lines[5].strip()
        else:
            flight_duration = self.flight_data_lines[4].strip()
        return flight_duration
    
    def airports(self):
        if self.flight_data_lines[3].strip() == "Self transfer" or self.flight_data_lines[3].strip().startswith("Separate"):
            airports = self.flight_data_lines[6].strip()
        else:
            airports = self.flight_data_lines[5].strip()
            airports = airports.replace("-", " to ")
        return airports
    
    def nr_of_stops(self):
        if self.flight_data_lines[3].strip() == "Self transfer" or self.flight_data_lines[3].strip().startswith("Separate"):
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
        
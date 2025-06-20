from datetime import datetime, timedelta

class DateParser():

    def __init__(self, date_str):
        self.date_str = date_str

    def transform_date(self):

        current_year = datetime.now().year
        date_str = self.date_str.strip().replace(",", "")
        parts = date_str.split()

        # Case like 18 July
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isalpha():
            try:
                parsed_date = datetime.strptime(f"{parts[0]} {parts[1]} {current_year}", "%d %B %Y")
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                return None
        
        # Case like July 18
        elif len(parts) == 2 and parts[0].isalpha() and parts[1].isdigit():
            try:
                parsed_date = datetime.strptime(f"{parts[1]} {parts[0]} {current_year}", "%d %B %Y")
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                return None
        
        # Case like 18 07
        elif len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            try:
                parsed_date = datetime.strptime(f"{parts[0]} {parts[1]} {current_year}", "%d %m %Y")
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                return None
        
        # Case like 18 July 2025
        elif len(parts) == 3 and parts[0].isdigit() and parts[1].isalpha() and parts[2].isdigit():
            try:
                parsed_date = datetime.strptime(f"{parts[0]} {parts[1]} {parts[2]}", "%d %B %Y")
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                return None
        
        # Case like July 18 2025
        elif len(parts) == 3 and parts[0].isalpha() and parts[1].isdigit() and parts[2].isdigit():
            try:
                parsed_date = datetime.strptime(f"{parts[1]} {parts[0]} {parts[2]}", "%d %B %Y")
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                return None
        
        # Case like 18 07 2025
        elif len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            try:
                parsed_date = datetime.strptime(f"{parts[0]} {parts[1]} {parts[2]}", "%d %m %Y")
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                return None
        
        for separator in [".", "/", "-"]:
            if separator in date_str:
                date_numeric_parts = date_str.split(separator)
                # Case like 18.07, 18/07, 18-07
                if len(date_numeric_parts) == 2 and date_numeric_parts[0].isdigit() and date_numeric_parts[1].isdigit():
                    try:
                        parsed_date = datetime(int(current_year), int(date_numeric_parts[1]), int(date_numeric_parts[0]))
                        return parsed_date.strftime("%d %B %Y")
                    except ValueError:
                        return None
                # Case like 18.07.2025, 18/07/2025, 18-07-2025
                elif len(date_numeric_parts) == 3 and date_numeric_parts[0].isdigit() and date_numeric_parts[1].isdigit() and date_numeric_parts[2].isdigit():
                    try:
                        parsed_date = datetime(int(date_numeric_parts[2]), int(date_numeric_parts[1]), int(date_numeric_parts[0]))
                        return parsed_date.strftime("%d %B %Y")
                    except ValueError:
                        return None
        
        return None
    
    def previous_day(self):

        date_choice_object = datetime.strptime(self.date_str, "%d %B %Y").date()
        previous_date_choice_object = date_choice_object - timedelta(days=1)
        previous_day = previous_date_choice_object.strftime("%d %B %Y")
        return previous_day
    
    def next_day(self):

        date_choice_object = datetime.strptime(self.date_str, "%d %B %Y").date()
        next_date_choice_object = date_choice_object + timedelta(days=1)
        next_day = next_date_choice_object.strftime("%d %B %Y")
        return next_day
import logging
import time
from dateutil import parser
from datetime import datetime, timedelta
import asyncio
import hashlib
from dotenv import load_dotenv
import os
import traceback
from FlightTracker import FlightTracker
from DateParser import DateParser
from DatabaseManager import DatabaseManager
from telegram import Update
from telegram import ReplyKeyboardMarkup
from telegram import KeyboardButton
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import BotCommand
from telegram.ext import CommandHandler
from telegram.ext import CallbackContext
from telegram.ext import JobQueue
from telegram.ext import ApplicationBuilder
from telegram.ext import ContextTypes
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import Application, MessageHandler, filters
from telegram.error import TelegramError, NetworkError, BadRequest, Forbidden, TimedOut


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
load_dotenv()
db_url = os.getenv('db_url')
db_manager = DatabaseManager(db_url=db_url)

FLIGHT_TYPE, ORIGIN_PRELIMINARY, ORIGIN_MAIN, ORIGIN_SPECIFIC, DESTINATION_PRELIMINARY, DESTINATION_MAIN, DESTINATION_SPECIFIC, FLIGHT_DATE, RETURN_DATE = range(9)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.first_name} requested help")
    help_text = (
        "🛫 <b>Flight Hawk Bot Guide</b>\n\n"
        "/start - Start searching for flights\n"
        "/bookmarks - View your saved flights\n"
        "/help - Show this help message\n"
        "/disclaimer - View bot info and disclaimer\n\n"
        "Use the on-screen buttons to navigate, bookmark, or delete flights.\n"
        "Currently supports One Way and Round Trip searches."
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def disclaimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.first_name} requested disclaimer")
    message = (
        "⚠️ *Disclaimer*\n\n"
        "This bot is an experimental project built for personal use and shared on GitHub. "
        "It scrapes data from Google Flights and is not officially affiliated with Google or any airline.\n\n"
        "Because the data is scraped from a third-party site, it may sometimes be inaccurate or unavailable, "
        "and the bot may break if the site changes.\n\n"
        "Use at your own discretion.\n\n"
        "For updates and source code, visit: [GitHub](https://github.com/xKatyJane/Selenium_Telegram_Bot)"
    )
    await update.message.reply_text(message, parse_mode='Markdown')

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "🔍 Flights Search"),
        BotCommand("bookmarks", "🎒 Bookmarks"),
        BotCommand("help", "ℹ️ Help"),
        BotCommand("disclaimer", "⚠️ Disclaimer")
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ''' Displays the welcome message and asks for flight type '''

    # Quit previous driver session if exists
    if "driver" in context.user_data:
        try:
            context.user_data["driver"].quit()
            logger.info(f"The driver was restarted by user {user.first_name}")
        except Exception as e:
            print(f"Error closing driver: {e}")
        finally:
            del context.user_data["driver"]
    
    # Remove previous context data if restarting driver
    keys_to_remove = [
        "flight_type_choice", "origin_preliminary_choice", "origin_main_choice",
        "origin_specific_choice", "destination_preliminary_choice", 
        "destination_main_choice", "destination_specific_choice",
        "date_choice", "return_date_choice", "page", "user_id"
    ]
    for key in keys_to_remove:
        if key in context.user_data:
            del context.user_data[key]

    # Initialize for the new user, display welcome message
    user = update.effective_user
    context.user_data['user_id'] = update.effective_user.id
    reply_keyboard = [["One way", "Round trip"]]

    await update.message.reply_text(
        '✈️ <b>Welcome to the Flight Hawk Bot!\n'
        '————————————————————\n'
        'I can help you to find cheap flights and track fare changes.\n</b>'
        'What type of flight are you looking for?\n',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return FLIGHT_TYPE

async def flight_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves flight type choice and asks for departure city '''

    user = update.message.from_user
    flight_type_choice = update.message.text.capitalize()
    logger.info(f"User {user.first_name} chose: {flight_type_choice}")
    context.user_data["flight_type_choice"] = flight_type_choice
    await update.message.reply_text(f"{flight_type_choice} it is! 🛫\nWhat is your departure city?")
    return ORIGIN_PRELIMINARY

async def choose_origin_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the option entered by the user (preliminary origin) and presents a list of matching origin options '''

    user = update.message.from_user
    origin_preliminary_choice = update.message.text
    logger.info(f"User {user.first_name} entered the departure city as: {origin_preliminary_choice}")
    context.user_data["origin_preliminary_choice"] = origin_preliminary_choice
    flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
    flight_tracker = FlightTracker(context)
    flight_tracker.get_google_flights()
    flight_tracker.flight_type(context)
    main_origin_options = flight_tracker.main_choice(context, 1, origin_preliminary_choice)

    if main_origin_options:
        reply_keyboard = [[option] for option in main_origin_options]
        await update.message.reply_text("📌 Choose an option from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        return ORIGIN_MAIN
    else:
        await update.message.reply_text("No such option found, please try again.")
        return ORIGIN_PRELIMINARY

async def choose_origin_specific(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the user's main origin choice, and if there are multiply airports in the chosen city, presents a list of airports '''

    user = update.message.from_user
    origin_main_choice = update.message.text
    logger.info(f"User {user.first_name} chose a main origin option: {origin_main_choice}")
    context.user_data["origin_main_choice"] = origin_main_choice
    flight_tracker = FlightTracker(context)
    flight_tracker.specific_choice(context, origin_main_choice)
    origin_specific_options = flight_tracker.specific_choice(context, origin_main_choice)

    if len(origin_specific_options)<=2:
        logger.info(f"User {user.first_name} selected an origin main with only one option: {origin_main_choice}, so not asking for specific origin.")
        context.user_data["origin_specific_choice"] = origin_main_choice
        flight_tracker.confirm_decision(context, origin_main_choice)
        await update.message.reply_text(f"🛬 Great! What is your destination city?")
        return DESTINATION_PRELIMINARY
    
    elif len(origin_specific_options)>2:
        reply_keyboard = [[option] for option in origin_specific_options]
        await update.message.reply_text("There are several airports available for this departure. Select an option from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        return ORIGIN_SPECIFIC

async def choose_departure_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the airport / specific origin choice and asks for the destination '''

    user = update.message.from_user
    origin_specific_choice = update.message.text
    logger.info(f"User {user.first_name} chose origin specific as: {origin_specific_choice}")
    context.user_data["origin_specific_choice"] = origin_specific_choice
    flight_tracker = FlightTracker(context)
    origin_specific_choice = context.user_data.get("origin_specific_choice")
    flight_tracker.confirm_decision(context, origin_specific_choice)
    await update.message.reply_text(f" 🛬 Great! What is your destination city?")
    return DESTINATION_PRELIMINARY

async def choose_destination_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the option entered by the user (preliminary destination) and presents a list of matching destination options '''

    user = update.message.from_user
    destination_preliminary_choice = update.message.text
    logger.info(f"User {user.first_name} entered the destination city as: {destination_preliminary_choice}")
    context.user_data["destination_preliminary_choice"] = destination_preliminary_choice
    destination_preliminary_choice = context.user_data.get("destination_preliminary_choice")
    flight_tracker = FlightTracker(context)
    main_destination_options = flight_tracker.main_choice(context, 2, destination_preliminary_choice)

    if main_destination_options:
        reply_keyboard = [[option] for option in main_destination_options]
        await update.message.reply_text("📌 Choose an option from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        return DESTINATION_MAIN
    else:
        await update.message.reply_text("No such option found, please try again.")
        return DESTINATION_PRELIMINARY

async def choose_destination_specific(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the user's main destination choice, and if there are multiply airports in the chosen city, presents a list of airports '''

    user = update.message.from_user
    destination_main_choice = update.message.text
    logger.info(f"User {user.first_name} chose a main destination option: {destination_main_choice}")
    context.user_data["destination_main_choice"] = destination_main_choice
    flight_tracker = FlightTracker(context)
    destination_specific_options = flight_tracker.specific_choice(context, destination_main_choice)

    if len(destination_specific_options)<=2:
        context.user_data["destination_specific_choice"] = destination_main_choice
        logger.info(f"User {user.first_name} selected a destination main with only one option: {destination_main_choice}, so not asking for specific destination.")
        await update.message.reply_text(f"Noted! 🗓️ What is the departure date?\nFor example: June 12, 12.06, 12.06.2025.")
        return FLIGHT_DATE
    elif len(destination_specific_options)>2:
        reply_keyboard = [[option] for option in destination_specific_options]
        await update.message.reply_text("There are several airports available for this destination. Select an option from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        return DESTINATION_SPECIFIC
    else:
        await update.message.reply_text("No such option found, please try again.")
        return DESTINATION_PRELIMINARY

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the airport / specific destination choice and asks for the date '''

    user = update.message.from_user
    destination_specific_choice = update.message.text
    logger.info(f"User {user.first_name} chose destination specific as: {destination_specific_choice}")
    context.user_data["destination_specific_choice"] = destination_specific_choice
    await update.message.reply_text("Noted! 🗓️ What is the departure date?\nFor example: June 12, 12.06, 12.06.2025.")
    return FLIGHT_DATE

async def confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the flight date, gets the flight info for one way flights, asks for return date for round trip flights '''

    user = update.message.from_user
    entered_date_choice = update.message.text
    logger.info(f"User {user.first_name} chose the date as: {entered_date_choice}")
    try:
        date_parser = DateParser(entered_date_choice)
        date_choice = date_parser.transform_date()
        logger.info(f"The entered flight date was parsed as: {date_choice}")
        date_choice_datetime = datetime.strptime(date_choice, "%d %B %Y")
        if date_choice_datetime.date() < datetime.now().date():
            await update.message.reply_text("This date is in the past. Please enter a future date.")
            logger.info("The entered flight date was rejected because it is in the past")
            return FLIGHT_DATE
    except:
        await update.message.reply_text("This is not the correct date format, please try again.")
        logger.info("The entered flight date was rejected by the parser because of incorrect format")
        return FLIGHT_DATE
    context.user_data["date_choice"] = date_choice
    if context.user_data.get("flight_type_choice") == "Round trip":
        await update.message.reply_text("And what is your return date?")
        return RETURN_DATE
    flight_tracker = FlightTracker(context)
    destination_specific_choice = context.user_data.get("destination_specific_choice")
    flight_tracker.confirm_decision(context, destination_specific_choice)
    flight_tracker.date(context)
    flights = flight_tracker.fetch_flight_data(context)
    if not flights:
        await update.message.reply_text("❌ No flights were found. Please try changing the data.\nYou can enter a new date.")
        logger.info(f"No flights found for user {user.first_name}")
        return FLIGHT_DATE
    logger.info(f"Found {len(flights)} flights for user {user.first_name}")
    await display_flight_results(flights, update, context)
    return ConversationHandler.END

async def choose_return_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the return flight date, gets the flight info for round trip flights '''

    user = update.message.from_user
    entered_return_date_choice = update.message.text
    logger.info(f"User {user.first_name} chose the return date as: {entered_return_date_choice}")
    try:
        date_parser = DateParser(entered_return_date_choice)
        return_date_choice = date_parser.transform_date()
        logger.info(f"The entered return flight date was parsed as: {return_date_choice}")
        date_choice = context.user_data.get("date_choice")
        if return_date_choice < date_choice:
            await update.message.reply_text("The return date cannot be before the departure date.")
            logger.info("The entered return flight date was rejected because it is before the departure date.")
            return RETURN_DATE
    except:
        await update.message.reply_text("This is not the correct date format, please try again.")
        logger.info("The entered return flight date was rejected by the parser")
        return RETURN_DATE
    context.user_data["return_date_choice"] = return_date_choice
    flight_tracker = FlightTracker(context)
    destination_specific_choice = context.user_data.get("destination_specific_choice")
    flight_tracker.confirm_decision(context, destination_specific_choice)
    flight_tracker.return_date(context)
    flights = flight_tracker.fetch_flight_data(context)
    await display_flight_results(flights, update, context)
    return ConversationHandler.END

async def display_flight_results(flights, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, show_all: bool = False, is_date_change: bool = False, is_return_flight: bool = False):
    ''' Displays a message with the flight ino to the user '''

    origin_specific_choice = context.user_data.get("origin_specific_choice")
    destination_specific_choice = context.user_data.get("destination_specific_choice")
    date_choice = context.user_data.get("date_choice")
    flights_per_page = 3
    start = page * flights_per_page
    end = len(flights) if show_all else start + flights_per_page
    if flights:
        current_flights = flights[start:end]
    else:
        current_flights = []
    return_date_choice = context.user_data.get("return_date_choice")
    
    # No flights found case
    if not flights:
        target = update.message or update.callback_query.message
        await target.reply_text("❌ No flights were found.")
        return
    
    # Main message body
    if context.user_data.get("flight_type_choice") == "One way":
        message = f"Flights from {origin_specific_choice} to {destination_specific_choice} on {date_choice}.\nI found a total of {len(flights)} flights.\n\n"
    elif context.user_data.get("flight_type_choice") == "Round trip":
        message = f"✈️ Flights between {origin_specific_choice} and {destination_specific_choice}.\nFlight dates: {date_choice} and {return_date_choice}.\n\n"
        if is_return_flight:
            message += f"✈️ Showing RETURN FLIGHTS.\nI found a total of {len(flights)} return flights.\n\n"
        else:
            message += f"✈️ Showing DEPARTURE FLIGHTS.\nI found a total of {len(flights)} departure options.\n\n"

    keyboard_one_way_flight_buttons = []
    keyboard_return_flight_buttons = []
    bookmarked = context.user_data.get("bookmarked_flights", set())
    for local_idx, flight in enumerate(current_flights):
        global_idx = start + local_idx
        display_idx = global_idx + 1 
        message += (
            f"✈️     <b>———— FLIGHT {display_idx} —————</b>  ✈️\n\n"
            f"📍    <b>Flight from: </b> {flight['airports']}\n"
            f"🛫    <b>Airline:</b> {flight['airline']}\n"
            f"🕘    <b>Departure:</b> {flight['departure_date']}, {flight['departure_time']}\n"
            f"🕒    <b>Arrival:</b> {flight['arrival_date']}, {flight['arrival_time']}\n"
            f"🔁    <b>Stops:</b> {flight['nr_of_stops']}\n"
            f"⌛    <b>Flight duration:</b> {flight['flight_duration']}\n"
            f"💰    <b>Price:</b> {flight['price']} {flight['currency']}\n"
        )

        # Defining the buttons for bookmarking / checking more details
        flight_data = f"{flight['airline']}_{flight['departure_date']}_{flight['departure_time']}_{flight['arrival_time']}_{flight['price']}"
        flight_id = hashlib.md5(flight_data.encode()).hexdigest()[:8]
        flight_mappings = context.user_data.get("flight_mappings", {})
        flight_mappings[flight_id] = flight_data
        context.user_data["flight_mappings"] = flight_mappings
        if context.user_data.get("flight_type_choice") == "One way":
            if flight_id in bookmarked:
                keyboard_one_way_flight_buttons.append([InlineKeyboardButton("✅ Bookmarked", callback_data="noop")])
            else:
                keyboard_one_way_flight_buttons.append([InlineKeyboardButton(f"🔍 Bookmark flight {display_idx}", callback_data=f"flight_{global_idx}_{flight_id}")])
        elif context.user_data.get("flight_type_choice") == "Round trip":
            if is_return_flight:
                if flight_id in bookmarked:
                    keyboard_one_way_flight_buttons.append([InlineKeyboardButton("✅ Bookmarked", callback_data="noop")])
                else:
                    keyboard_one_way_flight_buttons.append([InlineKeyboardButton(f"🔍 Bookmark flight {display_idx}", callback_data=f"return_flight_ret_{global_idx}_{flight_id}")])
            else:
                keyboard_return_flight_buttons.append([InlineKeyboardButton(f"🔍 Check this flight {display_idx}", callback_data=f"return_flight_dep_{global_idx}_{flight_id}")])

    # Message under the flight details
    if context.user_data.get("flight_type_choice") == "Round trip" and is_return_flight == False:
        message += "\nChoose a departing flight to see the details of a returning flight."
    if context.user_data.get("flight_type_choice") == "Round trip" and is_return_flight:
        message += "\n\n✈️ Showing RETURN FLIGHTS ✈️"
    elif context.user_data.get("flight_type_choice") == "Round trip" and not is_return_flight:
        message += f"\n\n✈️ Showing DEPARTURE FLIGHTS ✈️"
    
    # Extending the buttons for bookmarking / checking more details
    keyboard = []
    nav_buttons = []
    if context.user_data.get("flight_type_choice") == "One way":
        keyboard.extend(keyboard_one_way_flight_buttons)
    elif context.user_data.get("flight_type_choice") == "Round trip" and is_return_flight == False:
        keyboard.extend(keyboard_return_flight_buttons)
    elif context.user_data.get("flight_type_choice") == "Round trip" and is_return_flight == True:
        keyboard.extend(keyboard_one_way_flight_buttons)

    # Next / previous results buttons for pagination
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous results", callback_data=f"page_{page-1}"))
    if end < len(flights):
        nav_buttons.append(InlineKeyboardButton("Next results ➡️", callback_data=f"page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Date change buttons
    if context.user_data.get("flight_type_choice") == "One way":
        keyboard.append([
            InlineKeyboardButton("⬅️ Previous day", callback_data="date_previous_dep"),
            InlineKeyboardButton("Next day ➡️", callback_data="date_next_dep")])
    elif context.user_data.get("flight_type_choice") == "Round trip":
        keyboard.append([
            InlineKeyboardButton("⬅️ Previous departure day", callback_data="date_previous_dep"),
            InlineKeyboardButton("Next departure day ➡️", callback_data="date_next_dep")])
        keyboard.append([
            InlineKeyboardButton("⬅️ Previous return day", callback_data="date_previous_ret"),
            InlineKeyboardButton("Next return day ➡️", callback_data="date_next_ret")])
    if context.user_data.get("flight_type_choice") == "Round trip" and is_return_flight:
        keyboard.append([
        InlineKeyboardButton("🔁 Change departing flight", callback_data="change_departure_flight")])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    if is_date_change:
        if update.callback_query:
            target = update.callback_query.message
            await target.reply_text(message.strip(), parse_mode='HTML', reply_markup=reply_markup)
        else:
            target = update.message
            await target.reply_text(message.strip(), parse_mode='HTML', reply_markup=reply_markup)
    else:
        if update.callback_query:
            target = update.callback_query.message
            await target.edit_text(message.strip(), parse_mode='HTML', reply_markup=reply_markup)
        else:
            target = update.message
            await target.reply_text(message.strip(), parse_mode='HTML', reply_markup=reply_markup)
    
    context.user_data["flights"] = flights
    context.user_data["page"] = page

async def change_departure_flight(update: Update, context: ContextTypes.DEFAULT_TYPE, is_return_flight: bool = False):
    ''' For round trip flights, changing the departure date '''

    query = update.callback_query
    await query.answer()
    flight_tracker = FlightTracker(context)
    flight_tracker.come_back_to_dep_flight(context)
    flights = flight_tracker.fetch_flight_data(context)
    await display_flight_results(flights, update, context)


async def paginate_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ''' Paginates the results '''

    query = update.callback_query
    await query.answer()
    data = query.data
    flights = context.user_data.get("flights", [])
    current_page = context.user_data.get("page", 0)

    if query.data.startswith("next_"):
        new_page = int(query.data.split("_")[1])
        flights = context.user_data.get("flights", [])
        await display_flight_results(flights, update, context, page=new_page)

    if data.startswith("page_"):
        page = int(data.split("_")[1])
        flights = context.user_data.get("flights", [])
        await display_flight_results(flights, update, context, page=page)
    
    if data.startswith("date_previous_dep") or data.startswith("date_next_dep"):
        await change_flight_date(context, update, data, is_return_flight=False)
    elif data.startswith("date_previous_ret") or data.startswith("date_next_ret"):
        await change_flight_date(context, update, data, is_return_flight=True)
    
    if data.startswith("flight_"):
        flight_tracker = FlightTracker(context)
        flight_tracker.fetch_return_flight_data(context)

async def change_flight_date(context: ContextTypes.DEFAULT_TYPE, update: Update, direction: str, is_return_flight: bool):
    ''' Handles date change to previous / next day for departure or return flight '''

    flight_type = context.user_data.get("flight_type_choice")
    if flight_type == "One way":
        current_date = context.user_data.get("date_choice")
    elif flight_type == "Round trip":
        if is_return_flight:
            current_date = context.user_data.get("return_date_choice")
        else:
            current_date = context.user_data.get("date_choice")

    # Getting the desired date from the DateParser
    date_parser = DateParser(current_date)
    if direction.startswith("date_previous"):
        new_date = date_parser.previous_day()
        logger.info(f"New departure date (previous) has been parsed as: {new_date}")
    elif direction.startswith("date_next"):
        new_date = date_parser.next_day()
        logger.info(f"New departure date (next) has been parsed as: {new_date}")

    # Updating the correct date in context
    if flight_type == "One way":
        context.user_data["date_choice"] = new_date
        flight_tracker = FlightTracker(context)
        flight_tracker.date_change(context, "Departure", is_return_flight = False)
        flights = flight_tracker.fetch_flight_data(context)
        if flights is None:
            flights = []
        await display_flight_results(flights, update, context, page=0, show_all=False, is_return_flight=False, is_date_change=True)
    elif flight_type == "Round trip":
        if not is_return_flight:
            context.user_data["date_choice"] = new_date
            flight_tracker = FlightTracker(context)
            flight_tracker.date_change(context, "Departure", is_return_flight = False)
            flights = flight_tracker.fetch_flight_data(context)
            if flights is None:
                flights = []
            await display_flight_results(flights, update, context, page=0, show_all=False, is_return_flight=False, is_date_change=True)
        elif is_return_flight:
            context.user_data["return_date_choice"] = new_date
            flight_tracker = FlightTracker(context)
            flight_tracker.date_change(context, "Return", is_return_flight = True)
            flights = flight_tracker.fetch_flight_data(context)
            if flights is None:
                flights = []
            await display_flight_results(flights, update, context, page=0, show_all=False, is_return_flight=True, is_date_change=True)

async def handle_return_flight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ''' For round trip flights, gets data for the return trip '''

    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data

    # Selecting the correct index of the flight that user chose
    try:
        parts = data.split("_")
        selected_index = int(parts[3])
        context.user_data["selected_departure_flight_index"] = selected_index
    except (IndexError, ValueError):
        await query.edit_message_text("Invalid flight selection.")
        logger.info("The flight index could not be identifed.")
        return
    
    flights = context.user_data.get("flights", [])
    logger.info(f"User {user.first_name} selected departure flight to view return options")
    
    # Clicking on the selected departure flight to see the return flight data
    flight_tracker = FlightTracker(context)
    flight_tracker.confirm_dep_flight_for_round_trip(selected_index, context)
    return_flights = flight_tracker.fetch_flight_data(context)
    context.user_data["return_flights"] = return_flights
    await display_flight_results(return_flights, update, context, is_return_flight=True)


async def handle_flight_bookmark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ''' Handles adding a new flight bookmark into the database '''
    
    # Preventing repeated clicks on the same button
    if context.user_data.get("bookmarking_in_progress"):
        await update.callback_query.answer("⏳ Processing previous request...")
        return
    
    context.user_data["bookmarking_in_progress"] = True
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    data = query.data
    flight_type = context.user_data.get("flight_type_choice")
    flights = context.user_data.get("flights")
    return_flights = context.user_data.get("return_flights")

    if flight_type == "One way":
        # Extracting index and flight_id from callback data
        parts = data.split("_")
        index = int(parts[1])
        flight_id = parts[2]
        flight = flights[index]

        # Inserting data into database
        await db_manager.insert_user(user)
        await db_manager.insert_bookmark(user.id, flight_type, flight)
        
        # Storing the flight_id
        bookmarked = context.user_data.get("bookmarked_flights", set())
        bookmarked.add(flight_id)
        context.user_data["bookmarked_flights"] = bookmarked
        
    elif flight_type == "Round trip":
        # Extracting index and flight_id from callback data
        parts = data.split("_")
        index = int(parts[3])
        flight_id = parts[4]
        departure_index = context.user_data.get("selected_departure_flight_index")
        flight = flights[departure_index]
        return_flight = return_flights[index]

        # Inserting data into database
        await db_manager.insert_user(user)
        await db_manager.insert_bookmark(user.id, flight_type, flight, return_flight)
        
        # Storing the flight_id
        bookmarked = context.user_data.get("bookmarked_flights", set())
        bookmarked.add(flight_id)
        context.user_data["bookmarked_flights"] = bookmarked
    
    logger.info(f"User {user.first_name} added a flight to the database.")
    old_keyboard = query.message.reply_markup.inline_keyboard
    new_keyboard = []

    # Displaying bookmarked flights with "bookmarked" button
    for row in old_keyboard:
        new_row = []
        for button in row:
            if button.callback_data == data:
                new_row.append(InlineKeyboardButton("✅ Bookmarked", callback_data="noop"))
            else:
                new_row.append(button)
        new_keyboard.append(new_row)

    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise e
    context.user_data["bookmarking_in_progress"] = False

async def display_bookmarks(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    ''' Displays bookmarked flights to the user '''

    user_id = update.effective_user.id
    user = update.effective_user
    query = update.callback_query
    logger.info(f"User {user.first_name} requested bookmarks.")
    message = update.message
    bookmarks_per_page = 5
    bookmarks = await db_manager.get_user_bookmarks(user_id)

    start = page * bookmarks_per_page
    end = start + bookmarks_per_page
    current_page_bookmarks = bookmarks[start:end]

    if not bookmarks:
        await message.reply_text("📭 You have no bookmarks yet.")
        return
    
    text = f"You have {len(bookmarks)} total bookmarks.\n\n"
    keyboard = []
    for idx, row in enumerate(current_page_bookmarks, start=start + 1):
        if row['flight_type'] == "One way":
            text += (
                f"📌 <b>Bookmark {idx}</b>\n"
                f"🛫 <b>{row['route']}</b>\n"
                f"✈️ Airline: {row['airline']}\n"
                f"🕘 {row['departure_date']} {row['departure_time']} → {row['arrival_date']} {row['arrival_time']}\n"
                f"🔁 Stops: {row['departure_stops']}\n"
                f"⌛ Duration: {row['departure_duration']}\n"
                f"💰 {row['price']} {row['currency']}\n\n"
            )
        elif row['flight_type'] == "Round trip":
            text += (
                f"📌 <b>Bookmark {idx}</b>\n"
                f"🛫 <b>{row['route']}</b>\n"
                f"✈️ Airline: {row['airline']}\n"
                f"<b>Departing flight:</b>\n"
                f"🕘 Depart: {row['departure_date']} {row['departure_time']} → {row['arrival_date']} {row['arrival_time']}\n"
                f"🔁 Stops: {row['departure_stops']}\n"
                f"⌛ Duration: {row['departure_duration']}\n"
                f"<b>Returning flight:</b>\n"
                f"🔄 Return: {row['return_flight_departure_date']} {row['return_flight_departure_time']} → {row['return_flight_arrival_date']} {row['return_flight_arrival_time']}\n"
                f"🔁 Stops: {row['return_stops']}\n"
                f"⌛ Duration: {row['return_duration']}\n"
                f"💰 {row['price']} {row['currency']}\n\n"
            )
        keyboard.append([InlineKeyboardButton(f"🗑 Delete Bookmark {idx}", callback_data=f"delete_bookmark_{row['id']}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous bookmarks", callback_data=f"bookmarks_page_{page - 1}"))
    if end < len(bookmarks):
        nav_buttons.append(InlineKeyboardButton("Next bookmarks ➡️", callback_data=f"bookmarks_page_{page + 1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    if query:
        await query.answer()
        await query.edit_message_text(text=text.strip(), parse_mode="HTML", reply_markup=reply_markup)
    else:
        await message.reply_text(text.strip(), parse_mode="HTML", reply_markup=reply_markup)

async def delete_bookmark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ''' Deletes selected bookmark from the database '''

    query = update.callback_query
    await query.answer()
    user = query.from_user

    bookmark_id = int(query.data.split("_")[-1])
    user_id = query.from_user.id

    bookmarks = await db_manager.get_user_bookmarks(user_id, limit=100)
    if not any(b['id'] == bookmark_id for b in bookmarks):
        await display_bookmarks(update, context, page=0)
        return

    await db_manager.delete_bookmark(bookmark_id)
    logger.info(f"User {user.first_name} successfully deleted bookmark {bookmark_id}")
    await query.message.reply_text(f"✅ Bookmark deleted.")

    # Showing "DELETED" on buttons after deleting a bookmark
    old_keyboard = query.message.reply_markup.inline_keyboard
    new_keyboard = []
    for row in old_keyboard:
        new_row = []
        for button in row:
            if button.callback_data and str(bookmark_id) in button.callback_data:
                # Replace deleted bookmark button
                new_row.append(InlineKeyboardButton("✅ Deleted", callback_data="noop"))
            else:
                # Copy unchanged buttons
                new_row.append(button)
        new_keyboard.append(new_row)
    new_markup = InlineKeyboardMarkup(new_keyboard)
    try:
        await query.edit_message_reply_markup(reply_markup=new_markup)
    except Exception as e:
        logger.warning(f"Failed to update buttons after deletion: {e}")

    
async def bookmarks_pagination_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("bookmarks_page_"):
        page = int(data.split("_")[-1])
        await display_bookmarks(update, context, page=page)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ''' Logs the error and cleans up browser if needed '''

    error = context.error
    user = update.effective_user
    chat_id = update.effective_chat.id
    should_restart_conversation = False
    quit_driver = False

    # Prevent sending repeated error messages
    now = time.time()
    last_error_time = context.user_data.get("last_error_time", 0)
    if now - last_error_time < 5:
        logger.warning(f"Suppressing repeated error message for user {user.id if user else 'Unknown'}")
        return None
    context.user_data["last_error_time"] = now

    logger.error(f"Exception while handling update {update.update_id if update else 'Unknown'}: {error}",exc_info=error)

#    if chat_id:
#        try:
#            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Something went wrong. Please try again.")
#        except TelegramError:
#            pass

    if isinstance(error, NetworkError):
        logger.warning(f"Network error for {user.name}: {error}")
        error_message = "🌐 Network connection issue. Please try again in a moment."
        
    elif isinstance(error, TimedOut):
        logger.warning(f"Request timed out for {user.name}: {error}")
        error_message = "⏱️ Request timed out. Please try again."
        
    elif isinstance(error, BadRequest):
        logger.warning(f"Bad request for {user.name}: {error}")
        if "message is not modified" in str(error).lower():
            return
        error_message = "❌ Invalid request. Please start over with /start"
        should_restart_conversation = True
        
    elif isinstance(error, Forbidden):
        logger.warning(f"Bot was blocked by {user.name}: {error}")
        return
        
    elif "selenium" in str(error).lower() or "webdriver" in str(error).lower():
        logger.error(f"Selenium/WebDriver error for {user.name}: {error}")
        error_message = "🤖 Browser automation issue. Please try again with /start"
        should_restart_conversation = True
        quit_driver = True
        
    elif "database" in str(error).lower() or "connection" in str(error).lower():
        logger.error(f"Database error for {user.name}: {error}")
        error_message = "💾 Database connection issue. Please try again later."
        
    else:
        logger.error(f"Unknown error for {user.name}: {error}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        error_message = "⚠️ An unexpected error occurred. Please try again with /start"
        should_restart_conversation = True
        quit_driver = True
    
    try:
        await context.bot.send_message(chat_id=chat_id, text=error_message)
    except TelegramError as e:
        logger.error(f"Failed to send error message to {user.name}: {e}")

    if hasattr(context, 'driver'):
        try:
            context.driver.quit()
        except Exception:
            pass
    
    if should_restart_conversation:
        return ConversationHandler.END

    return None


async def cleanup_idle_drivers(context):
    ''' Cleans up idle Chrome drivers after inactivity '''

    application = context.application
    inactivity_timeout = 15 * 60
    while True:
        await asyncio.sleep(905)

        for user_id, user_data in list(application.user_data.items()):
            driver = user_data.get("driver")
            last_active = user_data.get("last_active")
            if driver and last_active:
                if time.time() - last_active > inactivity_timeout:
                    try:
                        driver.quit()
                        print(f"Closed idle driver for user {user_id}")
                    except Exception as e:
                        print(f"Error closing driver: {e}")
                    finally:
                        del user_data["driver"]
                        del user_data["last_active"]


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


def main() -> None:

    load_dotenv()
    bot_token = os.getenv('bot_token')
    application = Application.builder().token(bot_token).post_init(set_bot_commands).build()
    application.job_queue.run_repeating(cleanup_idle_drivers, interval=905, first=905)

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FLIGHT_TYPE: [MessageHandler(filters.Text(["One way", "Round trip", "Multi-city"]), flight_type)],
            ORIGIN_PRELIMINARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_origin_main)],
            ORIGIN_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_origin_specific)],
            ORIGIN_SPECIFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_departure_main)],
            DESTINATION_PRELIMINARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_destination_main)],
            DESTINATION_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_destination_specific)],
            DESTINATION_SPECIFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_date)],
            FLIGHT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmed)],
            RETURN_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_return_date)]
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    application.add_handler(conversation_handler)
    application.add_handler(CallbackQueryHandler(paginate_results, pattern=r"^(page_\d+|date_(previous|next)_(dep|ret))$"))
    application.add_handler(CallbackQueryHandler(handle_flight_bookmark, pattern=r"^flight_\d+_[a-f0-9]{8}$"))
    application.add_handler(CallbackQueryHandler(handle_flight_bookmark, pattern=r"^return_flight_ret_\d+_[a-f0-9]{8}$"))
    application.add_handler(CallbackQueryHandler(handle_return_flight, pattern=r"^return_flight_dep_\d+_[a-f0-9]{8}$"))
    application.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
    application.add_handler(CallbackQueryHandler(change_departure_flight, pattern="^change_departure_flight$"))
    application.add_handler(CallbackQueryHandler(bookmarks_pagination_handler, pattern=r"^bookmarks_page_\d+$"))
    application.add_handler(CallbackQueryHandler(delete_bookmark, pattern=r"^delete_bookmark_\d+$"))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("bookmarks", display_bookmarks))
    application.add_handler(CommandHandler("disclaimer", disclaimer))

    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
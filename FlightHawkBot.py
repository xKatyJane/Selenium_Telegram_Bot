import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup, KeyboardButton
import FlightTracker

flight_type_choice = None
origin_main_choice = None
origin_specific_choice = None
destination_choice = None
date_choice = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

FLIGHT_TYPE, ORIGIN_PRELIMINARY, ORIGIN_MAIN, ORIGIN_SPECIFIC, DESTINATION_PRELIMINARY, DESTINATION_MAIN, DESTINATION_SPECIFIC, DATE = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Displays the welcome message and asks for flight type '''
    user = update.effective_user
    reply_keyboard = [["One way", "Return", "Multi-city"]]

    await update.message.reply_text(
        '✈️ <b>Welcome to the Flight Hawk Bot! ✈️\n'
        'I can help you to find cheap flights and track fare changes.\n</b>'
        'What type of flight are you looking for?\n',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return FLIGHT_TYPE

async def flight_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves flight type choice and asks for departure city '''
    global flight_type_choice

    user = update.message.from_user
    flight_type_choice = update.message.text
    logger.info(f"User {user.first_name} chose: {flight_type_choice}")
    context.user_data["flight_type_choice"] = flight_type_choice
    await update.message.reply_text(f"{flight_type_choice} it is! 🛫 What is your departure city?")
    return ORIGIN_PRELIMINARY

async def choose_origin_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the departure city '''

    user = update.message.from_user
    origin_preliminary_choice = update.message.text
    logger.info(f"User {user.first_name} entered the departure city as: {origin_preliminary_choice}")
    context.user_data["origin_preliminary_choice"] = origin_preliminary_choice
    flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
    flight_tracker = FlightTracker.FlightTracker(context)
    flight_tracker.get_google_flights()
    flight_tracker.flight_type(context)
    main_origin_options = flight_tracker.main_choice(context, 1, origin_preliminary_choice)

    if main_origin_options:
#        reply_keyboard = [[KeyboardButton(text=option)] for option in main_origin_options]
        reply_keyboard = [[option] for option in main_origin_options]
        await update.message.reply_text("📌 Choose a departure option from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
    else:
        await update.message.reply_text("No options found, please try again.")
    return ORIGIN_MAIN

async def choose_origin_specific(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    origin_main_choice = update.message.text
    logger.info(f"User {user.first_name} chose a main origin option: {origin_main_choice}")
    context.user_data["origin_main_choice"] = origin_main_choice
    flight_tracker = FlightTracker.FlightTracker(context)
    flight_tracker.specific_choice(context, origin_main_choice)

    origin_specific_options = flight_tracker.specific_choice(context, origin_main_choice)
    if len(origin_specific_options)<=2:
        context.user_data["origin_specific_choice"] = origin_main_choice
        logger.info(f"User {user.first_name} selected an origin main with only one option: {origin_main_choice}, so not asking for specific origin.")
        await update.message.reply_text(f"Great! What is your destination city? 🛬")
        return DESTINATION_PRELIMINARY
    elif len(origin_specific_options)>2:
        reply_keyboard = [[option] for option in origin_specific_options]
        await update.message.reply_text("You can choose an airport or the main for all airports. ✈️",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        print(len(origin_specific_options))
        return ORIGIN_SPECIFIC
    else:
        await update.message.reply_text("No options found, please try again.")
        return ORIGIN_SPECIFIC

async def choose_departure_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    origin_specific_choice = update.message.text
    logger.info(f"User {user.first_name} chose origin specific as: {origin_specific_choice}")
    context.user_data["origin_specific_choice"] = origin_specific_choice
    await update.message.reply_text(f"Great! What is your destination city? 🛬")
    return DESTINATION_PRELIMINARY

async def choose_destination_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    destination_preliminary_choice = update.message.text
    logger.info(f"User {user.first_name} entered the destination city as: {destination_preliminary_choice}")
    context.user_data["destination_preliminary_choice"] = destination_preliminary_choice
    flight_tracker = FlightTracker.FlightTracker(context)
    origin_specific_choice = context.user_data.get("origin_specific_choice")
    flight_tracker.confirm_decision(context, origin_specific_choice)
#    flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
    main_destination_options = flight_tracker.main_choice(context, 2, destination_preliminary_choice)
    print(main_destination_options)

    if main_destination_options:
        reply_keyboard = [[option] for option in main_destination_options]
        await update.message.reply_text("📌 Choose a destination option from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
    else:
        await update.message.reply_text("No options found, please try again.")
    return DESTINATION_MAIN

async def choose_destination_specific(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    destination_main_choice = update.message.text
    logger.info(f"User {user.first_name} chose a main destination option: {destination_main_choice}")
    context.user_data["destination_main_choice"] = destination_main_choice
    flight_tracker = FlightTracker.FlightTracker(context)

    destination_specific_options = flight_tracker.specific_choice(context, destination_main_choice)
    if len(destination_specific_options)<=2:
        context.user_data["destination_specific_options"] = destination_main_choice
        logger.info(f"User {user.first_name} selected a destination main with only one option: {destination_main_choice}, so not asking for specific destination.")
        await update.message.reply_text(f"Noted! What is the departure date? For example DD-MM-YYYY.")
#        return DESTINATION_PRELIMINARY

    elif len(destination_specific_options)>2:
        reply_keyboard = [[option] for option in destination_specific_options]
        await update.message.reply_text("You can choose an airport or the city to search for all airports. ✈️",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        print(len(destination_specific_options))
    else:
        await update.message.reply_text("No options found, please try again.")
    return DESTINATION_SPECIFIC

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    destination_specific_choice = update.message.text
    logger.info(f"User {user.first_name} chose destination specific as: {destination_specific_choice}")
    context.user_data["destination_specific_choice"] = destination_specific_choice
    flight_tracker = FlightTracker.FlightTracker(context)
    destination_specific_choice = context.user_data.get("destination_specific_choice")
    flight_tracker.confirm_decision(context, destination_specific_choice)
    await update.message.reply_text(f"Noted! What is the departure date? For example DD-MM-YYYY.")
    return DATE

async def confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass



def main() -> None:
    BOT_TOKEN = '7843297201:AAF5-rRRaBsUYHMamsIEug-Kd-YSynlHTSw'
    BOT_NAME = '@Flight_Hawk_Bot'

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FLIGHT_TYPE: [MessageHandler(filters.Text(["One way", "Return", "Multi-city"]), flight_type)],
            ORIGIN_PRELIMINARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_origin_main)],
            ORIGIN_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_origin_specific)],
            ORIGIN_SPECIFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_departure_main)],
            DESTINATION_PRELIMINARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_destination_main)],
            DESTINATION_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_destination_specific)],
            DESTINATION_SPECIFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_date)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmed)],
        },
        fallbacks=[],
    )
    application = Application.builder().token("7843297201:AAF5-rRRaBsUYHMamsIEug-Kd-YSynlHTSw").build()
    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler('start', start))

    application.run_polling()

if __name__ == '__main__':
    main()
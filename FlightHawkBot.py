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
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

FLIGHT_TYPE, ORIGIN_MAIN, ORIGIN_SPECIFIC, DESTINATION, DATE = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    reply_keyboard = [["One way", "Return", "Multi-city"]]

    await update.message.reply_text(
        '<b>Welcome to the Flight Hawk Bot!\n'
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
    #FlightTracker().origin_main(context)
#    flight_tracker = FlightTracker.FlightTracker(context)
    await update.message.reply_text(f"You selected: {flight_type_choice}. What is your departure city?")
    return ORIGIN_MAIN

async def choose_origin_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ''' Saves the departure city '''

    user = update.message.from_user
    origin_main_choice = update.message.text
    logger.info(f"User {user.first_name} chose: {origin_main_choice}")
    context.user_data["origin_main_choice"] = origin_main_choice
    flight_type_choice = context.user_data.get("flight_type_choice", "Default Value")
    flight_tracker = FlightTracker.FlightTracker(context)
#    flight_tracker = FlightTracker.FlightTracker(context)
#    main_origin_options = flight_tracker.origin_main()
    flight_tracker.get_google_flights()
    main_origin_options = flight_tracker.origin_main(context)

    if main_origin_options:
#        reply_keyboard = [[KeyboardButton(text=option)] for option in main_origin_options]
        reply_keyboard = [[option] for option in main_origin_options]
        await update.message.reply_text("Please choose the city from the list.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
    else:
        await update.message.reply_text("No options found, please try again.")
    return ORIGIN_SPECIFIC

async def choose_origin_specific(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    origin_specific_choice = update.message.text
    logger.info(f"User {user.first_name} chose: {origin_specific_choice}")
    context.user_data["origin_specific_choice"] = origin_specific_choice
    flight_tracker = FlightTracker.FlightTracker(context)
    flight_tracker.origin_specific(context)

    origin_specific_options = flight_tracker.origin_specific(context)
    if len(origin_specific_options)<=2:
        pass
    elif len(origin_specific_options)>2:
        reply_keyboard = [[option] for option in origin_specific_options]
        await update.message.reply_text("You can choose an airport or the city to search for all airports.",
                                        reply_markup=ReplyKeyboardMarkup(
                                            reply_keyboard,
                                            one_time_keyboard=True,
                                            resize_keyboard=True))
        print(len(origin_specific_options))
    else:
        await update.message.reply_text("No options found, please try again.")
    return DESTINATION

async def choose_departure_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


def main() -> None:
    BOT_TOKEN = '7843297201:AAF5-rRRaBsUYHMamsIEug-Kd-YSynlHTSw'
    BOT_NAME = '@Flight_Hawk_Bot'

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FLIGHT_TYPE: [MessageHandler(filters.Text(["One way", "Return", "Multi-city"]), flight_type)],
            ORIGIN_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_origin_main)],
            ORIGIN_SPECIFIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_origin_specific)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_departure_main)],
        },
        fallbacks=[],
    )
    application = Application.builder().token("7843297201:AAF5-rRRaBsUYHMamsIEug-Kd-YSynlHTSw").build()
    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler('start', start))

    application.run_polling()

if __name__ == '__main__':
    main()
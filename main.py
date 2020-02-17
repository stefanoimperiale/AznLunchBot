import os
import sys

from telegram.ext import CommandHandler
from telegram.ext import InlineQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater, ConversationHandler

from bot_commands import start, caps, start_collect, unknown, inline_query, stop_collect, get_menu, button_menu, \
    get_places_name
from util import error, config, MENU, logger
from flask import Flask


# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    def run(upd):
        upd.start_polling()
elif mode == "prod":
    # GET endpoint for keeping alive application
    app = Flask(__name__)
    port = int(os.environ.get("PORT", "8443"))
    app.run(threaded=True, port=port)

    @app.route('/')
    def hello_world():
        return 'Hello, World!'

    def run(upd):
        heroku_app_name = os.environ.get("HEROKU_APP_NAME")
        upd.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=TOKEN)
        upd.bot.set_webhook(f"https://{heroku_app_name}.herokuapp.com/{TOKEN}")
else:
    logger.error("No MODE specified!")
    sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('get_menu', get_menu)],
        states={
            MENU: [MessageHandler(Filters.regex(
                '^({})$'.format('|'.join(get_places_name()))),
                button_menu)],
        },
        fallbacks=[CommandHandler('get_menu', get_menu)],
    )
    dispatcher.add_handler(conv_handler)

    caps_handler = CommandHandler('caps', caps)
    dispatcher.add_handler(caps_handler)

    inline_caps_handler = InlineQueryHandler(inline_query)
    dispatcher.add_handler(inline_caps_handler)

    collect_handler = CommandHandler('start_collect', start_collect)
    dispatcher.add_handler(collect_handler)

    stop_handler = CommandHandler('stop_collect', stop_collect)
    dispatcher.add_handler(stop_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # unknown message handler, must be the last
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    run(updater)

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

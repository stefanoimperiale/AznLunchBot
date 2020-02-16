from telegram.ext import CommandHandler
from telegram.ext import InlineQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater, ConversationHandler

from bot_commands import start, caps, start_collect, unknown, inline_query, stop_collect, get_menu, button_menu, \
    get_places_name
from util import error, config, MENU

TOKEN = config.read('token')
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


# Start the Bot
updater.start_polling()

# Block until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()

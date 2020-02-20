import os
import sys
from datetime import timedelta

from telegram.ext import CommandHandler, Dispatcher
from telegram.ext import InlineQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater, ConversationHandler

from bot_commands import start, caps, start_collect, unknown, inline_query, stop_collect, get_menu, button_menu, \
    get_places_name, save_jobs_job
from util import error, MENU, logger, HelloWorld, config, load_jobs, save_jobs


def set_handlers(dispatcher: Dispatcher):
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


# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    def run(upd):
        upd.start_polling()

elif mode == "prod":
    def run(upd):
        port = int(os.environ.get("PORT", "8443"))
        heroku_app_name = os.environ.get("HEROKU_APP_NAME")
        upd.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=TOKEN)
        upd.bot.set_webhook(f"https://{heroku_app_name}.herokuapp.com/{TOKEN}")

        # add GET dummy endpoint for cron-job
        upd.httpd.http_server.request_callback.add_handlers(host_pattern=r".*", host_handlers=[(r"/get", HelloWorld)])

else:
    logger.error("No MODE specified!")
    sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Periodically save jobs
    job_queue = updater.job_queue
    job_queue.run_repeating(save_jobs_job, timedelta(minutes=config.read('job_time')['save_interval']))

    try:
        load_jobs(job_queue)
    except FileNotFoundError:
        # First run
        pass

    set_handlers(dispatcher)
    run(updater)

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    # Run again after bot has been properly shut down
    save_jobs(job_queue)

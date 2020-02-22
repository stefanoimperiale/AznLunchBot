from datetime import time
from uuid import uuid4

import pytz
import telegram.ext
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode, ReplyKeyboardMarkup
from telegram.utils.helpers import escape_markdown

from retriever.menu_retriever import menu_retriever_by_job, retrieve_menu
from util.utility import config, get_places_name, MENU, build_menu, save_jobs


def start(update, context):
    """ COMMAND 'start' """
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm the menu retriever")


def caps(update, context):
    text_caps = ''.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def inline_query(update, context):
    """Handle the inline query."""
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=uuid4(),
            title="Caps",
            input_message_content=InputTextMessageContent(
                query.upper())),
        InlineQueryResultArticle(
            id=uuid4(),
            title="Bold",
            input_message_content=InputTextMessageContent(
                "*{}*".format(escape_markdown(query)),
                parse_mode=ParseMode.MARKDOWN)),
        InlineQueryResultArticle(
            id=uuid4(),
            title="Italic",
            input_message_content=InputTextMessageContent(
                "_{}_".format(escape_markdown(query)),
                parse_mode=ParseMode.MARKDOWN))]

    update.inline_query.answer(results)


def start_collect(update: telegram.Update, context: telegram.ext.CallbackContext):
    """ COMMAND 'start_collect' """
    jobs = context.job_queue.get_jobs_by_name('menu_ret')
    if len(jobs) > 0:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Job already started! Stop it by /stop_collect command')

    else:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Menu Retriever start!')

        t_zone = pytz.timezone(config.read('timezone'))
        job_time = config.read('job_time')
        t = time(job_time['hours'], job_time['minutes'], job_time['seconds'], tzinfo=t_zone)

        """ Running on Mon, Tue, Wed, Thu, Fri = tuple(range(5)) """
        context.job_queue.run_daily(menu_retriever_by_job, t,
                                    days=tuple(range(5)),
                                    context=update.message.chat_id,
                                    name='menu_ret')


def stop_collect(update: telegram.Update, context: telegram.ext.CallbackContext):
    """ COMMAND 'stop_collect' """
    jobs = context.job_queue.get_jobs_by_name('menu_ret')
    if len(jobs) > 0:
        jobs[0].schedule_removal()
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='The job has been stopped')
    else:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='No job started. Use /start_collect to start new one')


def get_menu(update: telegram.Update, context: telegram.ext.CallbackContext):
    """ COMMAND 'get_menu' """
    keyboard = get_places_name()
    if len(keyboard) == 0:
        context.bot.send_message(chat_id=update.message.chat_id, text='No lunch zones found! Configure new one')
    else:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Select a place and we\'ll try to retrieve the menu',
                                 reply_markup=ReplyKeyboardMarkup(build_menu(keyboard, 2), resize_keyboard=True,
                                                                  one_time_keyboard=True))
    return MENU


def button_menu(update, context):
    """ 'get_menu' RESPONSE HANDLER """
    reply_markup = telegram.ReplyKeyboardRemove()
    context.bot.send_message(chat_id=update.message.chat_id, text='Searching...', reply_markup=reply_markup)
    message = update.message.text
    place = next(iter(message.split()), '')
    place_info = config.read('lunchzone').get(place, None)
    if place_info is not None:
        retrieve_menu(context, update.message.chat_id, place_info['type'], place, place_info['address'])
    else:
        context.bot.send_message(update.message.chat_id, f'No configuration found for {message}')


def save_jobs_job(context):
    save_jobs(context.job_queue)


def unknown(update, context):
    """ UNKNOWN COMMAND"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

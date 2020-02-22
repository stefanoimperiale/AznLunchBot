import sys
from datetime import date
from typing import List

import requests
import telegram.ext
from bs4 import BeautifulSoup
from telegram import ParseMode

from facebook_scraper.facebook_scraper import get_posts
from retriever.mail_retriever import MailHandler
from util.utility import send_images_helper, config, list_in_chunks, html_to_png, send_file_helper, logger, MAIL_PASS


def retrieve_menu(context: telegram.ext.CallbackContext, chat_id: str, lunch_type: str, place_name: str,
                  address: str):
    context.bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)
    if lunch_type == 'facebook':
        handle_facebook(context, chat_id, place_name, address)
    elif lunch_type == 'web':
        handle_web(context, chat_id, place_name, address)
    elif lunch_type == 'mail':
        handle_mail(context, chat_id, place_name, address)


def handle_facebook(context: telegram.ext.CallbackContext, chat_id: str, place_name: str, link: str):
    caption = ''
    images = []

    posts = get_posts(link, pages=1)
    today = next((x for x in posts if x['time'].date() == (date.today())), None)
    if today is not None:
        caption = f"{place_name} - {date.today().strftime('%d %B %Y')} \n {today['text']}"
        images = today['image']

    send_images_helper(context, chat_id, images, caption, place_name)


def handle_web(context: telegram.ext.CallbackContext, chat_id: str, place_name: str, link: str):
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    html_images = get_htmls_from_specific_webpage(soup, place_name)
    photos = html_to_png(html_images)
    caption = f"{place_name} - {date.today().strftime('%d %B %Y')}"
    send_images_helper(context, chat_id, photos, caption, place_name)


def handle_mail(context, chat_id, place_name, address):
    mail_handler = MailHandler(MAIL_PASS)
    mail_ids = mail_handler.read_daily_mails(address)

    if len(mail_ids) == 0:
        context.bot.send_message(chat_id=chat_id, text=f'No menu today for: {place_name}')

    else:
        for ids in mail_ids:
            mail_info = mail_handler.get_mail_info(ids)
            attachments = mail_handler.get_mail_attachments(ids)
            text = f'From: {mail_info["from"]}\nSubject: {mail_info["subject"]}\nContent: {mail_info["content"]}'

            if len(attachments) > 0:
                for att in attachments:
                    filename = att['filename']
                    file_content = att['content']
                    send_file_helper(context, chat_id, filename, file_content, text)

            else:
                # no attachments
                context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def menu_retriever_by_job(context: telegram.ext.CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text='Start retrieving menus...')
    places = config.read('lunchzone')
    for place_name, value in places.items():
        type_lunch = value.get('type', '')
        retrieve_menu(context, context.job.context, type_lunch, place_name, value.get('address'))


def get_htmls_from_specific_webpage(soup, place_name: str) -> List[str]:
    results = []

    if place_name == 'AMICI_MIEI':
        excluded = ['pizze', 'sfizi', 'insalate', 'bevande', 'dolci']
        day = soup.find('section', class_='l-section wpb_row height_large').find('h3')
        sections = soup.find_all('section', class_='l-section wpb_row height_medium color_custom')
        sections = list(x for x in sections if x.get('id') not in excluded)
        sections.insert(0, day)

        # divide in chunk, useful for split large html in more image
        sections = list_in_chunks(sections, 5)
        for inner_sections in sections:
            results.append(''.join(map(lambda c: c.prettify(), inner_sections)))

    return results


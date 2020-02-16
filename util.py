import io
import logging
from typing import List

import filetype
import pdfcrowd
from pdf2image import convert_from_bytes
from telegram import InputMediaPhoto, ParseMode

from config_handler import ConfigReader

# logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# config utils
config = ConfigReader()

# STEPS for conversation handler
MENU = range(1)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_places_name() -> List[str]:
    """Return the list of places as concat of name and emoji"""
    places = config.read('lunchzone')
    places_list = []
    for placeName, value in places.items():
        places_list.append(f"{placeName} {value.get('emoji', '')}")
    return places_list


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """Helper for build menu or keyboard buttons"""
    menu = list_in_chunks(buttons, n_cols)
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def send_images_helper(context, chat_id, images, caption, place_name):
    """
    Helper for send images.
    If images list has one only element it will be send as single photo.
    If images list size is more than 1, then they will be send as album.
    Otherwise no menu are present
    """
    if len(images) > 1:
        media_photos = [InputMediaPhoto(image) for image in images]
        media_photos[0].caption = caption
        context.bot.send_media_group(chat_id=chat_id, media=media_photos, parse_mode=ParseMode.MARKDOWN)

    elif len(images) == 1:
        context.bot.send_photo(chat_id=chat_id, photo=images[0], caption=caption, parse_mode=ParseMode.MARKDOWN)

    else:
        context.bot.send_message(chat_id=chat_id, text=f'No menu today for: {place_name}')


def list_in_chunks(orig_list, chunk_dim):
    """Divide a list in a list of lists of at least 'chunk_dim' size """
    return [orig_list[i:i + chunk_dim] for i in range(0, len(orig_list), chunk_dim)]


def html_to_png(html_list: List[str]):
    # create the API client instance
    settings = config.read('pdfcrowd')
    client = pdfcrowd.HtmlToImageClient(settings['user'], settings['api_key'])

    # configure the conversion
    client.setOutputFormat('png')

    photos = []
    for image in html_list:
        # run the conversion and store the result into the "image" variable
        image = client.convertString(image)
        photos.append(io.BytesIO(image))
    return photos


def send_file_helper(context, chat_id, filename, file_content, caption):
    """
    Helper for handle generic files.
    If the file is a pdf, it will be converted and send as image/s.
    If the file is already an image it will not be processed.
    If the file is any other type, it will be send as document.
    """

    mime = filetype.guess_mime(file_content)
    if mime == 'application/pdf':
        pages = convert_from_bytes(file_content, 500)
        images = []
        for page in pages:
            file = io.BytesIO()
            page.save(file, 'png')
            file.name = filename
            file.seek(0)
            images.append(file)
        send_images_helper(context, chat_id, images, caption, '')

    elif filetype.image(file_content) is not None:
        send_images_helper(context, chat_id, [io.BytesIO(file_content)], caption, '')

    else:
        content = io.BytesIO(file_content)
        context.bot.send_document(chat_id=chat_id, document=content, filename=filename,
                                  parse_mode=ParseMode.MARKDOWN, caption=caption)
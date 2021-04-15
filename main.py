import logging
import os, random

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
GET_PROVERB_TEXT = 'Хочу пословицу!'
IMG_DIR = 'img'
random.seed(228)


def get_random_image(path: str) -> str:
    imgs = [file for file in os.listdir(path) if file.endswith('.png') or file.endswith('.jpg')]
    if len(imgs) == 0:
        raise RuntimeError('No .png or .jpg files in directory "' + IMG_DIR + '"')
    return path + '/' + random.choice(imgs)


def get_user_description(update: Update) -> str:
    return '(id: "{0}", full_name: "{1}", username: "{2}")'.format(str(update.effective_user.id),
                                                                   update.effective_user.full_name,
                                                                   str(update.effective_user.username))


def start(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        'Привет, ' + user.full_name + '\! Этот бот каждый день будет по твоему запросу присылать тебе '
        'по твоему запросу различные наркопословицы\. Чтобы получить первую, нажми кнопку\. '
        '*Мы не пропагандируем употребление наркотиков\!*',
        reply_markup=ReplyKeyboardMarkup([[GET_PROVERB_TEXT]], one_time_keyboard=True),
    )
    logging.info('Got /start from user ' + get_user_description(update))


def help_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_markdown_v2('Этот бот каждый день может присылать вам наркопословицы из рубрики '
                              '"Голос улиц" канала @farfond\. *Мы не пропагандируем употребление наркотиков\!*')


def handle_message(update: Update, _: CallbackContext) -> None:
    if update.message.text == GET_PROVERB_TEXT:
        img_path = get_random_image(IMG_DIR)
        logging.info('Sending image ' + img_path + ' to ' + get_user_description(update))
        proverb_img = open(get_random_image(IMG_DIR), 'rb')
        update.message.reply_photo(proverb_img)


def main() -> None:
    token_file = open("token.txt", "r")
    token = token_file.readline().rstrip('\n')
    token_file.close()
    updater = Updater(token=token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
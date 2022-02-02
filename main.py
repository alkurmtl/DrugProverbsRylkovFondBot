import datetime
import logging
import os, random
import pytz

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, PicklePersistence

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
GET_PROVERB_TEXT = 'Хочу пословицу!'
IMG_DIR = 'img'
ADMIN_ID = 33739616 # @wrg0ababd
random.seed(int(datetime.datetime.now().timestamp()))  # seed was 228 initially :)


def get_random_image(path: str) -> str:
    imgs = [file for file in os.listdir(path) if file.endswith('.png') or file.endswith('.jpg')]
    if len(imgs) == 0:
        raise RuntimeError('No .png or .jpg files in directory "' + IMG_DIR + '"')
    return path + '/' + random.choice(imgs)


def get_user_description(update: Update) -> str:
    return '(id: "{0}", full_name: "{1}", username: "{2}")'.format(str(update.effective_user.id),
                                                                   update.effective_user.full_name,
                                                                   str(update.effective_user.username))


def get_proverb_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[GET_PROVERB_TEXT]], one_time_keyboard=True, resize_keyboard=True)


def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_markdown_v2(
        'Нажми кнопку и узнай какая пословица или примета выпадет тебе сегодня, но помни, '
        'что *мы не пропагандируем употребление наркотиков\!*',
        reply_markup=get_proverb_keyboard(),
    )
    logging.info('Got /start from user ' + get_user_description(update))


def help_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_markdown_v2('Этот бот может каждый день присылать наркопословицы из рубрики '
                              '"Голос улиц" канала @farfond\. *Мы не пропагандируем употребление наркотиков\!*')


def send_everyone(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if 'ids' not in context.bot_data:
        return
    message_text = update.effective_message.text[15:]
    log_text = 'Sending message "' + message_text + '" to all users, ids:'
    for id in context.bot_data['ids']:
        log_text += ' '
        context.bot.send_message(
            id,
            message_text
        )
        log_text += str(id)
    logging.info(log_text)


def send_reminder(context: CallbackContext) -> None:
    job = context.job
    context.bot.send_message(
        int(str(job.context)),  # job.context == user id (object)
        'Привет, хочешь еще одну пословицу?',
        reply_markup=get_proverb_keyboard()
    )


def send_photo(update: Update, context: CallbackContext) -> None:
    img_path = get_random_image(IMG_DIR)
    logging.info('Sending image ' + img_path + ' to ' + get_user_description(update))
    proverb_img = open(get_random_image(IMG_DIR), 'rb')
    update.message.reply_photo(proverb_img)
    proverb_img.close()
    update.message.reply_text('После полуночи (по московскому времени) смогу прислать еще одну!')
    midnight = datetime.datetime.now(pytz.timezone('Europe/Moscow'))\
        .replace(hour=0, minute=0, second=0, microsecond=0)
    midnight += datetime.timedelta(days=1)
    context.job_queue.run_once(send_reminder, midnight,
                               context=update.effective_user.id, name=str(update.effective_user.id))


def handle_message(update: Update, context: CallbackContext) -> None:
    if 'ids' not in context.bot_data:
        context.bot_data['ids'] = set()
    context.bot_data['ids'].add(update.effective_user.id)
    logging.info('Got message with text "' + update.message.text + '" from ' + get_user_description(update))
    if update.message.text == GET_PROVERB_TEXT:
        if len(context.job_queue.get_jobs_by_name(str(update.effective_user.id))) > 0:
            update.message.reply_text('Полночь (по московскому времени) еще не настала!')
        else:
            send_photo(update, context)


def main() -> None:
    token_file = open("token.txt", "r")
    token = token_file.readline().rstrip('\n')
    token_file.close()
    persistence = PicklePersistence(filename='persistence')
    updater = Updater(token=token, persistence=persistence)
    updater.job_queue.scheduler.configure(misfire_grace_time=60)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("send_everyone", send_everyone))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

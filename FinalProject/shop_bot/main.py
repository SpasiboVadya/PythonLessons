from flask import Flask, request, abort
from telebot import TeleBot

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Update

from keyboards import START_KB
from models.model import Category

from config import TOKEN, PATH, WEBHOOK_URL

bot = TeleBot(token=TOKEN)

app = Flask(__name__)


@app.route(f'/{PATH}', methods=['POST'])
def webhook():
    """
    Function process webhook call
    """
    if request.headers.get('content-type') == 'application/json':

        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''

    else:
        abort(403)


@bot.message_handler(commands=['start'])
def start(message):
    # txt = Texts.objects(text_type='Greetings').get()
    txt = 'hello'

    kb = ReplyKeyboardMarkup()
    buttons = [KeyboardButton(button_name) for button_name in START_KB.values()]
    kb.add(*buttons)
    bot.send_message(message.chat.id, txt, reply_markup=kb)


@bot.message_handler(func=lambda message: message.text == START_KB['categories'])
def categories(message):
    cats = Category.objects(is_root=True)

    kb = InlineKeyboardMarkup()

    buttons = [InlineKeyboardButton(text=cat.title, callback_data=str(cat.id)) for cat in cats]

    kb.add(*buttons)
    bot.send_message(message.chat.id, 'Выберите категорию', reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def get_cat_or_products(call):
    """
    Приходит к нам id категории, получаем объект этой категории:
    1) Если объект не имеет предков - выводим продукты
    2) Если объект имеет предков - выводит этих предков

    :param call:
    :return:
    """
    kb = InlineKeyboardMarkup()
    title_text = ' | Категории:'
    category = Category.objects.get(id=call.data)
    buttons = []

    if category.subcategories:
        buttons = [InlineKeyboardButton(text=cat.title, callback_data=str(cat.id)) for cat in category.subcategories]

    else:
        title_text = ' | Товары:'
        buttons = [
            InlineKeyboardButton(text=product.title, callback_data=str(product.id)) for product in
            category.get_products()
        ]

    kb.add(*buttons)
    bot.edit_message_text(category.title + title_text,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          reply_markup=kb)
    # bot.send_message(call.message.chat.id, category.title, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'product')
def add_to_cart(call):
    product = call.data.split('_')[1]


if __name__ == '__main__':
    import time

    print('Started TELEGRAM BOT SHOP WEB SERVER')
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(
        url=WEBHOOK_URL,
        certificate=open('nginx-selfsigned.crt', 'r')
    )
    app.run(host='127.0.0.1', port=5000, debug=True)
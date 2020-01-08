#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import datetime
import os, sys
import json
import sqlite3
from sqlite3 import Error
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler
)
from oneliner_api import OneLiner_client, API_DATE_FORMAT

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

AUTH, START_DATE, DATE, PHOTO, LOCATION, INFO, PARSE = range(7)
TOKEN = os.getenv("TOKEN")
DB_FILE = os.getenv("DB_FILE")

def start(update, context):
    # first authenticate the user
    kb = KeyboardButton(text='Share my phone number', request_contact=True)
    if 'token' not in context.user_data:
        intro = 'Hi! My name is Professor Freud! I need to authenticate you first with One Liner app.'
        # update.message.reply_text(intro, )
        update.message.reply_text(intro, reply_markup=ReplyKeyboardMarkup(keyboard=[[kb], ["Cancel"]],
                                                                          one_time_keyboard=True))

        # TODO:
        # handle reply
        return AUTH

    else:
        return START_DATE


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn


def get_token(conn, username):
    SQL = f"select a.key from authtoken_token a " \
          f"join one_liner_customuser c on c.id = a.user_id where c.username=\"{username}\";"
    cur = conn.cursor()
    cur.execute(SQL)

    rows = cur.fetchall()
    return rows[0][0]


def auth(update, context):
    contact = update.effective_message.contact
    token = None
    reply_keyboard = [['Cool!']]
    phone_number = "+{0}".format(contact.phone_number)
    conn = create_connection(DB_FILE)
    try:
        ol_client = OneLiner_client()
        if ol_client:
            user_data = ol_client.get_user(data={
                "phone_number": phone_number
            })
            logger.info(user_data)
            username = user_data['username']
            token = get_token(conn, username)
            if token is not None:
                context.user_data['token'] = token
                update.message.reply_text('You were successfully authenticated!',
                                          reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return START_DATE
    except ValueError:
        update.message.reply_text('Your authentication was not successful! Try again :)',
                                  reply_markup=ReplyKeyboardRemove())
        return AUTH


def start_date(update, context):
    reply_keyboard = [['Today', 'Yesterday']]
    update.message.reply_text(
        'Do you want update for today or yesterday?\n'
        'Use /other to type another date.\n\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return DATE


def day_option_to_date(day):
    if day == 'Today':
        day_dtm = datetime.datetime.now()
    elif day == "Yesterday":
        day_dtm = datetime.datetime.now() - datetime.timedelta(days=1)
    return day_dtm


def other_day(update, context):
    user = update.message.from_user
    logging.info(update.message.text)
    update.message.reply_text('Enter date in format dd/mm/yyyy', reply_markup=ReplyKeyboardRemove())
    return PARSE


def parse_date(update, context):
    try:
        date = datetime.datetime.strptime(update.message.text, '%d/%m/%Y')
        context.user_data['date_pub'] = date.strftime(API_DATE_FORMAT)
        update.message.reply_text(
            'Thanks {0}. You typed date: {1} \n  Write your one liner update'.format(
                update.message.from_user.first_name, date))
        return INFO
    except ValueError:
        update.message.reply_text('Wrong date format. Should be dd/mm/yyyy')
        return DATE


def day(update, context):
    user = update.message.from_user
    date = day_option_to_date(update.message.text)
    logger.info("Ok %s. Your day chosen is %s", user, date)
    context.user_data['date_pub'] = date.strftime(API_DATE_FORMAT)
    update.message.reply_text('Thanks! I am sure it was amazing day! Now, send me a picture, '
                              'or send /skip if you don\'t want to. ',
                              reply_markup=ReplyKeyboardRemove())

    return PHOTO


def photo(update, context):
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    update.message.reply_text('Gorgeous! Now, send me a picture to be attached to your update, '
                              'or send /skip if you don\'t want to.')

    return INFO


def skip_photo(update, context):
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    update.message.reply_text('I bet you look great! Now, send me your update for the day '
                              'or send /skip.')

    return INFO




def publish_one_liner(update, context):
    user = update.message.from_user
    logger.info("Update of %s: %s", user.first_name, update.message.text)
    context.user_data['one_liner_txt'] = update.message.text
    # context.user_data['user_name'] = user.first_name
    ol_client = OneLiner_client();
    r = ol_client.post_one_liner(context.user_data, context.user_data['token'])
    if r.status_code != 201:
        update.message.reply_text('Ooops Something went wrong: %s' % r.text)
    else:
        update.message.reply_text('Thank you! Let\'s catch up tomorrow')

    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            AUTH: [MessageHandler(Filters.contact, auth)],

            START_DATE: [MessageHandler(Filters.regex('Cool'), start_date)],

            DATE: [MessageHandler(Filters.regex('Today|Yesterday'), day),
                   CommandHandler('other', other_day)],

            PHOTO: [MessageHandler(Filters.photo, photo),
                    CommandHandler('skip', skip_photo)],

            INFO: [MessageHandler(Filters.text, publish_one_liner)],

            PARSE: [MessageHandler(Filters.text, parse_date)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # dp.add_handler(MessageHandler(Filters.contact, contact_callback))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

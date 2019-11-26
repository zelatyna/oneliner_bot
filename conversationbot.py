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
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler
)
from oneliner_api import OneLiner_client, API_DATE_FORMAT

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

DATE, PHOTO, LOCATION, INFO, PARSE = range(5)
TOKEN = os.getenv("TOKEN")


def start(update, context):
    reply_keyboard = [['Today', 'Yesterday']]

    update.message.reply_text(
        'Hi! My name is Professor Freud. Please tel me what happened... ?'
        '*Send /other to type the date.\n\n',
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
            'Thanks {0}. You typed date: {1} \n  Write your one liner update'.format(update.message.from_user.first_name, date))
        return INFO
    except ValueError:
        update.message.reply_text('Wrong date format. Should be dd/mm/yyyy')
        return DATE


def day(update, context):
    user = update.message.from_user
    date = day_option_to_date(update.message.text)
    logger.info("Ok %s. Your day chosen is %s", user, date)
    context.user_data['date_pub'] = date.strftime(API_DATE_FORMAT)
    update.message.reply_text('Thanks! I am sure it was amazing day! Write your one liner update ',
                              reply_markup=ReplyKeyboardRemove())

    return INFO


#
# def photo(update, context):
#     user = update.message.from_user
#     photo_file = update.message.photo[-1].get_file()
#     photo_file.download('user_photo.jpg')
#     logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
#     update.message.reply_text('Gorgeous! Now, send me your location please, '
#                               'or send /skip if you don\'t want to.')
#
#     return LOCATION
#
#
# def skip_photo(update, context):
#     user = update.message.from_user
#     logger.info("User %s did not send a photo.", user.first_name)
#     update.message.reply_text('I bet you look great! Now, send me your location please, '
#                               'or send /skip.')
#
#     return LOCATION
#
#
# def location(update, context):
#     user = update.message.from_user
#     user_location = update.message.location
#     logger.info("Location of %s: %f / %f", user.first_name, user_location.latitude,
#                 user_location.longitude)
#     update.message.reply_text('Maybe I can visit you sometime! '
#                               'At last, tell me something about yourself.')
#
#     return INFO
#
#
# def skip_location(update, context):
#     user = update.message.from_user
#     logger.info("User %s did not send a location.", user.first_name)
#     update.message.reply_text('You seem a bit paranoid! '
#                               'At last, tell me something about yourself.')
#
#     return INFO

def publish_one_liner(context):
    ol_client = OneLiner_client()
    r = ol_client.post_one_liner(context.user_data)
    logging.info(r.status_code)

def one_liner(update, context):
    user = update.message.from_user
    logger.info("Update of %s: %s", user.first_name, update.message.text)
    context.user_data['one_liner_txt'] = update.message.text
    context.user_data['user_name'] = user.first_name
    publish_one_liner(context)
    update.message.reply_text('Thank you! I hope we can talk again some day.')
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
            DATE: [MessageHandler(Filters.regex('Today|Yesterday'), day),
                   CommandHandler('other', other_day)],

            # PHOTO: [MessageHandler(Filters.photo, photo),
            #         CommandHandler('skip', skip_photo)],
            #
            # LOCATION: [MessageHandler(Filters.location, location),
            #            CommandHandler('skip', skip_location)],

            INFO: [MessageHandler(Filters.text, one_liner)],

            PARSE: [MessageHandler(Filters.text, parse_date)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

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

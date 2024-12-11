#!/usr/bin/env python
# coding: utf-8
""" Logger Module for Live & Paper Trading """

import requests
import datetime
import logging
import threading
import pytz
import queue
from Logger_Module import logger

def get_time():
    current_time = datetime.datetime.now(pytz.timezone('ASIA/KOLKATA')).time()
    return current_time

def send_message(text):
    t = get_time().isoformat("seconds")

    # initializing mapping dictionary
    map_dict = {
        '.': '\\.',
        '!': '\\!',
        '}': '\\}',
        '{': '\\{',
        '|': '\\|',
        '=': '\\=',
        '-': '\\-',
        '+': '\\+',
        '(': '\\(',
        ')': '\\)',
        '_': '\\_'
    }
    # generator expression to construct vals
    # join to get string
    # message = ''.join(idx if idx not in map_dict else map_dict[idx]
    #                         for idx in text)

    final_message = f"{t}: {text} ({STRATEGY_NAME})"
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': GROUP_CHAT_ID,
        'text': final_message
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

def message_worker():
    while True:
        message = message_queue.get()
        if message is None:
            break
        send_message(message)
        message_queue.task_done()

def notify(text):
    message_queue.put(text)

def stop_worker():
    # Stop the worker thread
    logger.info('stopping the notification message worker')
    message_queue.put(None)
    worker_thread.join()

def telegram_credentials():
    try:
        # Config
        with open("Telegram_data.txt", mode='r') as f:
            credentials_data = f.readlines()
        for d in range(3): # mention range for number of data to retrieve
            credentials_data[d] = credentials_data[d].strip()
        logging.info("credentials imported from text file successfully.")
        return credentials_data
    except Exception as e:
        text = f"Error: {e}."
        logger.error(text)

# Retrieving bot token and chat ids
data = telegram_credentials()
# Queue to store messages
message_queue = queue.Queue()
# Replace with your bot's token
BOT_TOKEN = data[0] # 'your_telegram_bot_token'
CHAT_ID = data[1] # my_chat_id'
GROUP_CHAT_ID = data[2]
STRATEGY_NAME = 'Notify'

# Start the thread
logger.info('Starting notification message worker')
worker_thread = threading.Thread(target=message_worker)
worker_thread.start()

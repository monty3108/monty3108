# config.py

import datetime


""" All global variables and constants to declare here"""


# Global alice variable for functioning of Alice operations
alice = None

# set True for receiving notifications on Telegram
notification = False

# set True to print all log notifications
print_notification = True

# variable to maintain status of all orders to be updated by Order_Manager.py and
# live order status feed websocket OrderStatusFeed.py
order_status_dict = {}

# set True for Order Feed
order_Feed_required = True

# ##############Constants#############################

# **********Define Trade class for Nifty 50******************
INDEX_NIFTY_SYMBOL = 'NIFTY 50' #for index
FNO_NIFTY_SYMBOL = 'NIFTY' #for fno


# making required directories
dir_name = ['logs', 'pkl_obj'] # logs: placed all log related files, pkl_obj: placed all pkl objs


# File Paths includes json, pkl, and other types
# * under dir pkl_obj
path_complete_order_id = "pkl_obj/complete_order_id.pkl"
path_order_id_response = "pkl_obj/order_id_response.pkl"
path_order_status_feed = "pkl_obj/order_status_feed.pkl"
path_session    = "pkl_obj/session.pkl"
path_variable_container = "pkl_obj/variable_container.pkl"

# * under dir logs
path_balance = "logs/balance.csv"

# Variables related to timings
WEBSOCKET_START_TIME = datetime.datetime.strptime("08:30:00", "%H:%M:%S").time()
SESSION_START_TIME = datetime.datetime.strptime("09:14:59", "%H:%M:%S").time()
SESSION_END_TIME = datetime.datetime.strptime("15:30:00", "%H:%M:%S").time()




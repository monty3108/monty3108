# config.py
""" All global variables and constants to declare here"""


# Global alice variable for functioning of Alice operations
alice = None

# variable to maintain status of all orders to be updated by Order_Manager.py and
# live order status feed websocket OrderStatusFeed.py
order_status_dict = {}

# ##############Constants#############################

# **********Define Trade class for Nifty 50******************
INDEX_NIFTY_SYMBOL = 'NIFTY 50' #for index
FNO_NIFTY_SYMBOL = 'NIFTY' #for fno


# File Paths
logs_directory = "./logs"

# making required directories
dir_name = ['logs', 'pkl_obj'] # logs: placed all log related files, pkl_obj: placed all pkl objs


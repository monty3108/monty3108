# Buy Nifty Strategy
# Strategy for live market 
# Buy 1 lot on movement more than 150 : L1
# then on double of buy price(b) activate SL mechanism 
# b < 20
# when ltp = 2b, Put SL at b+2, securing principal: L2
# when ltp = 50, put SL at b+10, confirm profit 250: L3
# when ltp = 70, put SL at 2b+2, confirm profit ~500 (1:1): L4
# then above 80, maintain ltp/2 : L5

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import pandas as pd
from Trade_Live import Order, Trade
from Logger_Module import my_logger, logging
from pya3 import *
from Gen_Functions import *
from Alice_Module import *
import pickle
from OrderStatusFeed import start_order_feed_websocket

from enum import Enum

from Order_Manager import *


import threading
#import time
from queue import Queue
# constants from config files
import config



# Queue to store notifications in order
notification_queue = Queue()

# Function to process notifications from the queue
def notification_worker():
    while True:
        notification = notification_queue.get()  # Get the next notification from the queue
        if notification is None:  # If None is received, stop the worker
            break
        # Sending the notification
        my_logger(notification)
        notification_queue.task_done()

# Function to generate and send notifications
def log(message):
    # Put the notification into the queue for the worker to process
    if config.notification:
        notification_queue.put(message)
    if config.print_notification:
        print(message)

# Start a background thread that continuously processes notifications
worker_thread = threading.Thread(target=notification_worker)
worker_thread.daemon = True  # Ensures the worker thread exits when the main program exits
worker_thread.start()


# Level Enum & Variables classes defined
class Level(Enum):
    first = 1
    second = 2
    third = 3
    fourth = 4
    fifth = 5


class Variables :

    def __init__(self, change):
        self.change = change
        self.position = False
        self.first_order_sent = False
        self.level = Level.first
        self.inst = None
        self.qty = 0
        self.buy_hedge = False
        self.prices = {}
        self.last_sl_date= None
        self.tgt_date = None
        self.order_ids = {
            'order1' : None,
            'order2' : None,
            'order3' : None,
            'order_sl' : None,
            'order_tgt' : None,
            'order_sqoff' : None,
            'order_hedge': None

        }


def get_var_name(var):
    try:
        for name, value in globals().items():
            if value is var:
                logging.debug(f'Var name: {name}')
                return name
    except Exception as e:
        text = f"Error: {e}"
        my_logger(data_to_log=text, bot=True)
        logging.exception(text)


def reset_var(var) :
    """Func to reset the default values of variable of Variables Class"""
    fn = 'reser_var'
    try:
        global CHANGE
        var.change = CHANGE
        var.position = False
        var.first_order_sent = False
        var.level = Level.first
        var.dummy_inst = None
        var.qty = 0
        var.buy_hedge = False
        var.prices = {}
        var.order_ids = {
            'order1' : None,
            'order2' : None,
            'order3' : None,
            'order_sl' : None,
            'order_tgt' : None,
            'order_sqoff' : None
        }
        if ce_var.inst is None:
            ce.instrument = None
            logging.info('ce inst set to None')
        if pe_var.inst is None:
            pe.instrument = None
            logging.info('pe inst set to None')
        txt = f'{get_var_name(var)} is reset.'
        write_obj()
        log(txt)
        logging.info(txt)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def check_expiry():
    """Func to check expiry of ce_var & pe_var inst. If expired then reset to default."""
    fn = 'check_expiry'
    try:
        var = [ce_var, pe_var]
        date_format = '%Y-%m-%d'
        for i in var:
            if i.inst is not None:
                date_str = i.inst.expiry
                i_date = datetime.datetime.strptime(date_str, date_format)
                if i_date.date() < weekly_expiry_calculator():
                    text = f'{i.inst} is expired. Resetting {get_var_name(i)}.'
                    log(text)
                    logging.info(text)
                    reset_var(i)
                    write_obj()
                else:
                    text = f'{i.inst} is not expired.'
                    logging.info(text)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def obj_report():
    """Func to report values of ce_var and pe_var"""
    fn = 'obj_report'
    try:
        obj_list= [ce_var, pe_var]
        report = []
        for obj in obj_list:
            n = get_var_name(obj)
            a = obj.change
            b = obj.first_order_sent
            c = obj.level.value
            d = obj.inst
            eo = obj.qty
            f = obj.buy_hedge
            g = obj.prices
            h = obj.order_ids
            txt = f'{n}: Change: {a} First_order: { b} Level: {c} Inst: {d} Qty: {eo} Buy_hedge: {f} Prices: {g} Ids: {h} .'
            if d is None:
                report.append(f'{n}: None')
            else:
                report.append(txt)
        # dict_report= {'ce': report[0], 'pe' : report[1]}
        text = f'Obj Report: {report}'
        log(text)
        logging.info(text)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def check_hedge() :
    """Func to check buy posn & set buy_hedge to True"""
    try:
        global alice
        positions = alice.get_netwise_positions()
        # print(json.dumps(positions, indent=4))
        log_is_list = False
        if isinstance(positions, list):
            logging.info(f'positions log is a list. Continue process.')
            log_is_list = True
        else:
            logging.warning(f"Positions log is not a list, response: {positions}" )

        if log_is_list:
            position_log_list = []

            for log in positions:
                qty = int(log['Netqty'])
                # print(qty)
                buy_avg_price = float(log['Buyavgprc' ])
                option_type =  log['Opttype']

                position_log = {
                "Option_type": option_type,
                "AvgPrice": buy_avg_price,
                "Qty": qty
                }
                position_log_list.append(position_log)
            logging.info(f'all position: {position_log_list}')
            #print(json.dumps(trade_log_list, indent=4))
            for posn in position_log_list:
                if posn['Qty'] > 0:
                    if posn['AvgPrice'] > 0 and posn['AvgPrice']<5:
                        if posn['Option_type'] == 'CE':
                            logging.info('CE buy hedge is True')
                            ce_var.buy_hedge = True
                            write_obj()
                        else:
                            logging.info('PE buy hedge is True')
                            pe_var.buy_hedge = True
                            write_obj()

    except Exception as e:
        text = f"Error: {e}"
        logging.exception(text)


def calc_strike(ltp, premium=20, is_ce=True):
    """ Func to calculate strike as per premium For Nifty only"""
    fn = 'calc_strike'
    #rg #range
    try:
        inst_dict={}
        we = str(weekly_expiry_calculator())
        if is_ce is True:
            rg = range(0,25,1)
        else:
            rg = range(0,-25,-1)
        for i in rg:
            strike=strike_calc(ltp=ltp , base=50, strike_difference=i)
            inst = nf.get_instrument_for_fno(symbol=config.FNO_NIFTY_SYMBOL, expiry_date=we, is_fut=False,
                                             strike=strike, is_ce=is_ce)
            # print(f' inst: {inst, fn} ')
            info = alice.get_scrip_info(inst)
            # print(f' info: {info, fn} ')
            c_ltp= float(info['LTP'])
            if c_ltp<premium:
                # print(f'{inst} :{c_ltp, fn} ')
                inst_dict['inst'] = inst
                inst_dict['ltp'] = c_ltp
                txt= f'Strike Calculated for premium {premium}: {inst_dict} '
                log(txt)
                logging.info(txt)
                logging.info("Breaking for loop")
                break
        return inst_dict
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def calc_levels_price(first_entry, trade_var: Trade):
    """Func to calculate 2nd, 3rd entry and
    SL based on percent & max loss"""
    fn = 'calc_levels_price'
    try:
        x= first_entry
        y = (first_entry *2) + 2 # tgt
        z = first_entry * trade_var.qty # max buy amount

        dict = {
        'entry_price' : x,
        'tgt_price' : y,
        'max_loss' : z
        }
        logging.info(f'Calculated level prices: {dict}')
        return dict
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)
        return {}


# Check condition for change
def change_in_ltp(current_ltp):
    """func to check positive and negative change from previous close"""
    global POSITIVE_CHANGE, NEGATIVE_CHANGE, p_close
    try:
        previous_close = p_close
        ltp = current_ltp
        POSITIVE_CHANGE = round(ltp - previous_close, 2)
        NEGATIVE_CHANGE = round(previous_close - ltp,2)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.info(text)


def check_change(var_class: Variables, trade_var: Trade, is_ce = True):
    fn='first_level'

    change_in_ltp(nf.ltp)
    try:
        if var_class.level is Level.first:
            if is_ce:
                if POSITIVE_CHANGE > CHANGE:
                    if var_class.first_order_sent is False:
                        text = f'Index Change: {POSITIVE_CHANGE} taking posn'
                        log(text)
                        logging.info(text)
                        inst_dict = calc_strike(ltp=nf.ltp, premium=PREMIUM, is_ce=is_ce)
                        var_class.inst = inst_dict['inst'] # for notification & record
                        trade_var.instrument = inst_dict['inst']
                        trade_var.assigned(LOTS)
                        # sending buy order
                        var_class.order_ids['order1'] = send_order(transaction_type=TransactionType.Buy,
                                                                inst=trade_var.instrument,
                                                                qty=trade_var.qty,
                                                                order_type=OrderType.Market,
                                                                product_type=ProductType.Normal,
                                                                price=0.0
                                                                )
                        var_class.first_order_sent = True
                        subscribe()
                        ltp_update()
                elif var_class.first_order_sent is True:
                    order_id = var_class.order_ids['order1']
                    if is_pending(order_id):
                        return

                    if is_complete(order_id):
                        price = get_price(order_id)
                        var_class.prices = calc_levels_price(first_entry=price, trade_var=trade_var)
                        var_class.level = Level.second
                        var_class.qty = trade_var.qty
                        write_obj()
                        txt = f'{get_var_name(var_class)} order completed at price: {price}'
                        logging.info(txt)
                        log(txt)

        if var_class.level is Level.second:
            if trade_var.ltp >= var_class.prices['tgt_price'] and var_class.order_ids['order_tgt'] is None:
                # sending exit order
                var_class.order_ids['order_tgt'] = send_order(transaction_type=TransactionType.Sell,
                       inst=trade_var.instrument,
                       qty=trade_var.qty,
                       order_type=OrderType.Market,
                       product_type=ProductType.Normal,
                       price=0.0
                       )
                txt = f'{get_var_name(trade_var)} tgt criteria met. Ltp: {ce.ltp}'
                log(txt)
                logging.info(txt)
            elif var_class.order_ids['order_tgt'] is not None: #if order already sent, var_class.order_ids['order_tgt'] in not None
                order_id = var_class.order_ids['order_tgt']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    var_class.level = Level.third
                    write_obj()
                    txt = f"{get_var_name(trade_var)} tgt order completed."
                    log(txt)
                    logging.info(txt)
                    var_class.tgt_date = datetime.date.today()
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def read_obj() :
    global ce_var, pe_var
    ce_var, pe_var = read_pkl(file_path=config.path_variable_container)
    obj_report()


def write_obj() :
    global ce, pe, ce_buy, pe_buy, ce_var, pe_var
    obj_list = [ce_var, pe_var]
    write_pkl(obj=obj_list, file_path=config.path_variable_container)
    obj_report()


def today_expiry_day():
    '''func to return True if today is Thu Expiry Day'''
    fn = "today_expiry_day"
    try:
        we = weekly_expiry_calculator()
        today_date = datetime.date.today()
        return we == today_date
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)
        return None

logger.info('\n ####################' \
'\n **********New Log*************\n\n') 
logger.info(f'Time Check: {get_time() }') 
logger.info("All Modules imported successfully.")

# initialisation process
try:
    # create required directories
    create_dir(config.dir_name)

    # logging time variables
    time_cons = []
    time_cons.append(f"Websocket Start Time: {config.WEBSOCKET_START_TIME}")
    time_cons.append(f"Session Start Time: {config.SESSION_START_TIME}")
    time_cons.append(f"Session End Time; {config.SESSION_END_TIME}")
    for i in time_cons:
        logging.info(i)
except Exception as e:
    logging.exception(e)


# setting up program variables
try:
    # Exit if today is holiday
    is_holiday_today()

    # Constants
    CHANGE = 150
    PREMIUM = 20
    # MAX_LOSS = 4000.0
    POSITIVE_CHANGE = 0
    NEGATIVE_CHANGE = 0
    # to check if today is Expiry day. True if today is Expiry
    EXPIRY_DAY = today_expiry_day()
    EXIT_LEVEL = 5.5
    LOTS=1 # Mention lots. Lots qty will be extracted from instrument.
    QTY_ON_ERROR = 25
    txt = f'Parameters (a) Change: {CHANGE} (b) Premium: {PREMIUM} (c) Exit_Level: Entry + 2 (e) Expiry: {EXPIRY_DAY}'
    log(txt)
    logging.info(txt)

    # Generating Session ID
    if config.alice is None:
        logger.info("alice object is None. Calling get_session_id()")
        get_session_id()
        # session_id_generate()
        logging.debug(f'alice obj after calling:{config.alice} ')

    # Setting alice value from config file alice obj
    alice = config.alice

    # logging balance on csv. Try to maintain only one file
    # log_balance() # will be maintained in TradeNifty

except Exception as e:
    logging.exception(e)
    log(f"{e}. Exiting......")
    sys.exit()


# setting var for Index Nifty & ce and pe var & Sockets
try:
    # Nifty Index Instrument
    NIFTY_INST = config.alice.get_instrument_by_symbol(exchange='INDICES', symbol=config.INDEX_NIFTY_SYMBOL)
    logging.info(f'Nifty_Inst retrieved: {NIFTY_INST}')
    
    # nf for Nifty Index declared for Trade Class
    nf = Trade(alice=config.alice, paper_trade=True)
    logging.debug('nf declared for Trade class')
    
    nf.instrument = NIFTY_INST
    nf.assigned(lots=LOTS, qty_on_error=QTY_ON_ERROR)
    
    txt= f'nf class defined. Inst: {nf.instrument}'
    logging.info(txt)
    
    """### Previous Closing"""
    # four days back
    from_date = datetime.datetime.now().replace(hour=9, minute=14, second=0) - datetime.timedelta(days=4)
    logging.debug(f'from date: {from_date}')
    # yesterday
    to_date = datetime.datetime.now().replace(hour=15, minute=30, second=0) - datetime.timedelta(days=1)
    logging.debug(f'to date: {to_date}')

    # df = pd.DataFrame()
    df=nf.historical_data(no_of_days=None, interval="D", indices=True, from_datetime = from_date,to_datetime=to_date)
    # interval : ["1", "D"] // indices: True or False
    logging.debug(f'historical data: {df}')
    
    l=len(df['close']) - 1 # getting index of last element
    p_close = df.loc[l]['close']
    
    txt = f'Nifty Previous Close: {p_close} '
    logging.info(txt)
    
    # Initialising ce & pe
    logging.info("Initialising ce & pe")
    ce = Trade(alice=alice, paper_trade=False)
    
    ce_buy = Trade(alice=alice, paper_trade=False)
    
    pe = Trade(alice=alice, paper_trade=False)
    
    pe_buy = Trade(alice=alice, paper_trade=False)
    
    ce_var = Variables(CHANGE)
    pe_var = Variables(CHANGE)
    
    # Reading all objects
    read_obj()
    check_expiry()
    check_hedge() 
    
    # Websocket Connecting
    while get_time() < config.WEBSOCKET_START_TIME:
        sleep(30)
    
    log("WEBSOCKET_START_TIME(08:30) crossed.")
    logging.info("WEBSOCKET_START_TIME(08:30) crossed.")
    
    # code for connect websocket
    alice_websocket()

    # code for connect websocket for order feed updates
    if config.order_Feed_required:
        log("starting order feed")
        start_order_feed_websocket()
    
    #Waiting for session to start
    while get_time() <= config.SESSION_START_TIME:
        sleep(1)
        current_time=datetime.datetime.now(pytz.timezone('ASIA/KOLKATA')).time()
    
    log(f"SESSION_STARTED: {config.SESSION_START_TIME}.")
    logging.info(f"SESSION_STARTED: {config.SESSION_START_TIME}.")
    
    # subscribe for feeds (initially BN & Nifty)
    subscribe() # only assigned instruments will get subscribed for ltp feeds
    nf.ltp = 23532
    ltp_update() # exit if not updated withing 2 minutes

    # Dummy Instrument retrieval checking
    strike=strike_calc(ltp=nf.ltp , base=50, strike_difference=0)
    we = str(weekly_expiry_calculator())
    dummy_inst = nf.get_instrument_for_fno(symbol=config.FNO_NIFTY_SYMBOL, expiry_date=we, is_fut=False, strike=strike,
                                           is_ce=True)
    change_in_ltp(nf.ltp)
    dummy_msg = f'Dummy Inst at ATM: {dummy_inst}, Ltp: {nf.ltp}, close: {p_close}, Change: {POSITIVE_CHANGE}'
    logging.info(dummy_msg)
    log(dummy_msg)
except Exception as e:
    text = f"Error: {e}"
    log(f"{text}. Exiting....")
    logging.exception(text)
    sys.exit()


def strategy():
    fn = "Strategy"

    log('Entering While Loop')
    while True:

        try:
            check_change(var_class=ce_var, trade_var=ce, is_ce=True)
            check_change(var_class=pe_var, trade_var=pe, is_ce=False)

            # Sending report on every half an hour
            if (datetime.datetime.now().minute == 0 or datetime.datetime.now().minute == 30) and \
                    datetime.datetime.now().second == 0:
                txt = f'Nifty: {nf.ltp} {POSITIVE_CHANGE}'
                log(txt)
                log(position_report())
                sleep(2)

            # On Session Over @1530hrs break while loop
            if get_time() >= config.SESSION_END_TIME:
                log('Session End')
                logging.info('Session End')
                break

        except Exception as e:
            text = f"Error: {e}"
            log(text)
            logging.exception(text)

strategy_thread = threading.Thread(target=strategy)
strategy_thread.daemon = True  # Ensures the worker thread exits when the main program exits
strategy_thread.start()



while True:
    if get_time() >= config.SESSION_END_TIME:
        log('Session End')
        logging.info('Session End')
        break
    sleep(60)

# Closing websocket & unsubscribe inst"""
try:
    unsubscribe()
    alice.stop_websocket()
    
    """###Write Obj to the file obj.pkl"""
    write_obj()  
    logging.info('Exiting... ')
    sleep(30)
    # loggings
    log_trade_book()
    log_all_logs() 
except Exception as e:
    text = f"Error: {e}"
    log(text)
    logging.exception(text)


# Sending required logs to Telegram
try:
    docs_to_send = ["app_logs.txt", "data.txt", "logs/trade_log.csv",  "logs/balance.csv"]
    bot_token = '5398501864:AAFEn7ljDrKOVkXzhWX4P_khX9Xk-E8FicE'
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    bot_chat_id = ['5162043562']
    for item in docs_to_send:
        document = open(item, "rb")
        response = requests.post(url, data={'chat_id': bot_chat_id}, files={'document': document})
        # logging.info(response.json())
        logging.info(f"{item} sent to Bot.")
except Exception as e:
    text = f"Error: {e}"
    log(text)
    logging.exception(text)

# Deleting non required logs before closing
try:
    sleep(10)
    logging.info("Deleting non req files before closing.")
    docs_to_delete = ["data.txt"]
    for item in docs_to_delete:
        os.remove(item)
        logging.info(f"{item}: deleted")
except Exception as e:
    text = f"Error: {e}"
    logging.exception(text)
   
  
 

notification_queue.join()  # Block until all notifications are processed
print("All notifications sent, exiting.")
# Stop the worker thread
notification_queue.put(None)  # Send a signal to stop the worker
worker_thread.join()  # Wait for the worker thread to finish

# read_pkl(file_path=config.path_order_status_feed)
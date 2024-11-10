#OrderStatusFeed.py
#Aliceblue
#To be run after session generated


import websocket
import requests
import json
import threading
import time
import config
from Gen_Functions import create_dir, file_exist, read_pkl, write_pkl
from Logger_Module import my_logger, logging
import logging 
import datetime
# import threading
#import time
from queue import Queue

# Queue to store notifications in order
notification_queue = Queue()

# Function to process notifications from the queue
def notification_worker():
    while True:
        notification = notification_queue.get()  # Get the next notification from the queue
        if notification is None:  # If None is received, stop the worker
            break
        
        # Sending the notification
        #my_logger(data_to_log=notification, bot=True) 
        my_logger(notification) 
          
        notification_queue.task_done()

# Function to generate and send notifications
def log(message):
    # Put the notification into the queue for the worker to process
    notification_queue.put(message)

# Start a background thread that continuously processes notifications
worker_thread = threading.Thread(target=notification_worker)
worker_thread.daemon = True  # Ensures the worker thread exits when the main program exits
worker_thread.start()







def generate_token():
    logging.info('generating order feed token') 
    alice = config.alice
    if alice is None:
        logging.critical('alice var is None')
    """Generates an access token using API key and secret."""
    base_url ="https://ant.aliceblueonline.com/order-notify/" 
    token_url="ws/createWsToken"
    ws_url = "websocket" 
    Url = base_url + token_url
    
    #print(Url) 
    #sleep(10)
    res = alice._request(Url, "GET" )
    logging.info(f'generate token response: {res} ') 
    if res['status'] == 'Ok' :
        token_data = res
        access_token = token_data['result'][0]['orderToken']
        print(type(access_token)) 
        payload = {
        "orderToken" : access_token, 
        "userid": "AB154186" 
        } 
        datas = json.dumps(payload) 
        return datas
    else:
        logging.error(f"Error in token generation: {res.json()}")
        return None
   
    

def on_message(ws1, message):
    """Handles incoming WebSocket messages."""
    data = json.loads(message)
    new_msg = json.dumps(data, indent=4)
    print(new_msg) 
    log(new_msg) 
    logging.info(new_msg) 
    if 't' in data:
        manage_order_status(data) 

def on_error(ws1, error):
    """Handles WebSocket errors."""
    log(f"Error: {error}")

def on_close(ws1, close_status_code, close_msg):
    """Handles WebSocket closing."""
    logging.info("Order WebSocket closed")
    log("order feed closed") 
    start_orderfeed_websocket()

def on_open(ws1):
    """Handles WebSocket connection opening."""
    logging.info("WebSocket connection established")
    ws1.send(generate_token() )
    
    # Send heartbeat every minute to keep connection alive
    def send_heartbeat():
        while True:
            h = { 
              "heartbeat": "h", 
              "userId":"AB154186"
            }
            res = ws1.send(json.dumps(h))
            logging.debug(f"Heartbeat sent. Res: {res}")
            
            time.sleep(50)
    #starting heartbeat thread
    threading.Thread(target=send_heartbeat, daemon=True).start()

def start_orderfeed_websocket():
    """Establishes WebSocket connection."""
    
    logging.info("Establishes WebSocket connection.... ")
    thread = None
    create_dir = ['pkl_obj']
    WEB_SOCKET_URL =  "wss://ant.aliceblueonline.com/order-notify/websocket"
    
    #headers = token
    
    ws1 = websocket.WebSocketApp(WEB_SOCKET_URL,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    ws1.on_open = on_open
    thread = threading.Thread(target=ws1.run_forever) 
    thread.daemon = True
    thread.start()
    # ws1.run_forever()
    
def manage_order_status(order_msg):
    """func to maintain order status with order id""" 
    
    file_path = 'pkl_obj/orderstatusfeed.pkl'
    today_date = datetime.date.today()
    o_status = {} 
    msg = {} 
    order_id = order_msg['norenordno'] 
    msg[order_msg['norenordno']] = {
            'record_date' : today_date, 
            'status' : order_msg['status'], 
            'price' : order_msg['prc'], 
            'rejreason' : '' 
         }
    
    logging.info(msg)
    if file_exist(file_path):
         o_status = read_pkl(file_path)
         #if order_id in o_status:
         o_status[order_msg['norenordno']] = {
                'record_date' : today_date, 
                'status' : order_msg['status'], 
                'price' : order_msg['prc'], 
                'rejreason' : '' 
             }
         
         
    else:
         o_status[order_msg['norenordno']] = {
                'record_date' : today_date, 
                'status' : order_msg['status'], 
                'price' : order_msg['prc'], 
                'rejreason' : '' 
             }
    
    if o_status[order_id] ['status']=='REJECTED' :
        o_status[order_id] ['rejreason']=order_msg['rejreason'] 
        
    write_pkl(obj=o_status, file_path=file_path) 
    print(o_status) 
    
    
    
def del_old_records() :
    file_path = 'pkl_obj/orderstatusfeed.pkl'   
    today_date = datetime.date.today()
    records = read_pkl(file_path) 
    ids_to_del = [] 
    
    for record in records:
        print(record) 
        if records[record]['record_date'] < today_date:
            ids_to_del.append(record) 
            print(f'{record} deleted') 
           
    for id in ids_to_del:
             del records[id] 
            
    print('for exited') 
    print(records) 
    write_pkl(file_path=file_path, obj=records) 
    

file_path = 'pkl_obj/orderstatusfeed.pkl'   
msg = read_pkl(file_path)
for id in msg:
    msg[id]['record_date'] = msg[id]['record_date'].isoformat()
    print(msg[id]['record_date']) 

print(json.dumps(msg, indent=4)) 
#id ='24102300269409' 
#print(msg[id]['status']) 
#if id in msg:
#    print(type(msg[id]['record_date']) ) 
#    print(id) 
#    print(msg[id]) 
#    
#del_old_records() 
#    

#    



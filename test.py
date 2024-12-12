from My_Logger import setup_logger, LogLevel
from Notification_Module import notify, stop_worker, notify1

def me(msg):
    st = "nf_buy"
    text = f'{msg} ({st})'
    notify1(text)

def all(msg):
    st = "nf_buy"
    text = f'{msg} ({st})'
    notify(text)
# import My_Logger
# global STRATEGY_NAME
st = 'checking'
logger = setup_logger(logger_name="test", log_level=LogLevel.DEBUG)

logger.info('hello')
logger.debug("debug")

me('test')
all('personal')

stop_worker()
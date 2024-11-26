from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pya3 import *
from Gen_Functions import is_holiday_today, create_dir
from Alice_Module import *

from Order_Manager import *

# constants from config files
import config


create_dir(config.dir_name)

# Exit if today is holiday
is_holiday_today()

# Generating Session ID
if config.alice is None:
    logger.info("alice object is None. Calling get_session_id()")
    get_session_id()
    # session_id_generate()
    logging.debug(f'alice obj after calling:{config.alice} ')

# logging balance on csv. Try to maintain only one file
log_balance() # will be maintained in nf_buy
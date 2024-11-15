


def first_level():
    fn='first_level'
    global POSITIVE_CHANGE, NEGATIVE_CHANGE, PREMIUM, alice
    change_in_ltp(nf.ltp)
    try:
        if ce_var.level is Level.first:
        # For CE position
            if POSITIVE_CHANGE > CHANGE and ce_var.first_order_sent is False:
                ce_var.first_order_sent = True
                txt=f'Positive Change: {POSITIVE_CHANGE} taking Buy posn. '
                log(txt)
                logging.info(txt)
                inst_dict = calc_strike(ltp=nf.ltp,premium=PREMIUM,is_ce=True)
                ce.instrument = inst_dict['inst']
                premium = inst_dict['ltp']
                ce_var.inst = inst_dict['inst']
                ce.assigned(LOTS)
                #sbin = alice.get_instrument_by_symbol(exchange='NSE', symbol='SBIN' )
                ce_var.order_ids['order1'] = send_order(transaction_type=TransactionType.Buy ,
                                                       inst=ce_var.inst,
                                                       qty=25,
                                                       order_type=OrderType.Market,
                                                       product_type=ProductType.Normal,
                                                       price=0.0
                                                       )
                # ce.place_order(type_of_order=Order.sell, price=premium)
                subscribe()
                ltp_update()
                write_obj()
            elif ce_var.first_order_sent is True:
                order_id = ce_var.order_ids['order1']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    price = get_price(order_id)
                    ce_var.prices = calc_levels_price(price)
                    ce_var.level = Level.second
                    ce_var.qty = 25
                    write_obj()
                    txt= f'CE order1 completed at price: {price}'
                    logging.info(txt)
                    log(txt)

        if pe_var.level is Level.first:
            # For PE position
                if NEGATIVE_CHANGE > CHANGE and pe_var.first_order_sent is False:
                    pe_var.first_order_sent = True
                    txt=f'Negative Change: {NEGATIVE_CHANGE} taking Buy posn. '
                    log(txt)
                    logging.info(txt)
                    inst_dict = calc_strike(ltp=nf.ltp,premium=PREMIUM,is_ce=False)
                    pe.instrument = inst_dict['inst']
                    premium = inst_dict['ltp']
                    pe_var.inst = inst_dict['inst']
                    pe.assigned(LOTS)
                    pe_var.order_ids['order1'] = send_order(transaction_type=TransactionType.Buy,
                                                           inst=pe_var.inst,
                                                           qty=25,
                                                           order_type=OrderType.Limit,
                                                           product_type=ProductType.Normal,
                                                           price=premium
                                                           )
                    # ce.place_order(type_of_order=Order.sell, price=premium)
                    subscribe()
                    ltp_update()
                    write_obj()
                elif pe_var.first_order_sent is True:
                    order_id = pe_var.order_ids['order1']
                    if is_pending(order_id):
                        return

                    if is_complete(order_id):
                        price = get_price(order_id)
                        pe_var.prices = calc_levels_price(price)
                        pe_var.level = Level.second
                        pe_var.qty = 25
                        write_obj()
                        txt= f'PE order1 completed at price: {price}.'
                        logging.info(txt)
                        log(txt)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def second_level() :
    try:
        # For CE posns
        if ce_var.level is Level.second:
            if ce_var.order_ids['order2'] is None: # if order not sent
                if ce.ltp > ce_var.prices['second_entry']:
                    premium = ce.ltp
                    ce_var.order_ids['order2'] = send_order(transaction_type=TransactionType.Buy,
                           inst=ce_var.inst,
                           qty=25,
                           order_type=OrderType.Limit,
                           product_type=ProductType.Normal,
                           price=premium,
                           )
                    txt = f'CE Second entry criteria met. Ltp: {ce.ltp}'
                    log(txt)
                    logging.info(txt)
            else: # if order already sent
                order_id = ce_var.order_ids['order2']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    ce_var.level = Level.third
                    ce_var.qty += 25
                    write_obj()
                    txt = f"CE order2 completed. "
                    log(txt)
                    logging.info(txt)


        # For PE posns
        if pe_var.level is Level.second:
            if pe_var.order_ids['order2'] is None: # if order not sent
                if pe.ltp > pe_var.prices['second_entry']:
                    premium = pe.ltp
                    pe_var.order_ids['order2'] = send_order(transaction_type=TransactionType.Buy ,
                           inst=pe.instrument,
                           qty=25,
                           order_type=OrderType.Limit,
                           product_type=ProductType.Normal,
                           price=premium,
                           )
                    txt = f'PE Second entry criteria met. Ltp: {pe.ltp}'
                    log(txt)
                    logging.info(txt)
            else: # if order already sent
                order_id = pe_var.order_ids['order2']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    pe_var.level = Level.third
                    pe_var.qty += 25
                    write_obj()
                    txt = 'PE order2 completed'
                    logging.info(txt)
                    log(txt)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def third_level():
    try:
        # For CE posns
        if ce_var.level is Level.third:
            if ce_var.order_ids['order3'] is None: # if order not sent
                if ce.ltp > ce_var.prices['third_entry']:
                    buy_ce_hedge()
                    premium = ce.ltp
                    ce_var.order_ids['order3'] = send_order(transaction_type=TransactionType.Buy ,
                           inst=ce.instrument,
                           qty=25,
                           order_type=OrderType.Limit,
                           product_type=ProductType.Normal,
                           price=premium
                           )
                    logging.info("CE Third entry criteria met and order sent.")
            else: # if order already sent
                order_id = ce_var.order_ids['order3']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    ce_var.level = Level.fourth
                    ce_var.qty += 25
                    write_obj()
                    text = "CE order3 completed"
                    logging.info(text)
                    log(text)
        # For PE posns
        if pe_var.level is Level.third:
            if pe_var.order_ids['order3'] is None: # if order not sent
                if pe.ltp > pe_var.prices['third_entry']:
                    buy_pe_hedge()
                    premium = pe.ltp
                    pe_var.order_ids['order3'] = send_order(transaction_type=TransactionType.Buy ,
                           inst=pe.instrument,
                           qty=25,
                           order_type=OrderType.Limit,
                           product_type=ProductType.Normal,
                           price=premium
                           )
                    logging.info("PE Third entry criteria met and order sent.")
            else: # if order already sent
                order_id = pe_var.order_ids['order3']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    pe_var.level = Level.fourth
                    pe_var.qty += 25
                    write_obj()
                    text = "PE order3 completed"
                    logging.info(text)
                    log(text)
    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)


def fourth_level():
    """SL check"""
    try:
        # For CE posns
        if ce_var.level is Level.fourth:
            if ce_var.order_ids['order_sl'] is None: # if order not sent
                if ce.ltp > ce_var.prices['sl']:
                    ce_var.order_ids['order_sl'] = send_order(transaction_type=TransactionType.Sell,
                           inst=ce.instrument,
                           qty=ce_var.qty,
                           order_type=OrderType.Market,
                           product_type=ProductType.Normal,
                           price=0.0
                           )
                    logging.info("Tgt Triggered and order sent.")
            else: # if order already sent
                order_id = ce_var.order_ids['order_sl']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    reset_var(ce_var)
                    check_hedge()
                    write_obj()
                    text = "CE positions Squared Off. "
                    logging.info(text)
                    log(text)

        #For PE posns
        if pe_var.level is Level.fourth:
            if pe_var.order_ids['order_sl'] is None: # if order not sent
                if pe.ltp > pe_var.prices['sl']:
                    pe_var.order_ids['order_sl'] = send_order(transaction_type=TransactionType.Sell,
                           inst=pe.instrument,
                           qty=pe_var.qty,
                           order_type=OrderType.Market,
                           product_type=ProductType.Normal,
                           price=0.0
                           )
                    logging.info("Tgt Triggered and order sent.")
            else: # if order already sent
                order_id = pe_var.order_ids['order_sl']
                if is_pending(order_id):
                    return

                if is_complete(order_id):
                    reset_var(pe_var)
                    check_hedge()
                    write_obj()
                    text = "PE positions Squared Off."
                    logging.info(text)
                    log(text)

    except Exception as e:
        text = f"Error: {e}"
        log(text)
        logging.exception(text)

import pandas as pd
from Gen_Functions import *
import config

ce_var, pe_var = read_pkl(config.path_variable_container)

# df = pd.read_csv("logs/trade_log.csv")
# df['Amount'] = round(df['Amount'],2)
# df['Profit'] = round(df['Profit'],2)
# df.to_csv("logs/trade_log.csv", index=False)
# print(df)


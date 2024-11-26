import pandas as pd

df = pd.read_csv("logs/trade_log.csv")
df['Amount'] = round(df['Amount'],2)
df['Profit'] = round(df['Profit'],2)
df.to_csv("logs/trade_log.csv", index=False)
print(df)
import pandas as pd

df = pd.read_csv('./oportunidades.csv', encoding='utf-8')

df[ 'is_alert'][df[ 'is_alert']=="Request for EOI"] = False

df.to_csv('./oportunidades.csv', index=False, encoding='utf-8', header=True)

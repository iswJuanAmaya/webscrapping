import pandas as pd 


df = pd.read_csv('../oportunidades.csv', encoding='utf-8')

#add the new job to the dataset
df = df.append({'url_detail_id': 'detail_url', 'scrapped_day': 'today',  'title': 'title', 
        'opening_date': 'opening_date', 'closing_date': 'closing_date','location': 'location',
        'is_alert':'is_alert', 'source': 'source','tipo':'tipo','reference':'reference','organization':'organization'}, ignore_index=True)

print(df)

df.to_csv('../oportunidades.csv', index=False, encoding='utf-8', header=True)
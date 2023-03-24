#entry point
import pandas as pd
import requests
from lxml import html
from datetime import date
import time 
import random
import re

def get_page(url):
    #genera un random para dormir entre 4 y 12 segundos antes de hacer el requests
    rdm = random.randint(4, 12)
    print(f"dormirá por {rdm} segundos antes del requests")
    time.sleep(rdm)

    #hace el requests
    page = requests.get(url)
    tree = html.fromstring(page.content)
    return tree


def load_csv(file_name):
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def get_by_xpath_and_clean(tree, xpath, i=0):
    """"""
    try:
        text = tree.xpath(xpath)[i]
        text = re.sub(r'[\n\t\xa0]', '', text).strip()
        return text
    except:
        return None


def find_new_jobs(tree):
    """"""
    global df, source, today, words_to_look, file_name
    #obtiene los divs que envuelve a cada oportunidad
    jobs = tree.xpath('//div[contains(@id,"job_list_")]')
    print(f"{len(jobs)} trabajos encontrados")

    for job in jobs:
        #get the url of detail
        detail_url = job.xpath('./div/div/p/a[contains(@href,"/jobs/")]/@href')[0]

        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada, obteniendo detalle...')
            detail = get_page(detail_url)

            #get the title
            title = get_by_xpath_and_clean(detail, '//div[@class="content_header"]/h1/text()')
            #get the location
            location = get_by_xpath_and_clean(detail, '//h4[@class="primary_location"]/a/text()', i=1)
            #Opening Date:
            opening_date = get_by_xpath_and_clean(detail, 
                                '//label[contains(text(),"External Opening Date:")]/text()')\
                                .replace('External Opening Date:','').strip()
            #Closing Date
            closing_date = get_by_xpath_and_clean(detail, 
                                '//label[contains(text(),"External Closing Date: ")]/text()')\
                                .replace('External Closing Date:','').strip()
            
            #find the body of the job and look for the words_to_look to appear once at least
            is_alert = False
            text_for_alert = ' '.join(detail.xpath('//div[@class="job_description"]//descendant::text()'))
            text_for_alert = re.sub(r'[\n\t\xa0]', '', text_for_alert ).strip().lower()
            if "requirements" in text_for_alert:
                text_for_alert = text_for_alert.split("requirements")[0]
            elif "requisitos"  in text_for_alert:
                text_for_alert = text_for_alert.split("requisitos")[0] 
                
            if any(word in text_for_alert for word in words_to_look):
                is_alert = True

            #add the new job to the dataset
            df = df.append({'url_detail_id': detail_url, 'scrapped_day': today,  'title': title, 
                    'opening_date': opening_date, 'closing_date': closing_date,'location': location,
                    'is_alert':is_alert, 'source': source}, ignore_index=True)

    df.to_csv(file_name, index=False, encoding='utf-8', header=True)





def main():
    global main_url, df, source, today, words_to_look, file_name

    words_to_look = [
        'salud',
        'farmacoeconomía',
        'medicamentos',
        'health',
        'pharmacoeconomics',
        'medicines',
        'santé',
        'pharmacoéconomie',
        'médicaments',
        'saude',
        'farmacoeconomia',
        'medicamentos'
    ]
    
    today = date.today().strftime("%d/%m/%Y")
    source = 'IDB'
    file_name = '../oportunidades.csv'
    main_url = 'https://iadbcareers.referrals.selectminds.com/'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    print("\nObteniendo la pagina principal...")
    tree = get_page(main_url)
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(tree)


if __name__ == "__main__":
    main()
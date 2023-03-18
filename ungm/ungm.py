#entry point
import pandas as pd
import requests
from lxml import html
from datetime import date
import time 
import random
import re

def get_page():
    #genera un random para dormir entre 4 y 12 segundos antes de hacer el requests
    rdm = random.randint(4, 12)
    print(f"dormirá por {rdm} segundos antes del requests")
    time.sleep(rdm)

    hoy = date.today().strftime("%d-%b-%Y")
    headers = {
        'authority': 'www.ungm.org',
        'accept': '*/*',
        'accept-language': 'es-419,es;q=0.9,es-MX;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        # 'cookie': 'UNGM.UserPreferredLanguage=en; _ga=GA1.2.278469780.1678230703; _gid=GA1.2.548688420.1679160053; GCLB=CNjEvo3msJiMxQE',
        'origin': 'https://www.ungm.org',
        'referer': 'https://www.ungm.org/Public/Notice',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    json_data = {
        'PageIndex': 0,
        'PageSize': 25,
        'Title': '',
        'Description': '',
        'Reference': '',
        'PublishedFrom': hoy,
        'PublishedTo': hoy,
        'DeadlineFrom': '',
        'DeadlineTo': '',
        'Countries': [],
        'Agencies': [],
        'UNSPSCs': [],
        'NoticeTypes': [],
        'SortField': 'DatePublished',
        'SortAscending': False,
        'isPicker': False,
        'IsSustainable': False,
        'NoticeDisplayType': None,
        'NoticeSearchTotalLabelId': 'noticeSearchTotal',
        'TypeOfCompetitions': [],
    }
    print(f"pidiendo jobs para el día: {hoy}")
    #hace el requests
    page = requests.post('https://www.ungm.org/Public/Notice/Search',  
                        headers=headers, json=json_data)
    tree = html.fromstring(page.content)
    return tree


def load_csv(file_name):
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def get_by_xpath_and_clean(tree, xpath, i=0):
    """"""
    try:
        text = tree.xpath(xpath)[i]
        text = re.sub(r'[\n\t]', '', text).strip()
        return text
    except:
        return None


def find_new_jobs(tree):
    """"""
    global df, source, today, words_to_look, file_name
    #obtiene los divs que envuelve a cada oportunidad
    jobs = tree.xpath('//div[@role="row"]')
    print(f"{len(jobs)} trabajos encontrados")

    for job in jobs:
        #get the url of detail
        detail_url = main_url + '/' + get_by_xpath_and_clean(job,'./@data-noticeid')
        
        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada')
            #type RFQ
            reference = get_by_xpath_and_clean(job, './td[2]/text()')
            #get the title
            title = get_by_xpath_and_clean(job, './/span[@class="ungm-title ungm-title--small"]/text()')
            #type of opportunity
            type_of_opportunity = get_by_xpath_and_clean(job, 
                        './/div[@data-description="Deadline"]/following-sibling::div[3]/span/label/text()')
            
            #get the location (type RFQ)
            location = get_by_xpath_and_clean(job, 
                            './/div[@data-description="Deadline"]/following-sibling::div[5]/span/text()')
            #Opening Date:
            opening_date = get_by_xpath_and_clean(job, 
                                './/div[@data-description="Deadline"]/following-sibling::div/span/text()')
            #Closing Date
            closing_date = get_by_xpath_and_clean(job, './/div[@data-description="Deadline"]/span/text()')
            
            #find the body of the job and look for the words_to_look to appear once at least
            is_alert = False

            text_for_alert = title.strip().lower()
            if any(word in text_for_alert for word in words_to_look):
                is_alert = True
                
            #add the new job to the dataset
            df = df.append({'url_detail_id': detail_url, 'scrapped_day': today,  'title': title, 
                    'opening_date': opening_date, 'closing_date': closing_date,'location': location,
                    'is_alert': is_alert, 'source': source}, ignore_index=True)

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
        'santé ',
        'pharmacoéconomie',
        'médicaments',
        'saude',
        'farmacoeconomia',
        'medicamentos'
    ]

    today = date.today().strftime("%d/%m/%Y")
    source = 'ungm'
    file_name = './ungm_ops.csv'
    main_url = 'https://www.ungm.org/Public/Notice'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    print("\nObteniendo la pagina principal...")
    tree = get_page()
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(tree)


if __name__ == "__main__":
    main()
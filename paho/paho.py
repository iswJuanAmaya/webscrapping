#entry point
import pandas as pd
import requests
from lxml import html
from datetime import date
import time 
import random
import re

def get_main_page() -> dict:
    """
    this function makes the requests to specific url and returns the 
    parsed response as json.
    """
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en-US',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://paho.wd5.myworkdayjobs.com',
        'Referer': 'https://paho.wd5.myworkdayjobs.com/en-US/pahocareers',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'X-CALYPSO-CSRF-TOKEN': 'eaa62170-06f9-41c6-a714-ca05b831ba12',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    json_data = {
        'appliedFacets': {},
        'limit': 20,
        'offset': 0,
        'searchText': '',
    }

    response = requests.post(
        'https://paho.wd5.myworkdayjobs.com/wday/cxs/paho/pahocareers/jobs',
        headers=headers,
        json=json_data
        )
    
    return response.json()


def get_detail_page(url:str)-> dict:
    """
    this function makes the requests to @url and returns the 
    parsed response as json.  wait a random time first to avoid being blocked
    """
    #genera un random para dormir entre 4 y 12 segundos antes de hacer el requests
    rdm = random.randint(4, 12)
    print(f"dormirá por {rdm} segundos antes del requests")
    time.sleep(rdm)

    #hace el requests
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en-US',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Cookie': 'wday_vps_cookie=2468753930.1075.0000; timezoneOffset=360; PLAY_SESSION=9bbdb5aae9e9ccbc8f6e28b53421d4f30c05a554-paho_pSessionId=q6f78sgg8ajpos3jrd23k9r04n&instance=wd5prvps0006f; enablePrivacyTracking=false; wd-browser-id=1248b7b1-89a2-4e63-af0d-0d52436ee61e; CALYPSO_CSRF_TOKEN=13c1a9df-2901-4735-899a-d7fa812eb92d; TS014c1515=018b6354feaa5b28fb929e208d509e5813066a6117120ca00e77ec3f585c66e1977cd3e23cd72bfa07773c03898549fea9b9dc28f5',
        'Referer': 'https://paho.wd5.myworkdayjobs.com/en-US/pahocareers/details/PAHO-Consultant---Lab-Specialist---Influenza-Team_Req-03092-1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'X-CALYPSO-CSRF-TOKEN': 'eaa62170-06f9-41c6-a714-ca05b831ba12',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    response = requests.get(
        url,
        headers=headers,
    )

    return response.json()


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def get_by_xpath_and_clean(tree:html , xpath:str, i:int=0)->str:
    """"""
    try:
        text = tree.xpath(xpath)[i]
        text = re.sub(r'[\n\t]', '', text).strip()
        return text
    except:
        return None


def find_new_jobs(res:dict):
    """given @res, this function looks for new jobs and adds them to the dataset"""

    global df, source, today, words_to_look, file_name, main_url

    #obtiene los divs que envuelve a cada oportunidad
    jobs = res['jobPostings']

    print(f"{len(jobs)} trabajos encontrados")

    for job in jobs:
        """
        for each job, get the detail and add it to the dataset,
        also looks fot the words_to_look in the detail to see if 
        it is an alert
        """
        #get the url of detail
        detail_url = main_url + '/details/' + job['externalPath'].rsplit('/', 1)[1]

        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada, obteniendo detalle...')
            json_detail_url = 'https://paho.wd5.myworkdayjobs.com/wday/cxs/paho/pahocareers' +\
                                job['externalPath']
            detail = get_detail_page(json_detail_url)

            #id = job['bulletFields'][0]
            #get the title
            title = job['title']
            #get the location
            location = detail['jobPostingInfo']['country']['descriptor']
            #Opening Date:
            opening_date = detail['jobPostingInfo']['startDate']
            #Closing Date
            closing_date = detail['jobPostingInfo']['jobDescription']\
                                .split("<p></p><p><b>")[4].split("</b></p>")[1]
            
            #find the body of the job and look for the words_to_look to appear once at least
            is_alert = False
            text_for_alert = detail['jobPostingInfo']['jobDescription']\
                                .split("ADDITIONAL INFORMATION")[0]
            text_for_alert = re.sub(r'[\n\t\xa0]', '', text_for_alert ).strip().lower()
            if any(word in text_for_alert for word in words_to_look):
                is_alert = True

            #add the new job to the dataset
            df = df.append({'url_detail_id': detail_url, 'scrapped_day': today,  'title': title, 
                    'opening_date': opening_date, 'closing_date': closing_date,'location': location,
                    'is_alert':is_alert, 'source': source}, ignore_index=True)

    df.to_csv(file_name, index=False, encoding='utf-8', header=True)


def main():
    """
    no visita la url de la página, visita el endpoint que trae las oportunidades
    son 2 endpoints, uno para la pagina principal y otro para la de detalle, además
    esta pagina requiere headers y params en sus requests y retorna json
    """
    global main_url, df, source, today, words_to_look, file_name
    #el espacio es para que busca la palabra exacta, si puede detectar healthier como health
    words_to_look = [
        ' farmacoeconomía ',
        ' sistema de salud ',
        ' pharmacoeconomics ',
        ' health systems ',
        ' pharmacoéconomie ',
        ' systèmes de santé ', 
        ' farmacoeconomia ',
        ' sistemas de saude '
    ]

    today = date.today().strftime("%d/%m/%Y")
    source = 'PAHO'
    file_name = '../oportunidades.csv'
    main_url = 'https://paho.wd5.myworkdayjobs.com/en-US/pahocareers'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    print("\nObteniendo la pagina principal...")
    tree = get_main_page()
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(tree)


if __name__ == "__main__":
    main()
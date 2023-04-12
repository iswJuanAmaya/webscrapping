#entry point
import pandas as pd
import requests
from lxml import html
from datetime import date
import time 
import random
import re

def get_page(url:str) -> html:
    """
    this function makes the requests to the @url and returns the 
    parsed html tree. as this function is used algo to get the detail
    waith a random time first to avoid being blocked
    """
    #genera un random para dormir entre 4 y 12 segundos antes de hacer el requests
    rdm = random.randint(4, 12)
    print(f"dormirá por {rdm} segundos antes del requests")
    time.sleep(rdm)

    #hace el requests
    page = requests.get(url)
    tree = html.fromstring(page.content)
    return tree


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def get_by_xpath_and_clean(tree:html , xpath:str, i:int=0)->str:
    """ this function gets the text from @tree via @xpath in the @i index and 
    cleans it from \n, \t and \xa0, and returns the text. if @i is 'join' it
    returns the text of all the elements in the xpath joined by a space"""
    try:
        if i=='join':
            text = tree.xpath(xpath)
            text = re.sub(r'[\n\t\xa0]', '', ' '.join(text)).strip()
            return text
        else:
            text = tree.xpath(xpath)[i]
            text = re.sub(r'[\n\t\xa0]', '', text).strip()
            return text
    except:
        return None


def find_new_jobs(tree:html):
    """ given @tree, this function looks for new jobs and adds them to the dataset """

    global df, source, today, words_to_look, file_name

    #get a list of jobs and ommits the first one and the last one
    jobs = tree.xpath('//tbody/tr')[1:-1]

    print(f"{len(jobs)} trabajos encontrados")

    for i, job in enumerate(jobs):
        """
        for each job, get the detail and add it to the dataset,
        also looks fot the words_to_look in the detail to see if 
        it is an alert
        """
        try:
            #get the url of detail
            detail_url = 'https://www.oecd.org' + get_by_xpath_and_clean(job, '(./td[4]/*//a)[1]/@href')
        except Exception as e:
            print(f"fallo obteniendo el url del detalle con error: \n {e}")
            continue
        try:
            #looks if the detail url is already in the dataset
            if df['url_detail_id'][df['url_detail_id']==detail_url].any():
                print('this job is already in the dataset')
                continue
            #if not  exist, get the detail
            else:
                print('nueva oportunidad encontrada')
                #type RFQ
                type_RFQ = get_by_xpath_and_clean(job, './td[2]/text()')
                #get the title
                title = get_by_xpath_and_clean(job, '(./td[4]/*//a)[1]/text()')
                #get the location (type RFQ)
                location = 'N/A'
                #Opening Date:
                opening_date = get_by_xpath_and_clean(job, './td[5]/text()')
                #Closing Date
                closing_date = get_by_xpath_and_clean(job, './td[6]/text()', i='join')
                
                #find the body of the job and look for the words_to_look to appear once at least
                is_alert = False

                text_for_alert = title.strip().lower()
                if any(word in text_for_alert for word in words_to_look):
                    is_alert = True
                #add the new job to the dataset
                df = df.append({'url_detail_id': detail_url, 'scrapped_day': today,  'title': title, 
                        'opening_date': opening_date, 'closing_date': closing_date,'location': location,
                    'is_alert': is_alert, 'source': source,'tipo':type_RFQ}, ignore_index=True)
        
        except Exception as e:
            print(f"fallo obteniendo oportunidad {detail_url} con error: \n {e}")
            continue

    df.to_csv(file_name, index=False, encoding='utf-8', header=True)


def main():
    """
    visita la pagina principal y busca las nuevas oportunidades, 
    no visita la url de detalle, las keword las busca solo en el titulo
    """
    global main_url, df, source, today, words_to_look, file_name
    #el espacio es para que busca la palabra exacta, si puede detectar healthier como health
    words_to_look = [
        ' salud ',
        ' farmacoeconomía ',
        ' medicamentos ',
        ' health ', 
        ' pharmacoeconomics ',
        ' medicines ',
        ' santé ',
        ' pharmacoéconomie ',
        ' médicaments ',
        ' saude ',
        ' farmacoeconomia ',
        ' medicamentos '
    ]

    today = date.today().strftime("%d/%m/%Y")
    source = 'OECD'
    file_name = '../oportunidades.csv'
    # file_name = 'oecd_ops.csv'
    main_url = 'https://www.oecd.org/callsfortenders/listofallcallsfortenders.htm'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    print("\nObteniendo la pagina principal...")
    tree = get_page(main_url)
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(tree)


if __name__ == "__main__":
    main()


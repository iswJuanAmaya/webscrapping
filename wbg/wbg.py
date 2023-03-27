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
    #obtiene los divs que envuelve a cada oportunidad
    jobs = tree.xpath('//table/tbody/tr')
    print(f"{len(jobs)} trabajos encontrados")

    for i, job in enumerate(jobs):
        """
        for each job, get the detail and add it to the dataset,
        also looks fot the words_to_look in the detail to see if 
        it is an alert
        """
        #get the url of detail
        detail_url = main_url + "/" + get_by_xpath_and_clean(job,'./td/a/@href').rsplit('/', 1)[1]
        
        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada')

            detail_page = get_page(detail_url)

            #type RFQ
            reference = get_by_xpath_and_clean(job,'./td[2]/text()')
            #get the title
            title = get_by_xpath_and_clean(job,'./td/a/text()')
            #Opening Date:
            opening_date = get_by_xpath_and_clean(job,'./td[3]/text()')
            #Closing Date
            closing_date = get_by_xpath_and_clean(job,'./td[4]/text()')
            
            #find the body of the job and look for the words_to_look to appear once at least
            is_alert = False

            text_for_alert = ( title + get_by_xpath_and_clean(detail_page, 
                                            '//div[@class="c14v1-body-text"]/descendant::text()', i='join')\
                            ).strip().lower()
            
            if any(word in text_for_alert for word in words_to_look):
                is_alert = True

            #add the new job to the dataset
            df = df.append({'url_detail_id': detail_url, 'scrapped_day': today, 'title': title, 
                    'opening_date': opening_date, 'closing_date': closing_date, 'reference':reference,
                    'is_alert': is_alert, 'source': source}, ignore_index=True)

    df.to_csv(file_name, index=False, encoding='utf-8', header=True)


def main():
    """
    obtiene la pagina principal via reques y visita la url de cada detalle
    """
    global main_url, df, source, today, words_to_look, file_name

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
    source = 'wbg'
    main_url = 'https://www.worldbank.org/en/about/corporate-procurement/business-opportunities/administrative-procurement'
    file_name = '../oportunidades.csv'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    print("\nObteniendo la pagina principal...")
    tree = get_page(main_url)
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(tree)


if __name__ == "__main__":
    main()
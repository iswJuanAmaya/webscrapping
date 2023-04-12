#entry point
import pandas as pd
import requests
from lxml import html
from datetime import date
import time 
import random
import re

def get_page(page: int)->html:
    """
    this function makes the requests to the @url and returns the 
    parsed html tree. wait a random time first to avoid being blocked
    """
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
    
    """depending on @page is the number of page will be requested
    the first page is 0, the second is 1, etc, then also the date is required."""
    json_data = {
        'PageIndex': page,
        'PageSize': 15,
        'Title': '',
        'Description': '',
        'Reference': '',
        'PublishedFrom': '',
        'PublishedTo': hoy,
        'DeadlineFrom': hoy,
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
    page_resp = requests.post('https://www.ungm.org/Public/Notice/Search',  
                        headers=headers, json=json_data)
    
    tree = html.fromstring(page_resp.content)
    return tree


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def get_by_xpath_and_clean(tree:html , xpath:str, i:int=0)->str:
    """ this function gets the text from @tree via @xpath in the @i index and 
    cleans it from \n, \t and \xa0 """
    try:
        text = tree.xpath(xpath)[i]
        text = re.sub(r'[\n\t]', '', text).strip()
        return text
    except:
        return None


def find_new_jobs(tree:html)->int:
    """given @tree, this function looks for new jobs and adds them to the dataset,
    also return how many NEW jobs were found"""
    global df, source, today, words_to_look, file_name
    #obtiene los divs que envuelve a cada oportunidad
    jobs = tree.xpath('//div[@role="row"]')
    print(f"{len(jobs)} trabajos encontrados")

    nuevas_ops = 0
    for job in jobs:
        """
        for each job, get the detail and add it to the dataset,
        also looks fot the words_to_look in the detail to see if 
        it is an alert
        """
        #get the url of detail
        detail_url = main_url + '/' + get_by_xpath_and_clean(job,'./@data-noticeid')
        
        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada')
            reference = get_by_xpath_and_clean(job, './/div[@data-description="Deadline"]/following-sibling::div[4]/span/text()')
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
                    'is_alert': is_alert, 'source': source,'tipo':type_of_opportunity,
                    'reference':reference}, ignore_index=True)
            
            nuevas_ops += 1

    return nuevas_ops 


def main():
    """
    Esta pagina busca por el día, 
    hace un solo requests(a url no especial no main_url) que obtiene todos los 
    jobs del día(requiere headers y params), no hace requests por detalle .
    """
    global main_url, df, source, today, words_to_look, file_name
    #el espacio es para que busca la palabra exacta, si puede detectar healthier como health
    #está usando las keywords de unops por mientras
    words_to_look = [
        ' salud ',
        ' farmacoeconomía ',
        ' medicamentos ',
        ' health ',
        ' pharmacoeconomics ',
        ' medicines ',
        ' saude ',
        ' farmacoeconomia ',
        ' medicamentos ',
        ]

    today = date.today().strftime("%d/%m/%Y")
    source = 'ungm'
    file_name = '../oportunidades.csv'
    main_url = 'https://www.ungm.org/Public/Notice'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    #paginacion/ infinite scroll down simulation
    for page in range(1, 15):
        """ iterates from page 0 to page 5,
        each page has to return a maximum of 15 jobs,
        if it returns less than 10 NEW jobs, it means that 
        it is the last page, and the pagination is over.
        """
        print(f"Obteniendo pagina {page}...")
        tree = get_page(page)
        
        print(f"\nBuscando nuevas oportunidades. en pagina {page}..")
        nuevas_ops = find_new_jobs(tree)

        if nuevas_ops > 10:
            print(f"Se encontraron {nuevas_ops} nuevas oportunidades en la pagina {page} se hará un scroll más")
        else:
            print(f"Se encontraron {nuevas_ops} nuevas oportunidades en la pagina {page} se terminará el scroll")
            break
    
    df.to_csv(file_name, index=False, encoding='utf-8', header=True)


if __name__ == "__main__":
    main()
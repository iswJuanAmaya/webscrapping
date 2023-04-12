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
    wait a random time first to avoid being blocked
    """
    #genera un random para dormir entre 4 y 12 segundos antes de hacer el requests
    rdm = random.randint(4, 12)
    print(f"dormirá por {rdm} segundos antes del requests")
    time.sleep(rdm)

    #hace el requests
    page = requests.get(url)
    tree = html.fromstring(page.content)
    return tree


#special function to perform the first request
def get_main_page(main_url:str) -> dict:
    """this is a special requests that brings
    all the jobs in the page
    """
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'es-419,es;q=0.9,es-MX;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Origin': 'https://jobs.giz.de',
        'Referer': 'https://jobs.giz.de/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    #los paramertros definene cuantas oportunidades trae y que propiedades.
    params = {
        'data': '{"LanguageCode":"EN","SearchParameters":{"FirstItem":1,"CountItem":10000,"Sort":[{"Criterion":"PublicationStartDate","Direction":"DESC"}],"MatchedObjectDescriptor":["ID","PositionTitle","PositionURI","PositionShortURI","PositionLocation.CountryName","PositionLocation.CityName","PositionLocation.Longitude","PositionLocation.Latitude","PositionLocation.PostalCode","PositionLocation.StreetName","PositionLocation.BuildingNumber","PositionLocation.Distance","JobCategory.Name","PublicationStartDate","PublicationEndDate","ParentOrganizationName","OrganizationShortName","CareerLevel.Name","JobSector.Name","PositionIndustry.Name","PublicationCode"]},"SearchCriteria":[{"CriterionName":"PublicationChannel.Code","CriterionValue":["12"]}]}',
    }

    response = requests.get(main_url, params=params, headers=headers)
    return response.json()


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def clean(text:str) -> str:
    """this function cleans the @text from \n, \t and \xa0"""
    try:
        return re.sub(r'[\n\t\xa0]', '', text).strip()
    except:
        return None


def get_by_xpath_and_clean(tree:html , xpath:str, i:int=0)->str:
    """ this function gets the text from @tree via @xpath in the @i index and 
    cleans it from \n, \t and \xa0 """
    try:
        text = tree.xpath(xpath)[i]
        text = re.sub(r'[\n\t\xa0]', '', text).strip()
        return text
    except:
        return None


def find_new_jobs(tree:html):
    """given @tree, this function looks for new jobs and adds them to the dataset"""

    global df, source, today, words_to_look, file_name
    #obtiene los divs que envuelve a cada oportunidad
    jobs = tree['SearchResult']['SearchResultItems']
    print(f"{len(jobs)} trabajos encontrados")
    counter = 0
    for i, job in enumerate(jobs):
        """
        for each job, get the detail and add it to the dataset,
        also looks fot the words_to_look in the detail to see if 
        it is an alert
        """
        #get the url of detail
        detail_url = job['MatchedObjectDescriptor']['PositionURI']

        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada, obteniendo detalle...')
            try:
                detail_page = get_page(detail_url)
                counter += 1

                #get the title
                title = clean(job['MatchedObjectDescriptor']['PositionTitle'])
                #get the location
                try:
                    location = clean(job['MatchedObjectDescriptor']['PositionLocation'][0]['CityName'])
                except Exception as e:
                    print(f"no se pudo obtener la ubicacion, error: {e}")
                    location = None
                #Opening Date:
                try:
                    opening_date = clean(job['MatchedObjectDescriptor']['PublicationChannel'][0]['StartDate'])
                except Exception as e:
                    print(f"no se pudo obtener la fecha de apertura, error: {e}")
                #Closing Date
                closing_date = clean(job['MatchedObjectDescriptor']['PublicationEndDate'])
                
                #find the body of the job and look for the words_to_look to appear once at least
                is_alert = False
                #recolecta 3 divs que contienen el texto de la oportunidad
                l1 = detail_page.xpath('(//div[@class="panel-body"])[1]/descendant::text()')
                l2 = detail_page.xpath('(//div[@class="panel-body"])[2]/descendant::text()')
                l3 = detail_page.xpath('(//div[@class="panel-body"])[3]/descendant::text()')

                #une los 3 divs en un solo string, lo limpia y lo convierte a minusculas
                text_for_alert = re.sub(r'[\n\t\xa0]', '', ' '.join(l1+l2+l3) ).strip().lower()
                if any(word in text_for_alert for word in words_to_look):
                    is_alert = True

                #add the new job to the dataset
                df = df.append({'url_detail_id': detail_url, 'scrapped_day': today,  'title': title, 
                        'opening_date': opening_date, 'closing_date': closing_date,'location': location,
                        'is_alert':is_alert, 'source': source}, ignore_index=True)
                
            except Exception as e:
                print(f"falló obteniendo oportunidad {detail_url} con error: \n {e}")
                continue

        #esto es para evitar hacer más de 30 requests, ya que la pagina nos puede bloquear
        if counter == 30:
            print("30 jobs found, maximum reached, braking.")
            break

    print("Storing the updated dataset...")
    df.to_csv(file_name, index=False, encoding='utf-8', header=True)


def main():
    """
    Esta página funciona con un request principal(que necesita headers y params) 
    que devuelve un json con los links de las oportunidades con casi toda la 
    informacion requerida, se visita cada link de detalle para obtener 
    los campos donde se busca la palabra clave.
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
        ' gesundheit ',
        ' pharmakoökonomie ',
        ' medikamente ',
        ' gesundheitssystem ',
    ]
    
    today = date.today().strftime("%d/%m/%Y")
    source = 'GIZ'
    file_name = '../oportunidades.csv'
    main_url = 'https://api-giz.beesite.de/search/'

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)

    print("\nObteniendo la pagina principal...")
    tree = get_main_page(main_url)
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(tree)


if __name__ == "__main__":
    main()
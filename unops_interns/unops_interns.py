from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
#import action chains
from selenium.webdriver.common.action_chains import ActionChains
import time
#import no such element exception
from selenium.common.exceptions import NoSuchElementException
import requests
from lxml import html
import pandas as pd
from datetime import date
import re
import random

def set_driver():
    global driver
    #set default options to driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1024,768")
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options, executable_path='C:\\chromedriver.exe')


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
        if i=='join':
            text = tree.xpath(xpath)
            text = re.sub(r'[\n\t\xa0â\x80\x93]', '', ' '.join(text)).strip()
            return text
        else:
            text = tree.xpath(xpath)[i]
            text = re.sub(r'[\n\t\xa0â\x80\x93]', '', text).strip()
            return text
    except:
        return None


def find_new_jobs(links):
    """"""
    global df, source, today, words_to_look, file_name

    for i, link in enumerate(links):
        if i>15:
            break
        #get the url of detail
        detail_url = link
        
        #looks if the detail url is already in the dataset
        if df['url_detail_id'][df['url_detail_id']==detail_url].any():
            print('this job is already in the dataset')
            continue

        #if not  exist, get the detail
        else:
            print('nueva oportunidad encontrada')

            detail_page = get_page(detail_url)
            
            #get the title
            title = get_by_xpath_and_clean(detail_page, '//h1/text()')
            
            #get the location (type RFQ)
            location = get_by_xpath_and_clean(detail_page, '//span[text()="Duty station"]/following-sibling::span/text()')
            #Opening Date:
            opening_date = get_by_xpath_and_clean(detail_page, 
                '//span[text()="Application period"]/following-sibling::span/text()').split("to")[0].strip()
            #Closing Date
            closing_date = get_by_xpath_and_clean(detail_page, 
                '//span[text()="Application period"]/following-sibling::span/text()').split("to")[1].strip()
            
            #find the body of the job and look for the words_to_look to appear once at least
            is_alert = False

            #text for search
            text_for_alert = title + get_by_xpath_and_clean(detail_page, 
                '(//span[@class="longTextDescription"])[1]//descendant::text()', i='join')
            if any(word in text_for_alert for word in words_to_look):
                is_alert = True
                
            #add the new job to the dataset
            df = df.append({'url_detail_id': detail_url, 'scrapped_day': today,  'title': title, 
                    'opening_date': opening_date, 'closing_date': closing_date,'location': location,
                    'is_alert': is_alert, 'source': source}, ignore_index=True)

    df.to_csv(file_name, index=False, encoding='utf-8', header=True)


def paginate():
    global driver, main_url
    print(f"entrando a la pagina principal: {main_url}")
    driver.get(main_url)
    rdm = random.randint(3, 6)
    time.sleep(rdm)

    print("buscando el boton de paginacion con scroll")
    footer = driver.find_element(By.XPATH, '//div[@class="footer-nav"]')
    ActionChains(driver).scroll_to_element(footer).perform()

    links = [link.get_attribute('href') for link in 
             driver.find_elements(By.XPATH, '//a[contains(@href,"id")]')]
    while True:
        try:
            print("-----next page-----")
            driver.find_element(By.XPATH, '(//tr)[last()]/td/span/parent::td/following-sibling::td/a').click()

            print("durmiendo 5 segs")
            time.sleep(5)

            links += [link.get_attribute('href') for link in driver.find_elements(By.XPATH, '//a[contains(@href,"id")]')]
                
        except NoSuchElementException:
            print("no hay mas paginas")
            break

    driver.quit()
    return links


def main():
    """
    esta pagina es diferente, hace peticiones muy pesadas, por lo cual obté por usar selenium, 
    primero se hace la paginacion con selenium y luego se hace el requests a cada detalle
    """
    global main_url, df, source, today, words_to_look, file_name, driver
    words_to_look = [
        'salud',
        'farmacoeconomía',
        'medicamentos',
        'health',
        'pharmacoeconomics',
        'medicines',
        'saude',
        'farmacoeconomia',
        'medicamentos',
        ]

    today = date.today().strftime("%d/%m/%Y")
    source = 'unops_interns'
    file_name = '../oportunidades.csv'
    main_url = 'https://jobs.unops.org/Pages/ViewVacancy/InternshipListing.aspx'
    
    print("\nIniciando driver...")
    set_driver()

    print("\nhaciendo paginacion...")
    links = paginate()

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(links)


if __name__ == "__main__":
    main()

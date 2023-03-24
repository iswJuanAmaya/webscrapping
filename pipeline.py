#Script orquestador de la ejecución de los scripts de extracción, transformación y carga de datos.
import os
from datetime import date, timedelta
import time
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, body, sender, recipients, password):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Record the MIME types of both parts - text/plain and text/html.
    part2 = MIMEText(body, 'html')  
    msg.attach(part2)

    smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp_server.login(sender, password)
    smtp_server.sendmail(sender, recipients, msg.as_string())
    smtp_server.quit()


def generate_body(nuevas_alertas):
    html = """
        <html>
        <head></head>
        <body>
            <p>Se encontraron nuevas oportunidades!!::<br><br>
        """

    for index, row in nuevas_alertas.iterrows():
        detail_url = row['url_detail_id'] 
        title = row['title'][0:85] + "..." 
        html += f"""
        <a href="{detail_url}">{title}</a><br>
        """

    html += """
        </p>
        </body>
        </html>
        """
    return html


def generate_df_to_fill_body(df, tipo):
    """"""
    global today_datetime, today
    print("generando html para enviar las alertas por correo")

    if tipo == "diario":
        #selecciona las oportunidades escrapeadas hoy y que tengan alerta
        nuevas_alertas = df[['url_detail_id','title']]\
                            [
                                (df['scrapped_day'] == today) & (df['is_alert'] == True) 
                            ]
        #selecciona las oportunidades escrapeadas hoy
        nuevas_oportunidades = df[['url_detail_id','title']]\
                                [
                                    (df['scrapped_day'] == today)
                                ]
        
        print(f""" {len(nuevas_alertas)} \
            alertas detectadas en {len(nuevas_oportunidades)} oportunidades nuevas """
            )
        
        return nuevas_alertas
    
    elif tipo == "semanal":
        #['22/03/2023','21/03/2023','20/03/2023','19/03/2023','18/03/2023','17/03/2023','16/03/2023']
        fechas_semanales = [
                today_datetime.strftime("%d/%m/%Y"),
                (today_datetime - timedelta(1)).strftime("%d/%m/%Y"), 
                (today_datetime - timedelta(2)).strftime("%d/%m/%Y"),
                (today_datetime - timedelta(3)).strftime("%d/%m/%Y"),
                (today_datetime - timedelta(4)).strftime("%d/%m/%Y"),
                (today_datetime - timedelta(5)).strftime("%d/%m/%Y"),
                (today_datetime - timedelta(6)).strftime("%d/%m/%Y")
            ]
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes y que tengan alerta
        nuevas_alertas = df[['url_detail_id','title']]\
            [
                (df['scrapped_day'].isin(fechas_semanales)) & (df['is_alert'] == True)
            ]
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes 
        nuevas_oportunidades = df[['url_detail_id','title']]\
                                [
                                    (df['scrapped_day'].isin(fechas_semanales)) 
                                ]
        
        print(f""" {len(nuevas_alertas)} \
            alertas detectadas en {len(nuevas_oportunidades)} oportunidades nuevas """
            )
        
        return nuevas_alertas
    
    elif tipo == "lunes":
        #['20/03/2023', '19/03/2023', '18/03/2023']
        sab_dom_lun = [
                today_datetime.strftime("%d/%m/%Y"),
                (today_datetime - timedelta(1)).strftime("%d/%m/%Y"), 
                (today_datetime - timedelta(2)).strftime("%d/%m/%Y") 
            ]
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes y que tengan alerta
        nuevas_alertas = df[['url_detail_id','title']]\
            [
                (df['scrapped_day'].isin(sab_dom_lun)) & (df['is_alert'] == True)
            ]
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes 
        nuevas_oportunidades = df[['url_detail_id','title']]\
                                [
                                    (df['scrapped_day'].isin(sab_dom_lun)) 
                                ]
        print(f""" {len(nuevas_alertas)} \
            alertas detectadas en {len(nuevas_oportunidades)} oportunidades nuevas """
            )
        
        return nuevas_alertas


def correr_scrapers():
    """"""
    global folders
    for folder, script in folders.items():
        print(f"///////////////++++++++++++++++++++++ entrando a {folder} ++++++++++++++++++++++////////////////")
        os.chdir(folder)

        print(f"///////////////++++++++++++++++++++++ ejecutando {script} ++++++++++++++++++++++////////////////")
        os.system(f"python {script}")

        print(f"--------------------------volviendo a la carpeta raiz--------------------------------\n \n")
        os.chdir("..")  

        time.sleep(10)

    print("///////////////////////++++++++++++++++++++++ FIN DE LA EJECUCION DE LOS SCRAPPERS ++++++++++++++++++++++////////////////")


def main():
    """
    Script orquestador de la ejecución de los scripts de extracción, transformación y carga de datos.

    1) Itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, ejecuta el script y vuelve a la carpeta raiz

    2)corre el script de generacion y envio de alertas
    """
    global sender, recipients, password, today, today_datetime, folders
    sender = "garciaamayajuancristobal.soft@gmail.com"
    recipients = ["iswjuanamaya@gmail.com"]
    password = "bfqqofvsrmtefbbo"
    today_datetime = date.today()
    today = date.today().strftime("%d/%m/%Y")
    folders = {
        "giz":"giz.py",
        "idb":"idb.py",
        "oecd":"oecd.py",
        "paho":"paho.py",
        "ungm":"ungm.py"
        # "unops":"unops.py",
        # "unops_interns":"unops_interns.py"
        # "wbg":"wbg.py",
        }
    
    #--// Corre todos los scrapers //--#
    # 1) itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, ejecuta el script y vuelve a la carpeta raiz
    correr_scrapers()

    #--// Empieza el algoritmo de generacion de alertas y envió de correos //--#
    # 2) corre el script de generacion y envio de alertas
    print("--------->>>>>>>>>>> Algoritmo de generacion de alertas......")

    #lee las oportunidades guardadas
    print("leyendo oportunidades guardadas")
    df = pd.read_csv('oportunidades.csv', encoding='utf-8')

    #martes, miercoles, jueves y viernes
    if today_datetime.weekday() in [1,2,3,4]:

        print("Generando dataFrame con las alertas diarias")
        nuevas_alertas = generate_df_to_fill_body(df, "diario")

        cant_alertas = len(nuevas_alertas)
        if cant_alertas > 0:
            print(f"enviando {cant_alertas} alertas")
            body_html = generate_body(nuevas_alertas)
            subject = f"{cant_alertas} Nuevas oportunidades"
            send_email(subject, body_html, sender, recipients, password)

        else:
            print("no hay alertas el día de hoy")

        #Jueves
        if today_datetime.weekday() == 3:
            print("----Jueves----")
            print("Generando dataFrame con las alertas de esta semana")
            nuevas_alertas = generate_df_to_fill_body(df, "semanal")

            cant_alertas = len(nuevas_alertas)
            if cant_alertas > 0:
                print(f"enviando {cant_alertas} alertas")
                body_html_sem = generate_body(nuevas_alertas)
                subject = "Resumen de oportunidades semanal"
                send_email(subject, body_html_sem, sender, recipients, password)

            else:
                print("no hay alertas el día de hoy")
            

    #lunes
    elif today_datetime.weekday() == 0:
        print("Generando dataFrame con las alertas del sabado, domingo y lunes")
        nuevas_alertas = generate_df_to_fill_body(df, "lunes")
        
        cant_alertas = len(nuevas_alertas)
        if cant_alertas > 0:
            print(f"enviando {cant_alertas} alertas")
            body_html = generate_body(nuevas_alertas)
            subject = f"{cant_alertas} nuevas oportunidades"
            send_email(subject, body_html, sender, recipients, password)

        else:
            print("no hay alertas")


    # fin de semana no se envian alertas
    elif today_datetime.weekday() in [5,6]:
        print("--> Hoy es fin de semana, no se envian alertas")


if __name__ == "__main__":
    main()
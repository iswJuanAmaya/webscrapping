import os
from datetime import date, timedelta
import time
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, body, sender, recipients, password):
    """Envía un correo electrónico con el cuerpo y el asunto especificados. """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = 'dss.tisalud@gmail.com'
    msg['Cco'] = 'iswjuanamaya@gmail.com,gustavo.gilramos@gmail.com'

    # añade @body como el cuerpo del correo, con el html renderizado.
    part2 = MIMEText(body, 'html')  
    msg.attach(part2)

    smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp_server.login(sender, password)
    smtp_server.sendmail(sender, recipients, msg.as_string())
    smtp_server.quit()


def generate_body(nuevas_alertas:pd.DataFrame, msg:str)->str:
    """ recibe un dataframe filtrado con las alertas correspondientes,
    las itera y construlle un html con las alertas que servirá 
    como cuerpo del correo. eg:

    <html>
    <head></head>
        <body>
            <h1>Se encontraron nuevas oportunidades!</h1><br><br>
                <h2>UNGM</h2>
                1. <a href="{detail_url}">{title}</a><br>
                Deadline: {date}<br>
                Fecha de publicacion: {date}<br><br>

                2. <a href="{detail_url}">{title}</a><br>
                Deadline: {date}<br>
                Fecha de publicacion: {date}<br><br>

                <h2>UNOPS</h2>
                1. <a href="{detail_url}">{title}</a><br>
                Deadline: {date}<br>
                Fecha de publicacion: {date}<br><br>

                2. <a href="{detail_url}">consulting expert to luxemburg</a><br>
                Deadline: 2018-01-01<br>
                Fecha de publicacion: 2018-01-01<br><br>
        </body>
    </html>
    """

    organizaciones = {
        'IDB':'Banco Interamericano de Desarrollo',
        'GIZ':'GIZ',
        'wbg':'World Bank',
        'PAHO':'PAHO',
        'OECD':'OECD u OCDE',
        'unops':'UNOPS',
        'ungm':'Naciones Unidas'
    }

    html = f"""
    <html>
    <head></head>
    <body>
        <h2>{msg}</h2>
    """

    #itera sobre cada grupo de organizaciones
    for group_name, df_group in nuevas_alertas.groupby('source'):
        # forma el titulo del grupo
        html += f"<h3>{organizaciones[group_name]}</h3>"
        #contador por grupo para enumerar las oportunidades por subgrupo
        i = 1

        #itera sobre cada subgrupo de organizaciones
        for row_index, row in df_group.iterrows():
            detail_url = row['url_detail_id'] 
            title = row['title'][0:85] + "..." 
            location = row['location'] if row['location'] else False
            op_date = row['opening_date']
            cl_date = row['closing_date']

            #forma el titulo de esa oportunidad, un elemento a con el titulo que redirecciona a la url de detalle
            html += f"{i}. <a href='{detail_url}'>{title}</a><br>"
            
            #agrega la informacion de la oportunidad si existe
            html += f"Deadline: {cl_date}<br>" if cl_date else ""
            html += f"Fecha de publicacion: {op_date}<br>" if op_date else ""
            html += f"Ubicación: {location}<br><br>" if location else "<br><br>"

            i+=1

    html += """
        </p>
        </body>
        </html>
        """
    
    return html


def generate_df_to_fill_body(df:pd.DataFrame, tipo:str) -> pd.DataFrame:
    """
    Receive a dataframe with all the opportunities scrapped and 
    return a dataframe with the opportunities with alert depending on the type 
    of alert 
    daily: opportunities scrapped today; tuesday, wednesday, thursday, friday
    weekly: it will be sent on thursday
    monday: it will be contain opportunities scrapped on monday, sunday and saturday
    """
    global today_datetime, today
    print("generando html para enviar las alertas por correo")

    if tipo == "diario":
        #selecciona las oportunidades escrapeadas hoy y que tengan alerta
        nuevas_alertas = df[['url_detail_id','title','source','location','opening_date','closing_date']]\
                            [
                                (df['scrapped_day'] == today) & (df['is_alert'] == True) 
                            ]
        
        #selecciona las oportunidades escrapeadas hoy
        nuevas_oportunidades = df[['url_detail_id','title']]\
                                [
                                    (df['scrapped_day'] == today)
                                ]
        
        msg = f""" {len(nuevas_alertas)} \
            alertas detectadas en {len(nuevas_oportunidades)} oportunidades minadas"""
            
        print(msg)
        return nuevas_alertas, msg
    
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
        nuevas_alertas = df[['url_detail_id','title','source','location','opening_date','closing_date']]\
            [
                (df['scrapped_day'].isin(fechas_semanales)) & (df['is_alert'] == True)
            ]
        
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes 
        nuevas_oportunidades = df[['url_detail_id','title']]\
                                [
                                    (df['scrapped_day'].isin(fechas_semanales)) 
                                ]
        
        msg = f""" {len(nuevas_alertas)} \
            alertas detectadas en {len(nuevas_oportunidades)} oportunidades minadas"""
            
        print(msg)
        
        return nuevas_alertas, msg
    
    elif tipo == "lunes":

        #['20/03/2023', '19/03/2023', '18/03/2023']
        sab_dom_lun = [
                today_datetime.strftime("%d/%m/%Y"),
                (today_datetime - timedelta(1)).strftime("%d/%m/%Y"), 
                (today_datetime - timedelta(2)).strftime("%d/%m/%Y") 
            ]
        
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes y que tengan alerta
        nuevas_alertas = df[['url_detail_id','title','source','location','opening_date','closing_date']]\
            [
                (df['scrapped_day'].isin(sab_dom_lun)) & (df['is_alert'] == True)
            ]
        
        #selecciona las oportunidades escrapeadas sabado, domingo y lunes 
        nuevas_oportunidades = df[['url_detail_id','title']]\
                                [
                                    (df['scrapped_day'].isin(sab_dom_lun)) 
                                ]
        
        msg = f""" {len(nuevas_alertas)} \
            alertas detectadas en {len(nuevas_oportunidades)} oportunidades minadas"""
            
        print(msg)
        
        return nuevas_alertas, msg


def correr_scrapers():
    """iterates over folder and run the scrapers scripts"""
    global folders
    for folder, script in folders.items():

        print(f"///////////////++++++++++++++++++++++ ejecutando {script} ++++++++++++++++++++++////////////////")
        os.chdir(folder)
        os.system(f"python {script}")
        os.chdir("..")  

        time.sleep(10)

    print("///////////////////////++++++++++++++++++++++ FIN DE LA EJECUCION DE LOS SCRAPPERS ++++++++++++++++++++++////////////////")


def main():
    """
    Script orquestador de la ejecución de los scripts de extracción, transformación y carga de datos.

    1) Itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, 
    ejecuta el script y vuelve a la carpeta raiz

    2) Lee el archivo de alertas y lo convierte en un dataframe con las alertas correspondientes, 
    al final envia el correo y si hay alertas
    
    """
    global sender, recipients, password, today, today_datetime, folders
    sender = "alquimiadigital23@gmail.com"
    recipients = ["iswjuanamaya@gmail.com", "gustavo.gilramos@gmail.com", "dss.tisalud@gmail.com"]#
    password = "pyfiewjrnjmqtrnl" 
    today_datetime = date.today()
    today = date.today().strftime("%d/%m/%Y")
    folders = {
        "giz":"giz.py",
        "idb":"idb.py",
        "oecd":"oecd.py",
        "paho":"paho.py",
        "ungm":"ungm.py",
        "unops":"unops.py",
        "unops_interns":"unops_interns.py",
        "wbg":"wbg.py"
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
        nuevas_alertas, msg = generate_df_to_fill_body(df, "diario")

        cant_alertas = len(nuevas_alertas)
        if cant_alertas > 0:
            print(f"enviando {cant_alertas} alertas")
            body_html = generate_body(nuevas_alertas, msg)
            subject = f"{cant_alertas} Nuevas oportunidades"
            send_email(subject, body_html, sender, recipients, password)

        else:
            print("no hay alertas el día de hoy")

        #Jueves
        if today_datetime.weekday() == 3:
            print("----Jueves----")
            print("Generando dataFrame con las alertas de esta semana")
            nuevas_alertas, msg = generate_df_to_fill_body(df, "semanal")

            cant_alertas = len(nuevas_alertas)
            if cant_alertas > 0:
                print(f"enviando {cant_alertas} alertas")
                body_html_sem = generate_body(nuevas_alertas, msg)
                subject = "Resumen de oportunidades semanal"
                send_email(subject, body_html_sem, sender, recipients, password)

            else:
                print("no hay alertas el día de hoy")
            

    #lunes
    elif today_datetime.weekday() == 0:
        print("Generando dataFrame con las alertas del sabado, domingo y lunes")
        nuevas_alertas, msg = generate_df_to_fill_body(df, "lunes")
        
        cant_alertas = len(nuevas_alertas)
        if cant_alertas > 0:
            print(f"enviando {cant_alertas} alertas")
            body_html = generate_body(nuevas_alertas, msg)
            subject = f"{cant_alertas} nuevas oportunidades"
            send_email(subject, body_html, sender, recipients, password)

        else:
            print("no hay alertas")


    # fin de semana no se envian alertas
    elif today_datetime.weekday() in [5,6]:
        print("--> Hoy es fin de semana, no se envian alertas")


if __name__ == "__main__":
    main()
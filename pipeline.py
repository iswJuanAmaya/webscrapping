#imports
import os
import time, timedelta
"""
Script orquestador de la ejecución de los scripts de extracción, transformación y carga de datos.

1) Itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, ejecuta el script y vuelve a la carpeta raiz

2)corre el script de generacion y envio de alertas
"""

today = date.today()

folders = {
    "giz":"giz.py",
    "idb":"idb.py",
    "oecd":"oecd.py",
    "paho":"paho.py",
    "ungm":"ungm.py",
    "unops":"unops.py",
    "unops_interns":"unops_interns.py"
    # "wbg":"wbg.py",
    }


# 1) itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, ejecuta el script y vuelve a la carpeta raiz
for folder, script in folders.items():
    print(f"///////////////++++++++++++++++++++++ entrando a {folder} ++++++++++++++++++++++////////////////")
    os.chdir(folder)

    print(f"///////////////++++++++++++++++++++++ ejecutando {script} ++++++++++++++++++++++////////////////")
    os.system(f"python {script}")

    print(f"--------------------------volviendo a la carpeta raiz--------------------------------\n \n")
    os.chdir("..")  

    time.sleep(10)


# 2) corre el script de generacion y envio de alertas

if today.weekday() == 0:
    print("--------->>>>>>>>>>> Lunes se envian alertas de sabado, domingo y lunes")

    #['20/03/2023', '19/03/2023', '18/03/2023']
    sab_dom_lun = [
            today.strftime("%d/%m/%Y"),
            (today - timedelta(1)).strftime("%d/%m/%Y"), 
            (today - timedelta(2)).strftime("%d/%m/%Y") 
        ]
    
# fin de semana no se envian alertas
elif today.weekday() in [5,6]:
    print("--------->>>>>>>>>>> Hoy es fin de semana, no se envian alertas")

else:
    print("--------->>>>>>>>>>> Enviando alertas......")
    #os.system("python alerts.py")
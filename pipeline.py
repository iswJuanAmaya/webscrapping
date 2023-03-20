#imports
import os
"""
Script orquestador de la ejecución de los scripts de extracción, transformación y carga de datos.

1) Itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, ejecuta el script y vuelve a la carpeta raiz

2)corre el script de generacion y envio de alertas
"""

folders = {
    "giz":"giz.py",
    "idb":"idb.py",
    "oecd":"oecd.py",
    "paho":"paho.py",
    "ungm":"ungm.py",
    "unops":"unops.py",
    "unops_interns":"unops_interns.py",
    "wbg":"wbg.py",
}
# itera sobre el diccionario folders, toma la llave como la carpeta, se mueve a ella, ejecuta el script y vuelve a la carpeta raiz
for folder, script in folders.items():
    os.chdir(folder)
    os.system(f"python {script}")
    os.chdir("..")  

# corre el script de generacion y envio de alertas
os.system("python alerts.py")
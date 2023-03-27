##JC 27/03/23 -----  ------
8 scrappers de 8 paginas, cada uno con su propio script, funcionan via requests excepto unops que usa selenium,
cada scrapper lee la bdd para evitar agregar oportunidades repetidas, luego busca keywords en cierta parte
especifica de la página, si encuentra algún match lo marca como alerta, independietemente de esto lo guarda en la bdd.

Todos los scrappers apuntan a la misma base de datos oportunidades.csv, el script orquestador pipeline.py 
ejecuta todos los scrappers, luego detecta que dia de la semana es y en base a eso genera las alertas y 
las envia por correo.


/giz
    giz.py
        Script para descargar los datos de la página
    giz_ops.csv
        base de datos de prueba
    prueba.ipynb
        notebooks de prueba para primera aproximación de desarrollo del scraper
/idb
    giz.py
/oecd
    giz.py
/paho
    paho.py
/ungm
    giz.py
/unops
    giz.py
/unops_interns
    giz.py
/wbg
    giz.py

pipeline.py
    Script orquestador, ejecuta los scripts de cada fuente de datos(los de arriva),
    luego detecta que día de la semana es y en base a eso genera las alertas 
    y las envía por correo

oportunidades.csv
    basede datos de oportunidades, todos los scrappers apuntan a ella.

requirements.txt
    requerimientos para ejecutar el script, requiere esas librerías además se requiere tener chrome instalado la misma version 
    de chromedriver.
# Dates should be in the format yyyy/mm/dd

# if empty or none, will start from the earliest document
START_DATE = "2021/01/01"

# if empty or none, will scrape upto the latest document
END_DATE = None

# the directory where pdfs will be stored
DIR_TO_STORE_PDF = "pdfs"

# Mongo DB configuration

DB_HOST = "localhost"
DB_NAME = "myDB"
COLLECTION_NAME = "myCollection"


OUTPUT_JSON_TEMPLATE = {
 "actor" : "",
 "demandado" : "",  
 "entidad" : "CIUDAD DE MEXICO", 
 "expediente" : "",
 "fecha" : "",
 "fuero" : "FEDERAL", 
 "juzgado": "",
 "tipo" : " LABORAL ",
 "acuerdos" : "", 
 "monto": "",
 "fecha_presentacion": "",
 "actos_reclamados": "",
 "actos_reclamados_especificos": "",
 "naturaleza_procedimiento": "",
 "prestación_demandada": "",
 "organo_jurisdiccional_origen": "",  
 "expediente_origen": "",
 "materia": " LABORAL ", 
 "submateria": "",
 "fecha_sentencia": "",
 "sentido_sentencia": "",
 "resoluciones": "",
 "origen": " JUNTA FEDERAL DE CONCILIACION Y ARBITRAJE ",
 "fecha_insercion": "",
 "fecha_tecnica": "" }
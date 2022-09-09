from includes.PDFDownloader import PDFDownloader
from includes.PDFParser import PDFParser
from config import *
import time
import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


while True:
    logging.info("Downloading PDFs from https://www.gob.mx/jfca")
    downloader = PDFDownloader(DIR_TO_STORE_PDF, START_DATE, END_DATE)
    downloader.start_download()
    logging.info("PDFs download done. Starting the parsing now")
    parser = PDFParser(DIR_TO_STORE_PDF, START_DATE, END_DATE)
    parser.start_parse(skip_already_done=True)
    logging.info("All data parsed and saved to DB.")
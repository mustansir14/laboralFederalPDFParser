import requests
from bs4 import BeautifulSoup
from pathlib import Path
from config import *
from datetime import datetime
import logging
import os
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


class PDFDownloader:

    def __init__(self, dir_to_store="pdfs", start_date=None, end_date=None):

        self.dir_to_store = dir_to_store
        Path(dir_to_store).mkdir(parents=True, exist_ok=True)
        if start_date:
            self.start_date = datetime.strptime(start_date, "%Y/%m/%d")
        else:
            self.start_date = None
        if end_date:
            self.end_date = datetime.strptime(end_date, "%Y/%m/%d")
        else:
            self.end_date = None

    def start_download(self):

        page = 1

        while True:

            logging.info("Scraping Page " + str(page))
            if page == 1:
                res = requests.get("https://www.gob.mx/jfca/es/archivo/documentos?filter_id=4612&filter_origin=archive")
            else:
                res = requests.get("https://www.gob.mx/jfca/es/archivo/documentos?filter_id=4612&filter_origin=archive&idiom=es&page=" + str(page))
            res_text = res.text
            if "$('#prensa').append" in res_text:
                res_text = res_text.replace("$('#prensa').append('", "").replace("\\", "").replace("');", "")
            soup = BeautifulSoup(res_text, "html.parser")
            articles = soup.find_all("article")
            if len(articles) == 0:
                break
            for article in articles:
                if "Boletín Laboral" not in article.text:
                    continue
                article_date = article.time["date"].strip("\"\\").split()[0]
                if not self.is_within_range(article_date):
                    continue
                logging.info("Scraping %s" % article.h2.text)
                url = article.a["href"]
                if "https://www.gob.mx" not in url:
                    url = "https://www.gob.mx" + url
                res = requests.get(url)
                soup = BeautifulSoup(res.content, "html.parser")
                documents = soup.find_all("li", "documents")
                for document in documents:
                    pdf_url = document.a['href']
                    if "https://www.gob.mx" not in pdf_url:
                        pdf_url = "https://www.gob.mx" + pdf_url
                    doc_name = document.div.text.strip()
                    download_path = self.dir_to_store.rstrip() + "/" + article_date.replace("-", "_") + "_" + doc_name.replace(" ", "_").replace(",", "") + ".pdf"
                    if os.path.isfile(download_path):
                        logging.info("PDF %s already downloaded. Skipping" % doc_name)
                        continue
                    logging.info("Downloading PDF %s to %s" % (doc_name, download_path))
                    res = requests.get(pdf_url)
                    with open(download_path, "wb") as f:
                        f.write(res.content)
            page += 1


    def is_within_range(self, date, date_format="%Y-%m-%d"):

        date = datetime.strptime(date, date_format)
        if self.start_date and self.end_date:
            return date >= self.start_date and date <= self.end_date
        if self.start_date:
            return date >= self.start_date
        if self.end_date:
            return date <= self.end_date
        return True




if __name__ == "__main__":

    scraper = PDFDownloader(start_date=START_DATE, end_date=END_DATE)
    scraper.start_download()

from pdf2image import convert_from_path
import pytesseract
import cv2
from datetime import date, datetime
from glob import glob
import numpy as np
import json
import logging
from includes.DB import DB
import re
import unidecode
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)

from config import *

class PDFParser:

    def __init__(self, pdf_dir="pdfs", start_date=None, end_date=None):

        self.pdf_dir = pdf_dir.rstrip("/")
        if start_date:
            self.start_date = datetime.strptime(start_date, "%Y/%m/%d")
        else:
            self.start_date = None
        if end_date:
            self.end_date = datetime.strptime(end_date, "%Y/%m/%d")
        else:
            self.end_date = None
        self.db = DB(DB_HOST, DB_NAME, COLLECTION_NAME, DB_USER, DB_PASS)

    def start_parse(self, skip_already_done=False):

        pdfs = glob(self.pdf_dir + "/*.pdf")
        for pdf in pdfs:
            pdf = pdf.replace("\\", "/")
            date = datetime.strptime(pdf.split("/")[-1][:10], "%Y_%m_%d")
            if self.start_date and self.end_date:
                if not (date >= self.start_date and date <= self.end_date):
                    continue
            elif self.start_date:
                if date < self.start_date:
                    continue
            elif self.end_date:
                if date > self.end_date:
                    continue
            pdf_name = pdf.split("/")[-1]
            if skip_already_done and self.db.check_pdf(pdf_name):
                logging.info("PDF " + pdf_name + " already parsed and saved to DB. Skipping")
                continue
            logging.info("Parsing PDF: " + pdf_name)
            result = self.parse_pdf(pdf)
            try:
                self.db.insert(result)
                self.db.insert_pdf(pdf_name)
                logging.info("Data saved to DB successfully!")
            except Exception as e:
                logging.error("Error in saving to DB: " + str(e))

    
    def parse_pdf(self, pdf_path):

        pages = convert_from_path(pdf_path, 200)
        results = []
        juzgado = None
        organo_jurisdiccional_origen = None
        in_record = False
        file_name = pdf_path.strip("/").split("/")[-1]
        fecha = file_name[:8].replace("_", "/")
        day = file_name.split("_")[5]
        if len(day) == 1:
            day = "0" + day
        fecha += day
        actor = ""
        demandado = ""
        acuerdos = ""
        expediente = ""
        expediente_origen = ""
        total_sections = []
        for i, page in enumerate(pages):
            logging.info("Parsing Page %s" % str(i+1))
            opencvImage = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            img1, img2 = PDFParser.transform_image(opencvImage)

            # convert the image to black and white for better OCR
            ret,thresh = cv2.threshold(img1,120,255,cv2.THRESH_BINARY)
            text = str(pytesseract.image_to_string(thresh, config='--psm 6', lang="spa")).strip()
            ret,thresh = cv2.threshold(img2,120,255,cv2.THRESH_BINARY)
            text2 = str(pytesseract.image_to_string(thresh, config='--psm 6', lang="spa")).strip()
            if text2 and text2[0].isnumeric():
                text += "\n\n" + text2
            else:
                text += "\n" + text2


            new_text = ""
            text_len = len(text)
            for k in range(text_len):
                new_text += text[k]
                if text[k] == "\n" and k != 0 and text[k-1] != "\n" and k < (text_len - 1) and text[k+1].isnumeric() and (k >= (text_len - 4) or text[k+2] == "." or text[k+3] == "." or (text[k+2] == " " and text[k+3].isnumeric()) or ((text[k+3] == " " and text[k+4].isnumeric()))):
                    new_text += "\n"
            sections = new_text.split("\n\n")
            total_sections += sections
            
        j = 0
        while j < len(total_sections):
            try:
                section = total_sections[j].strip().upper()
                no_of_lines = len(section.split("\n"))
                if no_of_lines == 1:
                    if section.strip().startswith("JUNTA ESPECIAL N"):
                        organo_jurisdiccional_origen = unidecode.unidecode(section)
                    elif section.strip().startswith("SECRETARIA") or section.strip().startswith("SECRETARÍA"):
                        juzgado = unidecode.unidecode(section)
                if organo_jurisdiccional_origen and section[0].isnumeric():
                    for _ in range(50):
                        j += 1
                        if j >= len(total_sections) or total_sections[j][0].isnumeric() or total_sections[j].upper().strip().startswith("JUNTA ESPECIAL") or total_sections[j].upper().strip().startswith("SECRETARI") or total_sections[j].upper().strip().startswith("REPRESENTANTE"):
                            j -= 1
                            break
                        section += "\n\n" + total_sections[j].strip().upper()
                    
                    section = section.replace("Ñ", "**specialN**")
                    section = unidecode.unidecode(section)
                    section = section.replace("**specialN**", "Ñ")
                    
                    if "/" not in section.split(' ')[0]:
                        section = " ".join(section.split(' ')[1:])

                    if section.strip() == "":
                        j += 1
                        continue

                    if "VS" not in section:
                        if " VS " not in section and " YS " in section:
                            section = section.replace(" YS ", " VS ")
                        elif "VS " not in section and "YS " in section:
                            section = section.replace("YS ", "VS ")
                        elif " VS" not in section and " YS" in section:
                            section = section.replace(" YS", " VS")
                        if " VS " not in section and " 1S " in section:
                            section = section.replace(" 1S ", " VS ")
                        elif "VS " not in section and "1S " in section:
                            section = section.replace("1S ", "VS ")
                        elif " VS" not in section and " 1S" in section:
                            section = section.replace(" 1S", " VS")

                    paras = section.split("\n\n")
                    
                    if len(paras) > 1 and "AMPARO" in paras[0]:
                        dot_split = [x for x in paras[0].replace(",", ".").split(".") if x.strip()]
                        expediente = dot_split[0].replace(",", ".")
                        if len(dot_split) > 1:
                            expediente = dot_split[1].strip()
                            expediente_origen = dot_split[0].strip()
                            if len(paras) > 1:
                                vs_split = paras[1].split("VS")
                            else:
                                vs_split = paras[0].split("VS")
                            actor = vs_split[0].strip().replace("\n", " ")
                            if len(vs_split) > 1:
                                demandado = vs_split[1].strip().replace("\n", " ")
                            if len(paras) > 2:
                                acuerdos = "\n".join(paras[2:]).strip()

                    elif len(paras) >= 4:
                        dot_split = [x for x in paras[0].split(".") if x.strip()]
                        expediente = dot_split[0]                            
                        vs_split = ".".join(dot_split[1:]).split("VS")
                        actor = vs_split[0].strip().replace("\n", " ")
                        if len(vs_split) > 1:
                            demandado = vs_split[1].strip().replace("\n", " ")
                        acuerdos = " ".join(paras[1:])

                    else:
                        vs_split = section.split("VS")
                        dot_split = [x for x in vs_split[0].split(".") if x.strip()]
                        if len(dot_split) == 1:
                            first_word = vs_split[0].split()[0]
                            if "/" in first_word:
                                dot_split = [first_word] + [" ".join(vs_split[0].split()[1:])]
                            else:
                                dot_split = [vs_split[0].split("\n")[0]] + ["\n".join(vs_split[0].split('\n')[1:])] 
                        expediente = dot_split[0].strip()
                        if "IV" in expediente:
                            actor = ".".join(dot_split[1:]).replace("\n", " ").strip()
                        elif len(dot_split) > 2:
                            acuerdos = ".".join(dot_split[1:-1]).replace("\n", " ").strip()
                            actor = dot_split[-1].replace("\n", " ").strip()
                        elif len(dot_split) > 1:
                            actor = dot_split[1].replace("\n", " ").strip()
                        if len(vs_split) > 1:
                            demandado = vs_split[1].strip().replace("\n", " ")
                            if ";" in vs_split[1]:
                                semi_split = vs_split[1].split(";")
                                demandado = semi_split[0].replace("\n", " ").strip()
                                acuerdos = semi_split[1].replace("\n", " ").strip()
                        match = re.search(r'(\d+/\d+/\d+)', paras[0])
                        if match:
                            expediente = paras[0].strip().split(" ")[0]
                            rest_text = vs_split[0].split(expediente)[1].strip()
                            date_split = rest_text.split(match.group(1))
                            acuerdos = date_split[0] + match.group(1).replace("\n", " ").strip()
                            actor = date_split[1].replace("\n", " ").strip()
                            if len(vs_split) > 1:
                                demandado = vs_split[1].replace("\n", " ").strip()
                            
                if demandado or actor:
                    result = OUTPUT_JSON_TEMPLATE.copy()
                    result["fecha"] = fecha
                    result["actor"] = actor.lstrip(".").strip().replace("\n", " ")
                    result["demandado"] = demandado.lstrip(".").strip().replace("\n", " ")
                    if juzgado:
                        result["organo_jurisdiccional_origen"] = organo_jurisdiccional_origen.lstrip(".").strip().replace("\n", " ")
                        result["juzgado"] = juzgado.lstrip(".").strip().replace("\n", " ")
                    else:
                        result["juzgado"] = organo_jurisdiccional_origen.lstrip(".").strip().replace("\n", " ")
                    if "," in expediente:
                        acuerdos = expediente.split(",")[1] + acuerdos
                        expediente = expediente.split(",")[0]
                    result["acuerdos"] = acuerdos.lstrip(".").strip().replace("\n", " ")
                    result["expediente"] = expediente.lstrip(".").strip().replace("\n", " ")
                    result["expediente_origen"] = expediente_origen.lstrip(".").strip().replace("\n", " ")
                    result["fecha_insercion"] = datetime.now().isoformat()
                    result["fecha_tecnica"] = datetime.strptime(fecha, "%Y/%m/%d").isoformat()
                    results.append(result)
                    actor = demandado = acuerdos = expediente = expediente_origen = ""
                
                j += 1
            except Exception as e:
                print(e)
                print(section)
                break
        return results


    def transform_image(img):

            # img = cv2.imread(image_path)
            height = img.shape[0]
            width = img.shape[1]

            pixels_to_remove = int(height*0.07)
            img = img[pixels_to_remove:-pixels_to_remove, :]
            # Cut the image in half
            width_cutoff = width // 2
            s1 = img[:, :width_cutoff]
            s2 = img[:, width_cutoff:]
            return s1, s2

if __name__ == "__main__":
    parser = PDFParser()
    parser.start_parse(skip_already_done=True)

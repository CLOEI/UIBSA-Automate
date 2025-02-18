import requests
import base64
import json
import os
import sys
import logging

from category import kdko, klydu, ksdpm, pacdpb, pddp, pdppapkm, pi, sedk
from pdf2image import convert_from_path
from anthropic import Anthropic
from io import BytesIO
from thefuzz import process

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
format_output = logging.Formatter('%(levelname)s : %(asctime)s : %(message)s')
stdout_handler.setFormatter(format_output)    
logger.addHandler(stdout_handler)

with open("config.json", "r") as f:
    config = json.load(f)

client = Anthropic(
    api_key=config["api_key"],
)

def get_cert_scan_data_result(data):
    logger.info("Scanning certificate")
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=1,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You will be analyzing a description of a certificate image and extracting specific information from it. The image description will be provided to you in the following format:\n"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": data
                        }
                    },
                    {
                        "type": "text",
                        "text": "\nYour task is to extract the following information from the certificate image description:\n\n1. Name of the certificate recipient\n2. Role of the participant\n3. Name of the event or activity\n4. Location where the certificate was given\n5. Date when the certificate was given\n\nAfter extracting this information, you need to categorize the certificate into one of the following categories:\n\n- Pengembangan Diri dan profesionalisme\n- Prestasi/Capaian dan Pengembangan Bakat\n- Kegiatan Sosial dan Pemberdayaan Masyarakat\n- Kepemimpinan dan Kemampuan Organisasi\n- Spiritual,Etika dan Karakter\n- Publikasi dan Proses Penelitian/PkM\n- Program Internasional\n- Kegiatan Lain Yang Diakui Universitas\n\nChoose the category that best fits the certificate based on the information provided in the image description if the event name for a webinar it would be \"Pengembangan Diri dan profesionalisme\"\n\nPresent your findings in a JSON format with the following structure:\n\n{\n  \"recipient_name\": \"\",\n  \"participant_role\": \"\",\n  \"event_name\": \"\",\n  \"location\": \"\",\n  \"date\": \"\",\n  \"category\": \"\"\n}\n\nIf any of the required information is not available in the image description, use \"Not specified\" as the value for that field.\n\nImportant: Base all your extracted information solely on the content provided in the image description. Do not make assumptions or add information that is not explicitly stated in the description."
                    }
                ]
            }
        ]
    )
    return message.content[0].text

def get_category_type_from_image(img_data, data):
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0,
        system=f"Please examine the attached image and locate the word that follows 'sebagai' This word or phrase indicates the role in the certificate.\nExtract the exact word or phrase after 'sebagai.'\nMatch this extracted text precisely with the JSON values provided below. If the text is 'Peserta,' only consider entries that include the exact word 'Peserta' in the value.\nReturn the match in the format id, text without any additional explanation or commentary. Ensure no other role, such as 'Pembicara' or 'Moderator,' is chosen if the extracted text is 'Peserta.'\n{data}\nOnly respond with the exact matching entry in the format id, text",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_data
                        }
                    }
                ]
            }
        ]
    )
    return message.content[0].text

session = requests.Session()
logger.info("Trying to login to UIB sa")
r = session.post("https://sa.uib.ac.id/Login", data={"username": config["username"], "password": config["password"]})
logger.info("Fetching list of certificates")
r = session.post("https://sa.uib.ac.id//PenambahanKegiatan/Kegiatan/GetListKegiatan", data={"search": ""})

try:
    sertifikat_yang_diakui = r.json()
    choices = [x["text"] for x in sertifikat_yang_diakui]
    for filename in os.listdir("certificates"):
        logger.info(f"Processing {filename}")
        pdf_path = os.path.join("certificates", filename)
        image = convert_from_path(pdf_path, poppler_path="./poppler")[0]

        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        cert_data = json.loads(get_cert_scan_data_result(img_str))
        
        name = cert_data["recipient_name"]
        role = cert_data["participant_role"]
        event_name = cert_data["event_name"]
        location = cert_data["location"]
        date = cert_data["date_issued"]
        category = cert_data["category"]

        print(f"Name: {name}")
        print(f"Role: {role}")
        print(f"Event: {event_name}")
        print(f"Location: {location}")
        print(f"Date: {date}")
        print(f"Category: {category}")
        

        break;
        [name, date, category] = get_cert_scan_data_result(img_str).split(",")
        (text, score) = process.extractOne(name, choices)
        certificate_id = [x["id"] for x in sertifikat_yang_diakui if x["text"] == text][0]

        print(f"Name: {name.strip()}")
        print(f"Date: {date.strip()}")
        print(f"Category: {category.strip()}")
        print(f"Certificate ID: {certificate_id}")
        
        cid = None
        data = None

        if category.strip() == "Pengembangan Diri dan profesionalisme":
            cid = pddp.cid
            data = pddp.jenis_kegiatan_options
        elif category.strip() == "Prestasi/Capaian dan Pengembangan Bakat":
            cid = pacdpb.cid
            data = pacdpb.jenis_kegiatan_options
        elif category.strip() == "Kegiatan Sosial dan Pemberdayaan Masyarakat":
            cid = ksdpm.cid
            data = ksdpm.jenis_kegiatan_options
        elif category.strip() == "Kepemimpinan dan Kemampuan Organisasi":
            cid = klydu.cid
            data = klydu.jenis_kegiatan_options
        elif category.strip() == "Spiritual,Etika dan Karakter":
            cid = sedk.cid
            data = sedk.jenis_kegiatan_options
        elif category.strip() == "Publikasi dan Proses Penelitian/PkM":
            cid = pdppapkm.cid
            data = pdppapkm.jenis_kegiatan_options
        elif category.strip() == "Program Internasional":
            cid = pi.cid
            data = pi.jenis_kegiatan_options
        elif category.strip() == "Kegiatan Lain Yang Diakui Universitas":
            cid = kdko.cid
            data = kdko.jenis_kegiatan_options

        if cid:
            [ctid, text] = get_category_type_from_image(img_str, data).split(",")
            print(f"Category Type ID: {ctid} ({text.strip()})")

            data = {
                'idKategori': cid,
                'bankId': certificate_id,
                'jenisKegiatan': ctid,
                'tglKegiatan': date.strip(), 
                'url': '-',
            }

            files = {
                'sertifikat': open(pdf_path, 'rb'),
            }

            r = session.post("https://sa.uib.ac.id/PenambahanKegiatan/Kegiatan/Tambah", data=data, files=files)
            print(r.text)
        else:
            print("Category not found")
except json.JSONDecodeError:
    logger.error("UIB SA Probably down or invalid credentials")

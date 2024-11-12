import requests
import base64
import json
import os

from category import kdko, klydu, ksdpm, pacdpb, pddp, pdppapkm, pi, sedk
from pdf2image import convert_from_path
from anthropic import Anthropic
from io import BytesIO
from thefuzz import process

with open("config.json", "r") as f:
    config = json.load(f)

client = Anthropic(
    api_key=config["api_key"],
)

def get_cert_scan_data_result(data):
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0,
        system="Dengan mengambil sudut pandang mahasiswa yang ingin mengsubmit sertifikasi yang diterimanya ambil data dari foto yang diberikan. Jika itu merupakan webinar berarti itu merupakan pengembangan diri\n\nList kategori :\nPengembangan Diri dan profesionalisme\nPrestasi/Capaian dan Pengembangan Bakat\nKegiatan Sosial dan Pemberdayaan Masyarakat\nKepemimpinan dan Kemampuan Organisasi\nSpiritual,Etika dan Karakter\nPublikasi dan Proses Penelitian/PkM\nProgram Internasional\nKegiatan Lain Yang Diakui Universitas\n\njawab hanya satu dengan format seperti ini pastikan tanggal sesuai dengan format: nama acara, dd/mm/yyyy, nama kategori",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": data
                        }
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
r = session.post("https://sa.uib.ac.id/Login", data={"username": config["username"], "password": config["password"]})
r = session.post("https://sa.uib.ac.id//PenambahanKegiatan/Kegiatan/GetListKegiatan", data={"search": ""})

try:
    sertifikat_yang_diakui = r.json()
    choices = [x["text"] for x in sertifikat_yang_diakui]
    for filename in os.listdir("certificates"):
        pdf_path = os.path.join("certificates", filename)
        image = convert_from_path(pdf_path)[0]

        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
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
    print("Site probably down")

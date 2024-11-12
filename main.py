import requests
import json

from anthropic import Anthropic
from thefuzz import process

with open("config.json", "r") as f:
    config = json.load(f)

client = Anthropic(
    api_key=config["api_key"],
)

session = requests.Session()
r = session.post("https://sa.uib.ac.id/Login", data={"username": config["username"], "password": config["password"]})
r = session.post("https://sa.uib.ac.id//PenambahanKegiatan/Kegiatan/GetListKegiatan", data={"search": ""})

try:
    sertifikat_yang_diakui = r.json()
    choices = [x["text"] for x in sertifikat_yang_diakui]
    (text, score) = process.extractOne("Webinar Kepribadian Series 12: Multicultural Respect", choices)
    certificate_id = [x["id"] for x in sertifikat_yang_diakui if x["text"] == text][0]
    print(certificate_id)
except json.JSONDecodeError:
    print("Site probably down")
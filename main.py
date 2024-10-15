import requests
import json

from anthropic import Anthropic

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
    print(sertifikat_yang_diakui)
except json.JSONDecodeError:
    print("Site probably down")
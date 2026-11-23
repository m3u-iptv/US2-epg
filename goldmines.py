import re, gzip, requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

URL = "https://www.knowledgeskey.com/goldmines-bollywood-today-schedule/"
IST = timezone(timedelta(hours=5, minutes=30))

def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S +0530")

def parse_page(url, date):
    print(f"Fetching {url}")
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    print(f"Status: {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n")
    # Time + Title pattern: 01:06 AM - 03:10 AM / Title
    # Site pe alag-alag style hai, isliye 2 tarike try karenge
    programmes = []
    # Tarika 1: time range wale blocks
    pattern = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)\s*[-–to]+\s*(\d{1,2}:\d{2}\s*[AP]M)\s*\n\s*([A-Za-z0-9 .,'\-!&]+)", re.I)
    for m in pattern.finditer(text):
        start_s, stop_s, title = m.groups()
        title = title.strip()
        if len(title) < 2 or "Goldmines" in title or "Schedule" in title:
            continue
        try:
            st = datetime.strptime(f"{date} {start_s.strip().upper()}", "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
            sp = datetime.strptime(f"{date} {stop_s.strip().upper()}", "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
            if sp <= st: sp += timedelta(days=1)
            programmes.append((st, sp, title))
        except: pass
    # Duplicate hatao, sort karo
    uniq = []
    seen = set()
    for p in sorted(programmes):
        if p not in seen:
            seen.add(p); uniq.append(p)
    return uniq

today = datetime.now(IST).date()
tomorrow = today + timedelta(days=1)

all_progs = []
all_progs += parse_page(URL, str(today))
# Kal ke liye bhi same URL try karo - site kal ka bhi kabhi deta hai
try:
    all_progs += parse_page(URL + "?date=" + str(tomorrow), str(tomorrow))
except: pass

print(f"Total Programmes Mila: {len(all_progs)}")
if not all_progs:
    print("KUCH NAHI MILA - Site ka design badal gaya!")
    # Khali EPG mat banao, purana rakhne ke liye fail karo
    raise SystemExit(1)

tv = ET.Element("tv", {"generator-info-name":"Goldmines-EPG"})
ch = ET.SubElement(tv, "channel", {"id":"Goldmines.Bollywood.in"})
ET.SubElement(ch, "display-name").text = "Goldmines Bollywood"
ET.SubElement(ch, "display-name").text = "Goldmines.Bollywood.in"

ch2 = ET.SubElement(tv, "channel", {"id":"Goldmines.in"})
ET.SubElement(ch2, "display-name").text = "Goldmines"

for st, sp, title in sorted(all_progs):
    p = ET.SubElement(tv, "programme", {"start":fmt(st), "stop":fmt(sp), "channel":"Goldmines.Bollywood.in"})
    ET.SubElement(p, "title", {"lang":"hi"}).text = title
    # Dusri ID ke liye bhi same
    p2 = ET.SubElement(tv, "programme", {"start":fmt(st), "stop":fmt(sp), "channel":"Goldmines.in"})
    ET.SubElement(p2, "title", {"lang":"hi"}).text = title

xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
with gzip.open("goldmines-epg.xml.gz","wb") as f:
    f.write(xml_bytes)
print("Done: goldmines-epg.xml.gz ban gaya!")

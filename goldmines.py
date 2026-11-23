import re, gzip, requests, sys
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

IST = timezone(timedelta(hours=5, minutes=30))

def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S +0530")

def get_day(date_str):
    url = f"https://intvschedule.com/goldmines-schedule-today-tomorrow"
    print(f"Fetching {url}", flush=True)
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    print(f"Status: {r.status_code}", flush=True)
    text = r.text
    # Pattern: 01:06 AM - 03:10 AM ### Main Hoon Bodyguard
    pat = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)\s*###\s*([^\n#]+)", re.I)
    progs = []
    for m in pat.finditer(text):
        try:
            st = datetime.strptime(f"{date_str} {m.group(1).upper()}", "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
            sp = datetime.strptime(f"{date_str} {m.group(2).upper()}", "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
            if sp <= st: sp += timedelta(days=1)
            title = m.group(3).strip()
            if title and title.lower() != "movie":
                progs.append((st, sp, title))
            elif title.lower() == "movie":
                progs.append((st, sp, "Movie"))
        except: pass
    print(f"Found: {len(progs)}", flush=True)
    return progs

today = datetime.now(IST).date()
all_progs = get_day(str(today))
print(f"Total: {len(all_progs)}", flush=True)
if not all_progs:
    print("Phir bhi 0 aaya!")
    sys.exit(1)

tv = ET.Element("tv", {"generator-info-name":"Goldmines-EPG"})
ch = ET.SubElement(tv, "channel", {"id":"Goldmines.in"})
ET.SubElement(ch, "display-name").text = "Goldmines"

for st, sp, title in sorted(all_progs):
    p = ET.SubElement(tv, "programme", {"start":fmt(st), "stop":fmt(sp), "channel":"Goldmines.in"})
    ET.SubElement(p, "title", {"lang":"hi"}).text = title

xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
with gzip.open("goldmines-epg.xml.gz","wb") as f:
    f.write(xml_bytes)
print("Done!")

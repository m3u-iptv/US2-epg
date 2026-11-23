import re, gzip, requests, sys
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

IST = timezone(timedelta(hours=5, minutes=30))
BASE = "https://www.tvwish.com/IN/Channels/goldmines/745/Schedule"

def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S +0530")

def get_day(day_name, date):
    url = f"{BASE}/{day_name}"
    print(f"Fetching {url}", flush=True)
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    print(f"Status: {r.status_code}", flush=True)
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n")
    # TVWish pe time aise hota hai: 01:06 AM - Movie Name
    progs = []
    # Sabse pehle time wale line dhoondo
    pattern = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)\s*(?:-|–|to)?\s*\n\s*([A-Za-z0-9 .,'\-!&()]+)", re.I)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        m = re.match(r"^(\d{1,2}:\d{2}\s*[AP]M)$", line, re.I)
        if m and i+1 < len(lines):
            title = lines[i+1].strip()
            if len(title) < 2 or "Goldmines" in title or "Schedule" in title or "AM" in title.upper() or "PM" in title.upper():
                continue
            try:
                st = datetime.strptime(f"{date} {m.group(1).upper()}", "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
                progs.append((st, title))
            except: pass
    # Stop time = agle programme ka start
    out = []
    progs = sorted(set(progs))
    for idx, (st, title) in enumerate(progs):
        sp = progs[idx+1][0] if idx+1 < len(progs) else st + timedelta(hours=3)
        if sp <= st: sp += timedelta(days=1)
        out.append((st, sp, title))
    print(f"{day_name}: {len(out)} programmes", flush=True)
    return out

today = datetime.now(IST).date()
tomorrow = today + timedelta(days=1)

all_progs = []
all_progs += get_day("Today", str(today))
all_progs += get_day("Tomorrow", str(tomorrow))

print(f"Total: {len(all_progs)}", flush=True)
if not all_progs:
    print("Kuch nahi mila! Site ka design badla?")
    sys.exit(1)

tv = ET.Element("tv", {"generator-info-name":"Goldmines-EPG"})
ch = ET.SubElement(tv, "channel", {"id":"Goldmines.in"})
ET.SubElement(ch, "display-name").text = "Goldmines"
ET.SubElement(ch, "display-name").text = "Goldmines.in"

for st, sp, title in sorted(all_progs):
    p = ET.SubElement(tv, "programme", {"start":fmt(st), "stop":fmt(sp), "channel":"Goldmines.in"})
    ET.SubElement(p, "title", {"lang":"hi"}).text = title

xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
with gzip.open("goldmines-epg.xml.gz","wb") as f:
    f.write(xml_bytes)
print("Done: goldmines-epg.xml.gz ban gaya!")

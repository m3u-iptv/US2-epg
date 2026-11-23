import gzip
import requests
import xml.etree.ElementTree as ET

EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"

# Sirf ye wale chahiye
WANTED = [
    "Aastha.uk","B4U.Movies.uk","B4U.Music.uk","ColorsCineplex.uk",
    "ColorsGujarati.uk","COLORS.HD.uk","ColorsRishtey.uk",
    "SONY.MAX.2.uk","SONY.MAX.HD.uk","SONY.SAB.uk","SONY.TV.HD.uk",
    "Utsav.Bharat.uk","Utsav.Gold.HD.uky","Utsav.GOLD.uk","Utsav.Plus.HD.uk",
    "Zee.Cinema.uk","Zee.TV.HD.uk"
]

def norm(s):
    return s.lower().replace(".","").replace("_","").replace("-","").replace(" ","")

wanted_norm = set(norm(x) for x in WANTED)

print("Downloading EPG...")
r = requests.get(EPG_URL, timeout=60, headers={"User-Agent":"Mozilla/5.0"})
r.raise_for_status()
data = gzip.decompress(r.content)

root = ET.fromstring(data)
tv = ET.Element("tv", {"generator-info-name": "UK-Filter-EPG"})

keep_ids = set()
for ch in root.findall("channel"):
    cid = ch.get("id","")
    names = [cid] + [d.text or "" for d in ch.findall("display-name")]
    if any(norm(n) in wanted_norm for n in names):
        keep_ids.add(cid)
        tv.append(ch)
        print(f"Keep Channel: {cid}")

count = 0
for p in root.findall("programme"):
    if p.get("channel") in keep_ids:
        tv.append(p)
        count += 1

print(f"Total Programmes: {count}")
xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
with gzip.open("epg.xml.gz","wb") as f:
    f.write(xml_bytes)
print("Done: epg.xml.gz ban gaya")

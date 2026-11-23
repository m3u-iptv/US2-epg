import gzip, requests, xml.etree.ElementTree as ET, sys

EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"
WANTED = ["Aastha.uk","B4U.Movies.uk","B4U.Music.uk","ColorsCineplex.uk","ColorsGujarati.uk","COLORS.HD.uk","ColorsRishtey.uk","SONY.MAX.2.uk","SONY.MAX.HD.uk","SONY.SAB.uk","SONY.TV.HD.uk","Utsav.Bharat.uk","Utsav.Gold.HD.uky","Utsav.GOLD.uk","Utsav.Plus.HD.uk","Zee.Cinema.uk","Zee.TV.HD.uk"]
def norm(s): return s.lower().replace(".","").replace("_","").replace("-","").replace(" ","")
wanted_norm = set(norm(x) for x in WANTED)

print("Downloading...", flush=True)
try:
    r = requests.get(EPG_URL, timeout=90, headers={"User-Agent":"Mozilla/5.0","Accept-Encoding":"gzip"})
    print(f"Status: {r.status_code} Size: {len(r.content)}", flush=True)
    if r.status_code != 200:
        print("URL FAIL - EPG Nahi Mila!"); sys.exit(1)
    data = gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
except Exception as e:
    print(f"ERROR: {e}"); sys.exit(1)

root = ET.fromstring(data)
print(f"Total Channels in Source: {len(root.findall('channel'))}")

tv = ET.Element("tv", {"generator-info-name":"UK-Filter-EPG"})
keep_ids=set()
for ch in root.findall("channel"):
    cid=ch.get("id","")
    names=[cid]+[d.text or "" for d in ch.findall("display-name")]
    if any(norm(n) in wanted_norm for n in names):
        keep_ids.add(cid); tv.append(ch); print(f"Keep: {cid}")

c=0
for p in root.findall("programme"):
    if p.get("channel") in keep_ids:
        tv.append(p); c+=1
print(f"Keep Programmes: {c} | Keep Channels: {len(keep_ids)}")
if len(keep_ids)==0:
    print("KOI CHANNEL MATCH NAHI HUA! ID ALAG HAI!")
    # Debug - sab ID print karo
    for ch in root.findall("channel")[:30]:
        print("SOURCE ID:", ch.get("id"))

xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
with gzip.open("epg.xml.gz","wb") as f: f.write(xml_bytes)
print("Done epg.xml.gz")

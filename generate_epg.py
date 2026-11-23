import gzip
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# JioTV API Endpoints
CHANNELS_API = "https://jio.com"
EPG_API = "https://jio.com{}&offset={}"

def fetch_and_build_epg():
    tv = ET.Element("tv", {"generator-info-name": "JioTV-Auto-EPG"})
    
    headers = {
        "User-Agent": "okhttp/4.2.2",
        "appkey": "NzNiMDhlYzQyNjJm",
        "os": "android"
    }

    # 1. चैनल लिस्ट प्राप्त करें
    resp = requests.get(CHANNELS_API, headers=headers).json()
    channels = resp.get("result", [])

    # उदाहरण के लिए पहले 50 चैनल्स (आप इसे सभी चैनल्स के लिए हटा सकते हैं)
    for ch in channels[:50]:
        ch_id = str(ch["channel_id"])
        ch_name = ch["channel_name"]
        logo = f"https://jio.com{ch['logoUrl']}"

        channel_elem = ET.SubElement(tv, "channel", {"id": ch_id})
        ET.SubElement(channel_elem, "display-name").text = ch_name
        ET.SubElement(channel_elem, "icon", {"src": logo})

        # 2. आज (offset=0) और कल (offset=1) का EPG डेटा प्राप्त करें
        for offset in:
            try:
                epg_data = requests.get(EPG_API.format(ch_id, offset), headers=headers).json()
                for prog in epg_data.get("epg", []):
                    start_dt = datetime.fromtimestamp(prog["startEpoch"] / 1000, tz=timezone(timedelta(hours=5, minutes=30)))
                    end_dt = datetime.fromtimestamp(prog["endEpoch"] / 1000, tz=timezone(timedelta(hours=5, minutes=30)))

                    prog_elem = ET.SubElement(tv, "programme", {
                        "start": start_dt.strftime("%Y%m%d%H%M%S %z"),
                        "stop": end_dt.strftime("%Y%m%d%H%M%S %z"),
                        "channel": ch_id
                    })
                    ET.SubElement(prog_elem, "title", {"lang": "en"}).text = prog.get("showname", "No Title")
                    ET.SubElement(prog_elem, "desc", {"lang": "en"}).text = prog.get("description", "")
            except Exception as e:
                continue

    # 3. XML को epg.xml.gz में कंप्रेस करके सेव करें
    xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
    with gzip.open("epg.xml.gz", "wb") as f:
        f.write(xml_bytes)

if __name__ == "__main__":
    fetch_and_build_epg()
                  

import gzip
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# JioTV के सही API Endpoints
CHANNELS_API = "https://jio.com"
EPG_API = "https://jio.com{}&offset={}"

# यहाँ अपने पसंदीदा चैनल्स की ID डालें
TARGET_CHANNELS = [
    "144",  # Colors HD
    "175",  # Aastha
    "471",  # Sony SAB HD
    "291",  # SET HD
    "154",  # Zee TV HD
    "167",  # Star Plus HD
]

def fetch_and_build_epg():
    tv = ET.Element("tv", {"generator-info-name": "JioTV-Custom-EPG"})
    
    headers = {
        "User-Agent": "okhttp/4.2.2",
        "appkey": "NzNiMDhlYzQyNjJm",
        "os": "android"
    }

    # 1. चैनल लिस्ट प्राप्त करें
    resp = requests.get(CHANNELS_API, headers=headers).json()
    channels = resp.get("result", [])

    for ch in channels:
        ch_id = str(ch["channel_id"])
        
        # केवल चुनिंदा चैनल्स को ही प्रोसेस करें
        if ch_id not in TARGET_CHANNELS:
            continue

        ch_name = ch["channel_name"]
        logo = f"https://jio.com{ch['logoUrl']}"

        channel_elem = ET.SubElement(tv, "channel", {"id": ch_id})
        ET.SubElement(channel_elem, "display-name").text = ch_name
        ET.SubElement(channel_elem, "icon", {"src": logo})

        # 2. आज (0) और कल (1) का EPG डेटा प्राप्त करें
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
                print(f"Error fetching {ch_id}: {e}")
                continue

    # 3. XML को epg.xml.gz में कंप्रेस करके सेव करें
    xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
    with gzip.open("epg.xml.gz", "wb") as f:
        f.write(xml_bytes)
    print("epg.xml.gz सफलतापूर्वक बन गई है!")

if __name__ == "__main__":
    fetch_and_build_epg()
    

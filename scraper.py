import gzip
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

URL = "https://knowledgeskey.com"
CHANNEL_ID = "Goldmines.in"
CHANNEL_NAME = "Goldmines"


def fetch_and_generate():
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(URL, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  # Extract text lines cleanly
  lines = [
      line.strip()
      for line in soup.get_text(separator="\n").split("\n")
      if line.strip()
  ]

  schedule = []
  current_date = None
  date_pattern = re.compile(r"^(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})$")
  time_pattern = re.compile(r"^(\d{1,2}:\d{1,2}\s*[AP]M)$", re.IGNORECASE)

  for i, line in enumerate(lines):
    # Match Date (e.g., 23 Nov 2026)
    date_match = date_pattern.match(line)
    if date_match:
      try:
        current_date = datetime.strptime(date_match.group(1), "%d %b %Y")
      except ValueError:
        pass
      continue

    # Match Time (e.g., 01:33 AM or 04:3 AM)
    time_match = time_pattern.match(line)
    if time_match and current_date and i >= 2:
      raw_time = time_match.group(1).upper().replace(" ", "")
      # Fix single-digit minutes like 04:3AM -> 04:03AM
      parts = re.match(r"(\d{1,2}):(\d{1,2})([AP]M)", raw_time)
      if parts:
        hr, mn, ampm = parts.groups()
        fixed_time = f"{int(hr):02d}:{int(mn):02d} {ampm}"
        dt_start = datetime.strptime(
            f"{current_date.strftime('%Y-%m-%d')} {fixed_time}",
            "%Y-%m-%d %I:%M %p",
        )

        # Title is usually 2 lines above the time (skipping "Hindi | Film")
        title = lines[i - 2] if "Hindi" in lines[i - 1] else lines[i - 1]
        schedule.append((dt_start, title))

  # Sort chronologically
  schedule.sort(key=lambda x: x[0])

  # Build XMLTV structure
  tv = ET.Element("tv", {"generator-info-name": "Auto-Goldmines-EPG"})
  channel = ET.SubElement(tv, "channel", {"id": CHANNEL_ID})
  ET.SubElement(channel, "display-name").text = CHANNEL_NAME

  for idx, (start_dt, title) in enumerate(schedule):
    if idx + 1 < len(schedule):
      stop_dt = schedule[idx + 1][0]
    else:
      stop_dt = start_dt + timedelta(hours=2, minutes=30)

    prog = ET.SubElement(
        tv,
        "programme",
        {
            "start": start_dt.strftime("%Y%m%d%H%M%S +0530"),
            "stop": stop_dt.strftime("%Y%m%d%H%M%S +0530"),
            "channel": CHANNEL_ID,
        },
    )
    ET.SubElement(prog, "title", {"lang": "hi"}).text = title
    ET.SubElement(prog, "desc", {"lang": "hi"}).text = (
        f"{title} - Hindi Dubbed Movie on Goldmines"
    )
    ET.SubElement(prog, "category", {"lang": "en"}).text = "Movie"

  # Write compressed epg.xml.gz
  xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
  with gzip.open("epg.xml.gz", "wb") as f:
    f.write(xml_bytes)


if __name__ == "__main__":
  fetch_and_generate()
    

import gzip
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
import requests

PRIMARY_URL = "https://freedish.app/channel/33"
CHANNEL_ID = "goldmines.in"
CHANNEL_NAME = "Goldmines"

IST = timezone(timedelta(hours=5, minutes=30))
# Matches "12:00 am - 1:33 am" or "10:34 pm - 5:29 am"
RANGE_PATTERN = re.compile(
    r"^(\d{1,2}:\d{2}\s*[ap]m)\s*[-–]\s*(\d{1,2}:\d{2}\s*[ap]m)$", re.I
)


def parse_freedish_app():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
      )
  }
  resp = requests.get(PRIMARY_URL, headers=headers, timeout=25)
  resp.raise_for_status()

  soup = BeautifulSoup(resp.text, "html.parser")
  lines = [line.strip() for line in soup.stripped_strings if line.strip()]

  today_date = datetime.now(IST).replace(
      hour=0, minute=0, second=0, microsecond=0
  )
  current_date = today_date
  last_start_minutes = -1
  programs = []

  for i, line in enumerate(lines):
    match = RANGE_PATTERN.match(line)
    if match and i + 1 < len(lines):
      start_str, end_str = match.group(1), match.group(2)
      title = lines[i + 1]

      # Skip table header or utility links
      if title.lower() in ("information", "alarm", "get .ics file"):
        continue

      s_time = datetime.strptime(start_str.upper(), "%I:%M %p")
      e_time = datetime.strptime(end_str.upper(), "%I:%M %p")
      start_minutes = s_time.hour * 60 + s_time.minute

      if last_start_minutes != -1 and start_minutes < last_start_minutes:
        current_date += timedelta(days=1)
      last_start_minutes = start_minutes

      start_dt = current_date.replace(hour=s_time.hour, minute=s_time.minute)
      end_dt = current_date.replace(hour=e_time.hour, minute=e_time.minute)
      if end_dt <= start_dt:
        end_dt += timedelta(days=1)

      programs.append({
          "title": title,
          "desc": f"{title} - Hindi Dubbed Movie on Goldmines",
          "start": start_dt.strftime("%Y%m%d%H%M%S +0530"),
          "stop": end_dt.strftime("%Y%m%d%H%M%S +0530"),
      })

  return programs


def build_goldmines_epg():
  tv = ET.Element("tv", {"generator-info-name": "Goldmines-Custom-EPG"})
  ch_elem = ET.SubElement(tv, "channel", {"id": CHANNEL_ID})
  ET.SubElement(ch_elem, "display-name").text = CHANNEL_NAME

  try:
    progs = parse_freedish_app()
    for p in progs:
      prog_elem = ET.SubElement(
          tv,
          "programme",
          {"start": p["start"], "stop": p["stop"], "channel": CHANNEL_ID},
      )
      ET.SubElement(prog_elem, "title", {"lang": "hi"}).text = p["title"]
      ET.SubElement(prog_elem, "desc", {"lang": "hi"}).text = p["desc"]
      ET.SubElement(prog_elem, "category", {"lang": "en"}).text = "Movie"
    print(f"Success: {CHANNEL_NAME} ({len(progs)} shows scraped)")
  except Exception as e:
    print(f"Error scraping {CHANNEL_NAME}: {e}")

  xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
  with gzip.open("goldmines.xml.gz", "wb") as f:
    f.write(xml_bytes)


if __name__ == "__main__":
  build_goldmines_epg()
  

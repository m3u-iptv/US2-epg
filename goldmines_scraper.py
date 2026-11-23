import gzip
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
import requests

URL = "https://www.freedishtoday.com/goldmines-today-schedule-for-free-dish-users/"
CHANNEL_ID = "goldmines.in"
CHANNEL_NAME = "Goldmines"


def get_lines():
  # 1. Try curl_cffi (Chrome TLS impersonation)
  try:
    resp = cffi_requests.get(URL, impersonate="chrome120", timeout=25)
    if resp.status_code == 200 and "AM" in resp.text:
      soup = BeautifulSoup(resp.text, "html.parser")
      lines = [line.strip() for line in soup.stripped_strings if line.strip()]
      if len(lines) > 15:
        print("Fetched via curl_cffi")
        return lines
  except Exception as e:
    print(f"curl_cffi error: {e}")

  # 2. Fallback to Jina Reader
  try:
    resp = requests.get(f"https://jina.ai{URL}", timeout=25)
    if resp.status_code == 200 and "AM" in resp.text:
      clean_text = re.sub(r"[*#_`]", "", resp.text)
      lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
      if len(lines) > 15:
        print("Fetched via Jina Reader")
        return lines
  except Exception as e:
    print(f"Jina error: {e}")

  return []


def build_goldmines_epg():
  lines = get_lines()
  schedule_dict = {}
  current_date = None

  date_pattern = re.compile(
      r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
      re.I,
  )
  time_pattern = re.compile(r"^(\d{1,2}:\d{1,2}\s*[AP]M)$", re.I)

  for i, line in enumerate(lines):
    date_match = date_pattern.search(line)
    if date_match:
      raw_date = date_match.group(1)
      for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
          current_date = datetime.strptime(raw_date, fmt)
          break
        except ValueError:
          continue
      continue

    time_match = time_pattern.match(line)
    if time_match and current_date and i >= 1:
      raw_time = time_match.group(1).upper().replace(" ", "")
      parts = re.match(r"(\d{1,2}):(\d{1,2})([AP]M)", raw_time)
      if parts:
        hr, mn, ampm = parts.groups()
        fixed_time = f"{int(hr):02d}:{int(mn):02d} {ampm}"
        dt_start = datetime.strptime(
            f"{current_date.strftime('%Y-%m-%d')} {fixed_time}",
            "%Y-%m-%d %I:%M %p",
        )

        # Movie title detect karein ("Hindi | Film" skip karke)
        title = "Movie"
        for back in range(1, 5):
          if i - back >= 0:
            candidate = lines[i - back].strip()
            if (
                candidate
                and not any(
                    skip in candidate.lower()
                    for skip in [
                        "hindi",
                        "film",
                        "goldmines",
                        "schedule",
                        "|",
                        "source:",
                    ]
                )
                and not date_pattern.search(candidate)
            ):
              title = candidate
              break

        if dt_start not in schedule_dict or schedule_dict[dt_start] == "Movie":
          schedule_dict[dt_start] = title

  # Chronological order mein sort karein
  sorted_items = sorted(schedule_dict.items(), key=lambda item: item[0])
  print(f"Total Goldmines programs scraped: {len(sorted_items)}")

  # XMLTV structure banayein
  tv = ET.Element("tv", {"generator-info-name": "Goldmines-FreeDish-EPG"})
  ch_elem = ET.SubElement(tv, "channel", {"id": CHANNEL_ID})
  ET.SubElement(ch_elem, "display-name").text = CHANNEL_NAME

  for idx, (start_dt, title) in enumerate(sorted_items):
    if idx + 1 < len(sorted_items):
      stop_dt = sorted_items[idx + 1][0]
    else:
      stop_dt = start_dt + timedelta(hours=2, minutes=30)

    prog_elem = ET.SubElement(
        tv,
        "programme",
        {
            "start": start_dt.strftime("%Y%m%d%H%M%S +0530"),
            "stop": stop_dt.strftime("%Y%m%d%H%M%S +0530"),
            "channel": CHANNEL_ID,
        },
    )
    ET.SubElement(prog_elem, "title", {"lang": "hi"}).text = title
    ET.SubElement(prog_elem, "desc", {"lang": "hi"}).text = (
        f"{title} - Hindi Dubbed Movie on Goldmines"
    )
    ET.SubElement(prog_elem, "category", {"lang": "en"}).text = "Movie"

  xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
  with gzip.open("goldmines.xml.gz", "wb") as f:
    f.write(xml_bytes)


if __name__ == "__main__":
  build_goldmines_epg()
    

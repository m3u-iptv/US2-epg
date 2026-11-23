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
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "en-US,en;q=0.9",
  }
  response = requests.get(URL, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  # Extract all text lines cleanly
  lines = [
      line.strip()
      for line in soup.get_text(separator="\n").split("\n")
      if line.strip()
  ]

  schedule = []
  current_date = None

  # Matches date anywhere in the line (e.g., "Goldmines 23 Nov 2026" or "23 Nov 2026")
  date_pattern = re.compile(
      r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
      re.IGNORECASE,
  )
  # Matches time anywhere in the line (e.g., "01:33 AM" or "04:3 AM")
  time_pattern = re.compile(r"(\d{1,2}:\d{1,2}\s*[AP]M)", re.IGNORECASE)

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

    time_match = time_pattern.search(line)
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

        # Look upwards 1 to 3 lines to find the movie title (ignoring "Hindi | Film" or category labels)
        title = "Movie"
        for back in range(1, 4):
          if i - back >= 0:
            candidate = lines[i - back]
            if not any(
                skip in candidate.lower()
                for skip in ["hindi", "film", "goldmines", "schedule"]
            ):
              title = candidate
              break

        schedule.append((dt_start, title))

  # Remove duplicates & sort chronologically
  schedule = sorted(list(set(schedule)), key=lambda x: x[0])
  print(f"Total programs scraped: {len(schedule)}")

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
  

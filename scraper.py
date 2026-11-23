import gzip
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests

TARGET_URL = (
    "https://www.freedishtoday.com/goldmines-today-schedule-for-free-dish-users/"
)
API_URL = "https://freedishtoday.com"
JINA_URL = f"https://jina.ai{TARGET_URL}"

CHANNEL_ID = "Goldmines.in"
CHANNEL_NAME = "Goldmines"


def get_page_lines():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
      )
  }

  # Method 1: WordPress JSON API (Sabse fast aur block-free)
  try:
    r = requests.get(API_URL, headers=headers, timeout=20)
    if r.status_code == 200 and r.json():
      html_content = r.json()["content"]["rendered"]
      soup = BeautifulSoup(html_content, "html.parser")
      lines = [
          l.strip()
          for l in soup.get_text(separator="\n").split("\n")
          if l.strip()
      ]
      if len(lines) > 10:
        print("Fetched via WP API")
        return lines
  except Exception as e:
    print(f"API fallback: {e}")

  # Method 2: Jina Reader Proxy
  try:
    r = requests.get(JINA_URL, headers=headers, timeout=25)
    if r.status_code == 200 and "AM" in r.text:
      clean_text = re.sub(r"[*#_`]", "", r.text)
      lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
      if len(lines) > 10:
        print("Fetched via Jina Reader")
        return lines
  except Exception as e:
    print(f"Jina fallback: {e}")

  # Method 3: Direct HTML Fetch
  r = requests.get(TARGET_URL, headers=headers, timeout=25)
  soup = BeautifulSoup(r.text, "html.parser")
  print("Fetched via Direct HTML")
  return [
      l.strip() for l in soup.get_text(separator="\n").split("\n") if l.strip()
  ]


def fetch_and_generate():
  lines = get_page_lines()

  schedule = []
  current_date = None

  date_pattern = re.compile(
      r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
      re.IGNORECASE,
  )
  time_pattern = re.compile(r"^(\d{1,2}:\d{1,2}\s*[AP]M)$", re.IGNORECASE)

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

        # Movie title detect karein ("Hindi | Film" aur headers ko chhod kar)
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

        schedule.append((dt_start, title))

  # Duplicate entries hatayein aur time ke hisaab se sort karein
  unique_schedule = {}
  for dt, title in schedule:
    if dt not in unique_schedule or unique_schedule[dt] == "Movie":
      unique_schedule[dt] = title

  sorted_schedule = sorted(unique_schedule.items(), key=lambda x: x)
  print(f"Total programs scraped: {len(sorted_schedule)}")

  # XMLTV file banayein
  tv = ET.Element("tv", {"generator-info-name": "Auto-Goldmines-EPG"})
  channel = ET.SubElement(tv, "channel", {"id": CHANNEL_ID})
  ET.SubElement(channel, "display-name").text = CHANNEL_NAME

  for idx, (start_dt, title) in enumerate(sorted_schedule):
    if idx + 1 < len(sorted_schedule):
      stop_dt = sorted_schedule[idx + 1]
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

  xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
  with gzip.open("epg.xml.gz", "wb") as f:
    f.write(xml_bytes)


if __name__ == "__main__":
  fetch_and_generate()
  

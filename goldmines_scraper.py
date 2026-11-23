import gzip
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
import requests

CHANNEL_ID = "goldmines.in"
CHANNEL_NAME = "Goldmines"
IST = timezone(timedelta(hours=5, minutes=30))


def scrape_freedish_app():
  url = "https://freedish.app"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
      )
  }
  resp = requests.get(url, headers=headers, timeout=25)
  resp.raise_for_status()
  soup = BeautifulSoup(resp.text, "html.parser")

  programs = []
  today_date = datetime.now(IST).replace(
      hour=0, minute=0, second=0, microsecond=0
  )
  current_date = today_date
  last_start_minutes = -1

  # Flexible time range matcher: "12:00 am - 1:33 am", "12:00 AM to 01:33 AM", etc.
  time_range_re = re.compile(
      r"(\d{1,2}:\d{2}\s*[ap]m)\s*(?:-|–|—|to)\s*(\d{1,2}:\d{2}\s*[ap]m)", re.I
  )

  # Method A: Check HTML table rows first
  for tr in soup.find_all("tr"):
    row_text = " | ".join(
        td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])
    )
    m = time_range_re.search(row_text)
    if m:
      cells = [
          td.get_text(" ", strip=True)
          for td in tr.find_all(["td", "th"])
          if td.get_text(strip=True)
      ]
      title = next((c for c in cells if not time_range_re.search(c)), None)
      if title and title.lower() not in (
          "information",
          "alarm",
          "program",
          "show",
      ):
        start_str, end_str = m.group(1), m.group(2)
        s_time = datetime.strptime(
            re.sub(r"\s+", " ", start_str.upper()), "%I:%M %p"
        )
        e_time = datetime.strptime(
            re.sub(r"\s+", " ", end_str.upper()), "%I:%M %p"
        )
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

  if programs:
    print(f"Scraped {len(programs)} shows from freedish.app table")
    return programs

  # Method B: Check stripped_strings fallback on freedish.app
  lines = [l.strip() for l in soup.stripped_strings if l.strip()]
  for i, line in enumerate(lines):
    m = time_range_re.search(line)
    if m and i + 1 < len(lines):
      title = lines[i + 1]
      if title.lower() in ("information", "alarm", "get .ics file"):
        continue
      start_str, end_str = m.group(1), m.group(2)
      s_time = datetime.strptime(
          re.sub(r"\s+", " ", start_str.upper()), "%I:%M %p"
      )
      e_time = datetime.strptime(
          re.sub(r"\s+", " ", end_str.upper()), "%I:%M %p"
      )
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

  if programs:
    print(f"Scraped {len(programs)} shows from freedish.app lines")
  else:
    print("DEBUG freedish.app sample lines:", lines[:25])
  return programs


def scrape_freedishtoday_api():
  api_url = "https://freedishtoday.com"
  headers = {"User-Agent": "Mozilla/5.0"}
  resp = requests.get(api_url, headers=headers, timeout=25)
  if resp.status_code != 200 or not resp.json():
    return []

  html = resp.json()["content"]["rendered"]
  soup = BeautifulSoup(html, "html.parser")
  lines = [l.strip() for l in soup.stripped_strings if l.strip()]

  date_re = re.compile(
      r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
      re.I,
  )
  time_re = re.compile(r"^(\d{1,2}:\d{1,2}\s*[AP]M)$", re.I)

  raw_items = []
  current_date = None

  for i, line in enumerate(lines):
    dm = date_re.search(line)
    if dm:
      for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
          current_date = datetime.strptime(dm.group(1), fmt)
          break
        except ValueError:
          pass
      continue

    tm = time_re.match(line)
    if tm and current_date and i >= 1:
      parts = re.match(
          r"(\d{1,2}):(\d{1,2})([AP]M)", tm.group(1).upper().replace(" ", "")
      )
      if parts:
        hr, mn, ampm = parts.groups()
        dt_start = datetime.strptime(
            f"{current_date.strftime('%Y-%m-%d')} {int(hr):02d}:{int(mn):02d}"
            f" {ampm}",
            "%Y-%m-%d %I:%M %p",
        )
        title = "Movie"
        for back in range(1, 5):
          if i - back >= 0:
            cand = lines[i - back]
            if not any(
                s in cand.lower()
                for s in ["hindi", "film", "goldmines", "schedule", "|"]
            ) and not date_re.search(cand):
              title = cand
              break
        raw_items.append((dt_start, title))

  # Deduplicate & sort
  dedup = {}
  for dt, t in raw_items:
    if dt not in dedup or dedup[dt] == "Movie":
      dedup[dt] = t
  sorted_items = sorted(dedup.items(), key=lambda x: x)

  programs = []
  for idx, (start_dt, title) in enumerate(sorted_items):
    stop_dt = (
        sorted_items[idx + 1]
        if idx + 1 < len(sorted_items)
        else start_dt + timedelta(hours=2, minutes=30)
    )
    programs.append({
        "title": title,
        "desc": f"{title} - Hindi Dubbed Movie on Goldmines",
        "start": start_dt.strftime("%Y%m%d%H%M%S +0530"),
        "stop": stop_dt.strftime("%Y%m%d%H%M%S +0530"),
    })
  print(f"Scraped {len(programs)} shows from freedishtoday WP API")
  return programs


def build_goldmines_epg():
  progs = []
  try:
    progs = scrape_freedish_app()
  except Exception as e:
    print(f"freedish.app error: {e}")

  if not progs:
    try:
      progs = scrape_freedishtoday_api()
    except Exception as e:
      print(f"freedishtoday API error: {e}")

  tv = ET.Element("tv", {"generator-info-name": "Goldmines-Custom-EPG"})
  ch_elem = ET.SubElement(tv, "channel", {"id": CHANNEL_ID})
  ET.SubElement(ch_elem, "display-name").text = CHANNEL_NAME

  for p in progs:
    prog_elem = ET.SubElement(
        tv,
        "programme",
        {"start": p["start"], "stop": p["stop"], "channel": CHANNEL_ID},
    )
    ET.SubElement(prog_elem, "title", {"lang": "hi"}).text = p["title"]
    ET.SubElement(prog_elem, "desc", {"lang": "hi"}).text = p["desc"]
    ET.SubElement(prog_elem, "category", {"lang": "en"}).text = "Movie"

  print(f"FINAL COUNT: {CHANNEL_NAME} -> {len(progs)} programs")
  ET.indent(tv, space="  ")
  xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)

  with open("goldmines.xml", "wb") as f:
    f.write(xml_bytes)
  with gzip.open("goldmines-epg.xml.gz", "wb") as f:
    f.write(xml_bytes)


if __name__ == "__main__":
  build_goldmines_epg()
            

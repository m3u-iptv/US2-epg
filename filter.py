import xml.etree.ElementTree as ET

target_channels = {
    "Aastha.uk",
    "Utsav.Bharat.uk",
    "Utsav.Plus.HD.uk",
    "Zee.Cinema.uk",
    "Zee.TV.HD.uk"
}

tree = ET.parse("full.xml")
root = tree.getroot()

for elem in list(root):
    if elem.tag == "channel" and elem.get("id") not in target_channels:
        root.remove(elem)
    elif elem.tag == "programme" and elem.get("channel") not in target_channels:
        root.remove(elem)

tree.write("custom_epg.xml", encoding="utf-8", xml_declaration=True)

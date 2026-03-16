import xml.etree.ElementTree as ET
import os
import math

def etaisyys_pisteesta_viivaan(p, a, b):
    px, py = p[0], p[1]
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    l2 = (ax - bx)**2 + (ay - by)**2
    if l2 == 0: return math.sqrt((px - ax)**2 + (py - ay)**2)
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / l2))
    proj_x = ax + t * (bx - ax)
    proj_y = ay + t * (by - ay)
    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)

def rdp_karsinta(pisteet, epsilon):
    if len(pisteet) < 3:
        return pisteet
    max_dist = 0
    index = 0
    for i in range(1, len(pisteet) - 1):
        d = etaisyys_pisteesta_viivaan(pisteet[i], pisteet[0], pisteet[-1])
        if d > max_dist:
            index = i
            max_dist = d
    if max_dist > epsilon:
        vasen = rdp_karsinta(pisteet[:index+1], epsilon)
        oikea = rdp_karsinta(pisteet[index:], epsilon)
        return vasen[:-1] + oikea
    else:
        return [pisteet[0], pisteet[-1]]

def prosessoi_gpx(gpx_in, txt_out, tarkkuus=0.00005):
    if not os.path.exists(gpx_in):
        print(f"Tiedostoa {gpx_in} ei löydy.")
        return

    try:
        tree = ET.parse(gpx_in)
        root = tree.getroot()
        # Maastokartat käyttää tätä nimiavaruutta
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

        # Haetaan nimi
        nimi_el = root.find('.//gpx:trk/gpx:name', ns)
        reitin_nimi = nimi_el.text if nimi_el is not None else "Karsittu reitti"

        # TÄRKEÄ KORJAUS: Etsitään trkpt-tagit trkseg:n sisältä
        alkuperaiset = []
        for trkpt in root.findall('.//gpx:trkseg/gpx:trkpt', ns):
            lat = trkpt.get('lat')
            lon = trkpt.get('lon')
            if lat and lon:
                alkuperaiset.append([float(lat), float(lon)])

        if not alkuperaiset:
            print("GPX-tiedostosta ei löytynyt koordinaatteja. Tarkista polku.")
            return

        # Suoritetaan karsinta
        karsitut = rdp_karsinta(alkuperaiset, tarkkuus)

        # Tallennetaan
        with open(txt_out, 'w', encoding='utf-8') as f:
            f.write(f"# {reitin_nimi} (Alkuperäisiä: {len(alkuperaiset)}, Karsittuja: {len(karsitut)})\n")
            for p in karsitut:
                f.write(f"{p[0]}, {p[1]}\n")

        print(f"VALMIS! '{reitin_nimi}' tallennettu tiedostoon: {txt_out}")
        print(f"Pisteitä poistettu: {len(alkuperaiset) - len(karsitut)} kpl.")

    except Exception as e:
        print(f"Virhe: {e}")

if __name__ == "__main__":
    # tarkkuus 0.00005 on n. 5 metriä. Suurenna lukua jos haluat karsia enemmän.
    prosessoi_gpx('reitti.gpx', 'gpx-reitti.txt', tarkkuus=0.00005)

import os
import folium
import base64
import html
import webbrowser
import random  # Tarvitaan hajontaa varten
from exif import Image as ExifImage
from PIL import Image, ImageOps
from io import BytesIO

def decimal_coords(coords, ref):
    try:
        d, m, s = float(coords[0]), float(coords[1]), float(coords[2])
        decimal = d + (m / 60.0) + (s / 3600.0)
        return -decimal if ref in ['S', 'W'] else decimal
    except: return None

def get_photo_data(filepath):
    try:
        with open(filepath, 'rb') as f:
            img_exif = ExifImage(f)
            has_gps = hasattr(img_exif, 'gps_latitude') and img_exif.has_exif
            lat = decimal_coords(img_exif.gps_latitude, img_exif.gps_latitude_ref) if has_gps else None
            lon = decimal_coords(img_exif.gps_longitude, img_exif.gps_longitude_ref) if has_gps else None
            dt = getattr(img_exif, 'datetime_original', 'Aikaleima puuttuu')
        
        if lat is None:
            return None, dt, None

        with Image.open(filepath) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((350, 350))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=75)
            img_str = base64.b64encode(buf.getvalue()).decode()
        return (lat, lon), dt, img_str
    except: return None, None, None

def lue_reitit(tiedosto='reitit.txt'):
    reitit = []
    nykyinen = None
    if os.path.exists(tiedosto):
        with open(tiedosto, 'r', encoding='utf-8') as f:
            for rivi in f:
                rivi = rivi.strip()
                if not rivi: continue
                if rivi.startswith('#'):
                    nykyinen = {'otsikko': rivi[1:].strip(), 'pisteet': []}
                    reitit.append(nykyinen)
                elif nykyinen:
                    try:
                        osat = rivi.split(',')
                        nykyinen['pisteet'].append([float(osat[0]), float(osat[1])])
                    except: continue
    return reitit

def lue_kohteet(tiedosto='kohteet.txt'):
    kohteet = []
    if os.path.exists(tiedosto):
        with open(tiedosto, 'r', encoding='utf-8') as f:
            for rivi in f:
                osat = rivi.strip().split(',')
                if len(osat) >= 3:
                    try:
                        nimi = osat[0].strip()
                        lat = float(osat[1].strip())
                        lon = float(osat[2].strip())
                        kohteet.append({'nimi': nimi, 'coords': [lat, lon]})
                    except: continue
    return kohteet

def create_map(photo_dir='photos'):
    # 1. Kartan alustus
    m = folium.Map(location=[60.2121, 21.3057], zoom_start=9, tiles=None)
    
    m.get_root().header.add_child(folium.Element("""
        <style>
            path.leaflet-interactive:focus { outline: none !important; }
            .leaflet-container :focus { outline: none !important; }
        </style>
    """))

    folium.TileLayer('openstreetmap', name='Normaali kartta', overlay=False).add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com{x}&y={y}&z={z}', 
        attr='Google', name='Satelliitti', overlay=False, show=False
    ).add_to(m)

    kaikki_pisteet = []
    puuttuvat_gps = []
    
    # 2. Reitit
    reitit = lue_reitit('reitit.txt')
    for i, reitti in enumerate(reitit):
        if reitti['pisteet']:
            folium.PolyLine(
                reitti['pisteet'], color="blue", weight=4, opacity=0.7,
                tooltip=reitti['otsikko'],
                popup=folium.Popup(f"<b>{reitti['otsikko']}</b>", max_width=450)
            ).add_to(m)
            kaikki_pisteet.extend(reitti['pisteet'])

            # Alku- ja loppuikonit reiteille
            if i == 0:
                folium.Marker(
                    reitti['pisteet'][0], 
                    popup=folium.Popup("REITIN ALKU", max_width=450), 
                    icon=folium.Icon(color='green', icon='play', prefix='fa')
                ).add_to(m)
            if i == len(reitit) - 1:
                folium.Marker(
                    reitti['pisteet'][-1], 
                    popup=folium.Popup("REITIN LOPPU", max_width=450), 
                    icon=folium.Icon(color='red', icon='flag', prefix='fa')
                ).add_to(m)

    # 3. Valokuvat hajonnalla (Jitter)
    if os.path.exists(photo_dir):
        for fn in os.listdir(photo_dir):
            if fn.lower().endswith(('jpg', 'jpeg')):
                coords, dt, img_b64 = get_photo_data(os.path.join(photo_dir, fn))
                if coords:
                    # Lisätään pieni hajonta (n. 5-15 metriä), jotta päällekkäiset kuvat erottuvat
                    lat_j = coords[0] + random.uniform(-0.0001, 0.0001)
                    lon_j = coords[1] + random.uniform(-0.0001, 0.0001)
                    jittered_coords = [lat_j, lon_j]
                    
                    kaikki_pisteet.append(jittered_coords)
                    web_path = os.path.join(photo_dir, fn).replace("\\", "/")
                    pop = f'<b>{html.escape(str(dt))}</b><br><a href="{web_path}" target="_blank"><img src="data:image/jpeg;base64,{img_b64}" width="350"></a>'
                    
                    folium.Marker(
                        jittered_coords, 
                        popup=folium.Popup(pop, max_width=450),
                        icon=folium.Icon(color='blue', icon='camera')
                    ).add_to(m)
                else:
                    puuttuvat_gps.append(fn)

    # Kirjoitetaan puuttuvat GPS-tiedot
    with open('puuttuvat_gps.txt', 'w', encoding='utf-8') as f:
        if puuttuvat_gps:
            f.write("\n".join(sorted(puuttuvat_gps)))
        else:
            f.write("Kaikissa kuvissa on GPS-tiedot.")

    # 4. Käyntikohteet (Oranssit ikonit päällimmäiseksi)
    kohteet = lue_kohteet('kohteet.txt')
    for kohde in kohteet:
        kaikki_pisteet.append(kohde['coords'])
        folium.Marker(
            kohde['coords'], 
            popup=folium.Popup(f"<b>{kohde['nimi']}</b>", max_width=450),
            icon=folium.Icon(color='orange', icon='info-sign'),
            z_index_offset=1000  # Nostaa nämä muiden päälle
        ).add_to(m)

    # GLOBAALI JAVASCRIPT: Reitin korostus
    m.get_root().html.add_child(folium.Element("""
        <script>
            window.onload = function() {
                var mapDiv = document.querySelector('.folium-map');
                var leafletMap = window[mapDiv.id];
                leafletMap.on('popupopen', function(e) {
                    if (e.popup._source instanceof L.Polyline && !(e.popup._source instanceof L.Marker)) {
                        e.popup._source.setStyle({color: 'red', weight: 8, opacity: 1});
                    }
                });
                leafletMap.on('popupclose', function(e) {
                    if (e.popup._source instanceof L.Polyline && !(e.popup._source instanceof L.Marker)) {
                        e.popup._source.setStyle({color: 'blue', weight: 4, opacity: 0.7});
                    }
                });
            };
        </script>
    """))

    folium.LayerControl(collapsed=False).add_to(m)
    
    if kaikki_pisteet:
        m.fit_bounds(kaikki_pisteet)
        output = 'valokuvakartta.html'
        m.save(output)
        webbrowser.open('file://' + os.path.realpath(output))

if __name__ == "__main__":
    create_map()

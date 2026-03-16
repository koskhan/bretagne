import os
import piexif
from PIL import Image

def muunna_exif_koordinaateiksi(arvo):
    """Muuntaa desimaaliluvun EXIF-muotoon (asteet, minuutit, sekunnit)."""
    abs_arvo = abs(arvo)
    asteet = int(abs_arvo)
    minuutit = int((abs_arvo - asteet) * 60)
    sekunnit = int((abs_arvo - asteet - minuutit/60) * 3600 * 100)
    return ((asteet, 1), (minuutit, 1), (sekunnit, 100))

def puhdista_exif(exif_dict):
    """Poistaa EXIF-sanakirjasta arvot, joita piexif ei osaa käsitellä (ehkäisee 'dump' virheet)."""
    for ifd in ("0th", "Exif", "GPS", "1st"):
        if ifd in exif_dict:
            for tag in list(exif_dict[ifd]):
                try:
                    # Testataan pystyykö piexif pakkaamaan tämän yksittäisen tagin
                    piexif.dump({ifd: {tag: exif_dict[ifd][tag]}})
                except:
                    # Jos tallennus epäonnistuu (kuten virhe 41729), poistetaan se
                    del exif_dict[ifd][tag]
    return exif_dict

def tallenna_gps(tiedosto_nimi, lat, lon):
    polku = os.path.join('photos', tiedosto_nimi.strip())
    if not os.path.exists(polku):
        print(f"Hylätty: Tiedostoa '{polku}' ei löydy.")
        return False

    try:
        img = Image.open(polku)
        
        # Alustetaan tyhjä EXIF-rakenne
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Jos kuvassa on jo EXIF-tietoa, ladataan ja puhdistetaan se
        if "exif" in img.info:
            try:
                exif_dict = piexif.load(img.info["exif"])
                exif_dict = puhdista_exif(exif_dict)
            except:
                print(f"Varoitus: Kuvan {tiedosto_nimi} EXIF-data oli pahasti vioittunut, alustetaan uusi.")

        # Lisätään tai päivitetään GPS-tiedot
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = muunna_exif_koordinaateiksi(lat)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = muunna_exif_koordinaateiksi(lon)

        # Muunnetaan sanakirja tavuiksi ja tallennetaan kuva
        exif_bytes = piexif.dump(exif_dict)
        img.save(polku, exif=exif_bytes)
        img.close()
        return True
    except Exception as e:
        print(f"Virhe tiedostossa {tiedosto_nimi}: {e}")
        return False

if __name__ == "__main__":
    lista_file = 'koordinaatit.txt'
    
    if not os.path.exists(lista_file):
        print(f"Virhe: Tiedostoa '{lista_file}' ei löydy.")
        with open(lista_file, 'w', encoding='utf-8') as f:
            f.write("# Malli: kuva1.jpg, 60.1695, 24.9354\n")
        print(f"Loin tyhjän mallitiedoston '{lista_file}'. Täytä se ja aja ohjelma uudelleen.")
    else:
        onnistuneet = 0
        with open(lista_file, 'r', encoding='utf-8') as f:
            for rivi in f:
                rivi = rivi.strip()
                if not rivi or rivi.startswith('#'):
                    continue
                
                try:
                    osat = rivi.split(',')
                    if len(osat) == 3:
                        nimi = osat[0].strip()
                        lat = float(osat[1].strip())
                        lon = float(osat[2].strip())
                        
                        if tallenna_gps(nimi, lat, lon):
                            print(f"Päivitetty: {nimi}")
                            onnistuneet += 1
                    else:
                        print(f"Virheellinen rivi: {rivi} (pitää olla: nimi, lat, lon)")
                except ValueError:
                    print(f"Virheelliset koordinaatit rivillä: {rivi}")

        print(f"\nValmis! Päivitettiin yhteensä {onnistuneet} kuvaa.")

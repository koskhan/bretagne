import re
import os
import html

def palauta_kaikki_tiedot_html(html_file='valokuvakartta.html', output_file='reitit.txt'):
    if not os.path.exists(html_file):
        print(f"Virhe: Tiedostoa '{html_file}' ei löydy.")
        return

    with open(html_file, 'r', encoding='utf-8') as f:
        sisalto = f.read()

    # 1. Etsitään kaikki PolyLine-muuttujat ja koordinaatit
    pattern_lines = re.compile(r'var\s+(poly_line_[a-z0-9]+)\s*=\s*L\.polyline\(\s*(\[\[.*?\]\])', re.DOTALL)
    reitit = pattern_lines.findall(sisalto)

    if not reitit:
        print("Tiedostosta ei löytynyt reittejä.")
        return

    tulokset = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for var_name, koord_str in reitit:
            otsikko = "Palautettu reitti"
            
            # SEURATAAN LINKITYSKETJUA:
            # a) Etsitään popup-muuttuja, joka on sidottu tähän viivaan
            bind_match = re.search(var_name + r'\.bindPopup\((.*?)\)', sisalto)
            if bind_match:
                popup_var = bind_match.group(1).strip()
                
                # b) Etsitään html-muuttuja, joka on asetettu tähän popupiin
                content_match = re.search(popup_var + r'\.setContent\((.*?)\)', sisalto)
                if content_match:
                    html_var = content_match.group(1).strip()
                    
                    # c) Etsitään itse tekstisisältö html-muuttujan määrittelystä
                    # Folium käyttää usein jQuery-tyylistä $('<div>...</div>')[0] määrittelyä
                    text_pattern = r'var\s+' + html_var + r'\s*=\s*\$\(\'([\s\S]*?)\'\)'
                    text_match = re.search(text_pattern, sisalto)
                    
                    if text_match:
                        raw_html = text_match.group(1)
                        # Poistetaan HTML-tagit (<b>, <div> jne) ja siistitään teksti
                        otsikko = re.sub(r'<[^>]*>', '', raw_html)
                        otsikko = html.unescape(otsikko).strip()

            # Puhdistetaan ja tallennetaan koordinaatit
            osat = [s.strip() for s in koord_str.replace('[', '').replace(']', '').split(',') if s.strip()]
            
            f.write(f"# {otsikko}\n")
            for i in range(0, len(osat), 2):
                if i + 1 < len(osat):
                    f.write(f"{osat[i]}, {osat[i+1]}\n")
            
            f.write("\n")
            tulokset += 1
            print(f"Palautettu otsikolla: {otsikko}")

    print(f"\nVALMIS! {tulokset} reittiä palautettu tiedostoon '{output_file}'.")

if __name__ == "__main__":
    palauta_kaikki_tiedot_html()

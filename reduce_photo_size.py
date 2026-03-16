import os
from PIL import Image

def optimoi_kuvat(input_dir='photos', output_dir='optimoidut', target_height=1800, max_kb=500):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            img_path = os.path.join(input_dir, filename)
            save_path = os.path.join(output_dir, filename)

            with Image.open(img_path) as img:
                # 1. Säilytä alkuperäinen EXIF-data (GPS, aika)
                exif_data = img.info.get('exif')

                # 2. Muuta kokoa korkeuden mukaan (säilytä kuvasuhde)
                w, h = img.size
                new_w = int(w * (target_height / h))
                img = img.resize((new_w, target_height), Image.Resampling.LANCZOS)

                # 3. Iteratiivinen pakkaus alle 500 kt rajaan
                laatu = 85
                while laatu > 10:
                    img.save(save_path, "JPEG", exif=exif_data, quality=laatu, optimize=True)
                    
                    # Tarkista onko koko alle 500 kt (500 * 1024 tavua)
                    if os.path.getsize(save_path) <= max_kb * 1024:
                        break
                    laatu -= 5  # Lasketaan laatua portaittain
            
            print(f"Valmis: {filename} (Laatu: {laatu}%, Koko: {os.path.getsize(save_path)//1024}kt)")

if __name__ == "__main__":
    optimoi_kuvat()

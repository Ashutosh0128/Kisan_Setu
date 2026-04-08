import os
import re
import urllib.request
import urllib.parse
import django

# Setup django to update DB
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan_backend.settings')
django.setup()

from api.models import Equipment

def get_image_url(query):
    # Use Yahoo Image search, heavily relying on the 'tse\d.mm.bing.net' proxy URLs which give high quality images directly
    url = f"https://images.search.yahoo.com/search/images;?p={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
        
        # Look for the Bing thumbnail URLs which are reliable and don't require hotlink bypasses
        matches = re.findall(r"src='(https://tse\d\.mm\.bing\.net/th\?[^']+)'", html)
        if matches:
             # Grab the first match. Clean it up to ensure it fetches the full size if possible (by altering the w/h params or just using the root id)
             best_url = matches[0]
             # To get a slightly larger image, remove &w=... &h=...
             best_url = re.sub(r'&w=\d+', '&w=800', best_url)
             best_url = re.sub(r'&h=\d+', '&h=600', best_url)
             best_url = best_url.replace('&c=7', '&c=0') # Don't crop heavily
             return best_url
             
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    return None

def main():
    equipments = Equipment.objects.all()
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    for eq in equipments:
        print(f"Searching for {eq.name}...")
        img_url = get_image_url(eq.name + " high quality photo")
        if img_url:
            print(f"Found: {img_url}")
            filename = eq.name.lower().replace(" ", "_").replace("-", "_") + ".jpg"
            filepath = os.path.join(assets_dir, filename)
            
            try:
                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, timeout=10) as response, open(filepath, 'wb') as out_file:
                    out_file.write(response.read())
                
                # Update DB to point to new image
                eq.image = f"assets/{filename}"
                eq.save()
                print(f"Successfully saved {filename} to DB")
            except Exception as e:
                print(f"Failed to download/save {filename}: {e}")
        else:
            print(f"No image found for {eq.name}")

    print("Done updating equipment images.")

if __name__ == "__main__":
    main()

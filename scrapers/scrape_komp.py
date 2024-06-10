import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re

client = MongoClient('mongodb://mongo:27017/projekt')
db = client['projekt']
collection = db['televisions']

base_url = 'https://www.morele.net/kategoria/komputery-stacjonarne-672/,,,,,,,,0,,,,/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

async def fetch_page(session, url):
    async with session.get(url, headers=headers) as response:
        return await response.text()

async def parse_page(session, url):
    print(f'Parsing URL: {url}')
    page_content = await fetch_page(session, url)
    soup = BeautifulSoup(page_content, 'html.parser')

    product_list = soup.find('div', {'class': 'cat-list-products', 'data-controller': 'product-list'})
    if product_list:
        products = product_list.find_all('div', class_='cat-product card')
        if products:
            for product in products:
                try:
                    name = product.get('data-product-name', 'Brak nazwy')
                    
                    price_tag = product.select_one('.price-new')
                    image_tag = product.select_one('img.product-image')
                    link_tag = product.select_one('div.cat-product-image')
                    features_tag = product.select('.cat-product-feature')
                    
                    price_str = price_tag.text.strip().split('zł')[0].replace(',', '.').replace(' ', '').strip() if price_tag else "0"
                    price_str = ''.join(filter(lambda x: x.isdigit() or x == '.', price_str))
                    price = float(price_str)
                    
                    image = image_tag.get('data-src') if image_tag and image_tag.get('data-src') else (image_tag.get('src') if image_tag else "Brak obrazka")
                    link = link_tag['data-button-href-param'] if link_tag and link_tag.has_attr('data-button-href-param') else "Brak linku"
                    full_link = f'https://www.morele.net{link}' if not link.startswith('http') else link

                    features = {}
                    for feature in features_tag:
                        feature_name = feature.get_text(strip=True).split(':')[0]
                        feature_value = feature.find('b').get_text(strip=True) if feature.find('b') else "Brak"
                        features[feature_name] = feature_value

                    product_data = {
                        'name': name,
                        'price': price,
                        'image': image,
                        'link': full_link,
                        'features': features
                    }

                    result = collection.insert_one(product_data)
                    #print(f'Zapisano produkt: {name}')
                except Exception as e:
                    print(f'Błąd podczas przetwarzania produktu: {e}')
        else:
            print("Nie znaleziono produktów wewnątrz kontenera.")
    else:
        print("Nie znaleziono kontenera listy produktów. Sprawdź selektor.")

async def scrape():
    async with aiohttp.ClientSession() as session:
        
        first_page_content = await fetch_page(session, base_url + '1/')
        soup = BeautifulSoup(first_page_content, 'html.parser')
        pagination_div = soup.select_one('.pagination-btn-nolink-anchor')
        if pagination_div:
            x = pagination_div.text.strip()
            #print(f"Pobrana wartość: {x}")
            num_pages = int(re.findall(r'\d+', x)[-1])
        else:
            print("Nie znaleziono div'a z klasą 'pagination-btn-nolink-anchor'.")
            num_pages = 1

        
        tasks = []
        for page in range(1, num_pages + 1):
            url = f'{base_url}{page}/'
            tasks.append(parse_page(session, url))

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(scrape())

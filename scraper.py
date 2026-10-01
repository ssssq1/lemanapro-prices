import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import time

# Очищенные URL категорий Лемана ПРО (без лишних параметров)
CATEGORIES = {
    "wall": "https://lemanapro.ru/catalogue/bloki-stroitelnye/gazobetonnyy-blok/",
    "roof": "https://lemanapro.ru/catalogue/metallocherepica/",
    "finish": "https://rostov.lemanapro.ru/catalogue/oboi-kreaforta/",
    "foundation": "https://lemanapro.ru/catalogue/armatura/",
    "tiles": "https://lemanapro.ru/catalogue/plitka-keramicheskaya/",
    "paint": "https://lemanapro.ru/catalogue/kraski/"
}

def get_prices_from_category(url):
    """Заходит на страницу категории и собирает цены, обходя защиту"""
    
    # Создаем скрейпер с реалистичными заголовками
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        delay=3  # Пауза между запросами, чтобы не спамить
    )
    
    # Добавляем дополнительные заголовки, как у настоящего браузера
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = scraper.get(url, headers=headers, timeout=20)
        
        if response.status_code == 403:
            print(f"   ⛔ Доступ запрещён (403). Попробуем упростить URL...")
            # Пробуем без www и с https
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = []
        
        # Метод 1: Ищем по data-testid="price-integer" (стабильный селектор)
        price_elements = soup.find_all(attrs={"data-testid": "price-integer"})
        for el in price_elements:
            price_text = el.get_text(strip=True)
            clean_price = re.sub(r'[^\d]', '', price_text)
            if clean_price and len(clean_price) > 0:
                prices.append(float(clean_price))
        
        # Метод 2: Ищем цены с символом рубля (резервный)
        if len(prices) == 0:
            price_texts = soup.find_all(string=re.compile(r'\d+\s*₽'))
            for text in price_texts:
                clean = re.sub(r'[^\d]', '', str(text).strip())
                if clean and len(clean) > 0:
                    prices.append(float(clean))
        
        # Метод 3: Ищем любые числовые значения в элементах с классом price
        if len(prices) == 0:
            price_classes = soup.find_all(class_=re.compile(r'[Pp]rice'))
            for el in price_classes:
                text = el.get_text(strip=True)
                clean = re.sub(r'[^\d]', '', text)
                if clean and len(clean) > 0:
                    prices.append(float(clean))
        
        # Берём среднее из первых 5-8 цен (чтобы избежать акционных)
        if len(prices) >= 3:
            sample = prices[:8]
            avg = sum(sample) / len(sample)
            return avg
        elif len(prices) > 0:
            return prices[0]
            
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:100]}")
    
    return None

def main():
    print("🔄 Начинаем обновление цен с Лемана ПРО...")
    print("=" * 60)
    print("💡 Используем cloudscraper для обхода защиты Cloudflare")
    print("=" * 60)
    
    # Базовые цены-заглушки
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0},
        "tiles": {"material": 900.0, "labor": 0.0},
        "paint": {"material": 400.0, "labor": 0.0}
    }

    updated = False
    success_count = 0
    
    for key, url in CATEGORIES.items():
        print(f"\n📂 Категория '{key}':")
        print(f"   URL: {url}")
        
        avg_price = get_prices_from_category(url)
        
        if avg_price is not None:
            avg_price = round(avg_price)
            old_price = prices_data[key]["material"]
            prices_data[key]["material"] = avg_price
            updated = True
            success_count += 1
            print(f"   ✅ Успех! Средняя цена: {avg_price} ₽")
        else:
            print(f"   ⚠️ Не удалось получить цены")

    print("\n" + "=" * 60)
    print(f"📊 Итого: успешно обновлено {success_count} из {len(CATEGORIES)} категорий")
    
    if updated:
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл prices.json создан/обновлён!")
        print("📄 Содержимое файла:")
        print(json.dumps(prices_data, indent=2, ensure_ascii=False))
    else:
        print(" Ни одна категория не обновилась.")
        print("💡 Попробуйте найти API сайта через F12 → Network")

if __name__ == "__main__":
    main()

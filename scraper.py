import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import time

# Ссылки на категории Лемана ПРО
CATEGORIES = {
    "wall": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/stroitelnye-materialy/stenovye-bloki/gazobeton/",
    "roof": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/krovlya-i-fasad/krovlya/metallocherepitsa/",
    "finish": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/otdelochnye-materialy/oboi/",
    "foundation": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/stroitelnye-materialy/armatura/",
    "tiles": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/otdelochnye-materialy/plitka-keramogranit/plitka-keramicheskaya/",
    "paint": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/otdelochnye-materialy/lakokrasochnye-materialy/kraski/"
}

def get_prices_from_category(url):
    """Заходит на страницу категории и собирает цены первых товаров, обходя защиту"""
    
    # Создаем скрейпер, который притворяется обычным браузером Chrome
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        delay=2 # Небольшая задержка, чтобы не спамить запросами
    )
    
    try:
        response = scraper.get(url, timeout=15)
        
        # Если всё равно 403, выводим для отладки
        if response.status_code == 403:
            print(f"   ⛔ Доступ запрещён (403). Защита сайта слишком строгая.")
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = []
        
        # Способ 1: Ищем по стабильному атрибуту data-testid
        price_elements_id = soup.find_all(attrs={"data-testid": "price-integer"})
        for el in price_elements_id:
            price_text = el.get_text(strip=True)
            clean_price = re.sub(r'[^\d]', '', price_text)
            if clean_price:
                prices.append(float(clean_price))
                
        # Способ 2: Если первый не сработал, ищем по символу рубля (резервный вариант)
        if len(prices) == 0:
            price_elements_text = soup.find_all(string=re.compile(r'\d+\s*₽'))
            for el in price_elements_text:
                clean_price = re.sub(r'[^\d]', '', str(el).strip())
                if clean_price:
                    prices.append(float(clean_price))
        
        # Берём цены первых 5 товаров и считаем среднее
        if len(prices) >= 3:
            sample = prices[:5]
            return sum(sample) / len(sample)
        elif len(prices) > 0:
            return prices[0]
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    return None

def main():
    print("🔄 Начинаем обновление цен с Лемана ПРО (с обходом защиты)...")
    print("=" * 60)
    
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0},
        "tiles": {"material": 900.0, "labor": 0.0},
        "paint": {"material": 400.0, "labor": 0.0}
    }

    updated = False
    for key, url in CATEGORIES.items():
        print(f"\n📂 Категория '{key}':")
        avg_price = get_prices_from_category(url)
        
        if avg_price is not None:
            avg_price = round(avg_price)
            old_price = prices_data[key]["material"]
            prices_data[key]["material"] = avg_price
            updated = True
            print(f"   ✅ Успех! Средняя цена: {avg_price} ₽ (было: {old_price} ₽)")
        else:
            print(f"   ⚠️ Не удалось получить цены.")

    print("\n" + "=" * 60)
    
    if updated:
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл prices.json успешно создан/обновлён!")
    else:
        print("⚠️ Ни одна категория не обновилась. Файл prices.json не создан.")

if __name__ == "__main__":
    main()

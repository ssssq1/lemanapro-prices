import requests
from bs4 import BeautifulSoup
import json
import re

# Ссылки на категории (добавил еще 2 для полноты картины)
CATEGORIES = {
    "wall": "https://vashdom24.ru/catalog/gazobetonnye_bloki/",
    "roof": "https://vashdom24.ru/catalog/metallocherepitsa/",
    "foundation": "https://vashdom24.ru/catalog/armatura/",
    "finish": "https://vashdom24.ru/catalog/oboi/"
}

def get_avg_price(url):
    """Пытается получить среднюю цену со страницы категории"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = []
        
        # Способ 1: Ищем элементы с классами, содержащими слова price, cost, sum
        for el in soup.find_all(class_=re.compile(r'price|cost|sum|tovar-price', re.IGNORECASE)):
            text = el.get_text(strip=True)
            clean = re.sub(r'[^\d]', '', text)
            # Фильтруем адекватные цены (от 10 до 100 000 рублей), чтобы отсечь мусор
            if clean and 10 < float(clean) < 100000:
                prices.append(float(clean))
                
        # Способ 2: Если классы не сработали, ищем паттерн "число + ₽" или "число + руб" в тексте
        if len(prices) < 3:
            text_content = soup.get_text()
            matches = re.findall(r'(\d{1,3}(?:\s\d{3})*)\s*(?:₽|руб\.|руб)', text_content, re.IGNORECASE)
            for m in matches[:30]: # Проверяем первые 30 совпадений
                clean = re.sub(r'[^\d]', '', m)
                if clean and 10 < float(clean) < 100000:
                    prices.append(float(clean))
        
        # Если нашли хотя бы 3 цены, берем среднее из первых 5 (чтобы избежать акционных "от")
        if len(prices) >= 3:
            sample = prices[:5]
            return sum(sample) / len(sample)
        elif len(prices) > 0:
            return prices[0]
            
        return None
        
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {str(e)[:80]}")
        return None

def main():
    print("🔄 Начинаем обновление цен с vashdom24.ru...")
    print("=" * 50)
    
    # Базовые значения
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0}
    }

    updated = False
    success_count = 0
    
    for key, url in CATEGORIES.items():
        print(f"\n📂 Категория '{key}':")
        avg_price = get_avg_price(url)
        
        if avg_price is not None:
            avg_price = round(avg_price)
            prices_data[key]["material"] = avg_price
            updated = True
            success_count += 1
            print(f"   ✅ Успех! Базовая цена: {avg_price} ₽")
        else:
            print(f"   ⚠️ Цены не найдены (возможно, нужна точная настройка селектора)")

    print("\n" + "=" * 50)
    print(f"📊 Итого: успешно {success_count} из {len(CATEGORIES)}")
    
    if updated:
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл prices.json успешно создан/обновлён!")
    else:
        print("⚠️ Ни одна категория не обновилась.")

if __name__ == "__main__":
    main()

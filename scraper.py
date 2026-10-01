import requests
from bs4 import BeautifulSoup
import json
import re

# Ссылки на категории vashdom24.ru
CATEGORIES = {
    # Для калькулятора дома
    "wall": "https://vashdom24.ru/catalog/gazobetonnye_bloki/",
    "roof": "https://vashdom24.ru/catalog/metallocherepitsa/",
    "foundation": "https://vashdom24.ru/catalog/armatura/",
    "finish": "https://vashdom24.ru/catalog/oboi/",
    "rebar12": "https://vashdom24.ru/catalog/armatura/",
    "rebar8": "https://vashdom24.ru/catalog/armatura/",
    "concrete": "https://vashdom24.ru/catalog/beton/",
    "glue": "https://vashdom24.ru/catalog/smesi/",
    "mortar": "https://vashdom24.ru/catalog/smesi/",
    # Для ремонта квартиры
    "wallpaper": "https://vashdom24.ru/catalog/oboi/",
    "laminate": "https://vashdom24.ru/catalog/laminat/",
    "tile": "https://vashdom24.ru/catalog/plitka/",
    "stretchCeiling": "https://vashdom24.ru/catalog/potolki/",
    "cable": "https://vashdom24.ru/catalog/kabel/",
    "socket": "https://vashdom24.ru/catalog/rozetki/",
    "pipe": "https://vashdom24.ru/catalog/truby/",
    "faucet": "https://vashdom24.ru/catalog/smesiteli/",
    "interiorDoor": "https://vashdom24.ru/catalog/dveri-mezhkomnatnye/",
    "entranceDoor": "https://vashdom24.ru/catalog/dveri-vhodnye/"
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
            if clean and 10 < float(clean) < 100000:
                prices.append(float(clean))
                
        # Способ 2: Если классы не сработали, ищем паттерн "число + ₽" или "число + руб"
        if len(prices) < 3:
            text_content = soup.get_text()
            matches = re.findall(r'(\d{1,3}(?:\s\d{3})*)\s*(?:₽|руб\.|руб)', text_content, re.IGNORECASE)
            for m in matches[:30]:
                clean = re.sub(r'[^\d]', '', m)
                if clean and 10 < float(clean) < 100000:
                    prices.append(float(clean))
        
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
    
    # Базовые значения (заглушки, если парсинг не сработает)
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0},
        "rebar12": {"material": 118.0, "labor": 0.0},
        "rebar8": {"material": 65.0, "labor": 0.0},
        "concrete": {"material": 5600.0, "labor": 0.0},
        "glue": {"material": 350.0, "labor": 0.0},
        "mortar": {"material": 280.0, "labor": 0.0},
        "wallpaper": {"material": 1200.0, "labor": 0.0},
        "laminate": {"material": 900.0, "labor": 0.0},
        "tile": {"material": 1500.0, "labor": 0.0},
        "stretchCeiling": {"material": 600.0, "labor": 0.0},
        "cable": {"material": 60.0, "labor": 0.0},
        "socket": {"material": 250.0, "labor": 0.0},
        "pipe": {"material": 120.0, "labor": 0.0},
        "faucet": {"material": 1800.0, "labor": 0.0},
        "interiorDoor": {"material": 9000.0, "labor": 0.0},
        "entranceDoor": {"material": 30000.0, "labor": 0.0}
    }

    updated = False
    success_count = 0
    
    for key, url in CATEGORIES.items():
        print(f"\n📂 Категория '{key}':")
        avg_price = get_avg_price(url)
        
        if avg_price is not None:
            # === ПОПРАВКИ НА ЕДИНИЦЫ ИЗМЕРЕНИЯ ===
            if key == "wall":
                avg_price = avg_price / 2.5           # цена за поддон → за м³
            elif key == "roof":
                avg_price = avg_price / 2.5           # цена за лист → за м²
            elif key == "foundation":
                avg_price = avg_price * 11.7          # цена за пог.м → за хлыст 11.7м
            elif key == "rebar12":
                avg_price = avg_price                 # уже за пог.м (оставляем)
            elif key == "rebar8":
                avg_price = avg_price                 # уже за пог.м
            elif key == "concrete":
                avg_price = avg_price * 4             # цена за мешок/упаковку → за м³
            elif key == "glue":
                avg_price = avg_price                 # уже за мешок 25кг
            elif key == "mortar":
                avg_price = avg_price * 20            # за мешок 25кг → за м³
            elif key == "finish":
                avg_price = avg_price / 10.5          # цена за рулон → за м²
            elif key == "wallpaper":
                avg_price = avg_price / 10.5          # цена за рулон → за м²
            elif key == "laminate":
                avg_price = avg_price                 # уже за м²
            elif key == "tile":
                avg_price = avg_price                 # уже за м²
            elif key == "stretchCeiling":
                avg_price = avg_price                 # уже за м²
            elif key == "cable":
                avg_price = avg_price                 # уже за пог.м
            elif key == "socket":
                avg_price = avg_price                 # уже за шт
            elif key == "pipe":
                avg_price = avg_price                 # уже за пог.м
            elif key == "faucet":
                avg_price = avg_price                 # уже за шт
            elif key == "interiorDoor":
                avg_price = avg_price                 # уже за шт
            elif key == "entranceDoor":
                avg_price = avg_price                 # уже за шт
            # =============================================
            
            avg_price = round(avg_price)
            prices_data[key]["material"] = avg_price
            updated = True
            success_count += 1
            print(f"   ✅ Успех! Базовая цена: {avg_price} ₽")
        else:
            print(f"   ⚠️ Цены не найдены (оставлено значение-заглушка)")

    print("\n" + "=" * 50)
    print(f"📊 Итого: успешно {success_count} из {len(CATEGORIES)}")
    
    if updated:
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл prices.json успешно создан/обновлён!")
        print("\n📄 Содержимое prices.json:")
        print(json.dumps(prices_data, indent=2, ensure_ascii=False))
    else:
        print("⚠️ Ни одна категория не обновилась.")

if __name__ == "__main__":
    main()

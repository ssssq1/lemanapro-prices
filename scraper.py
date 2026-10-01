import requests
from bs4 import BeautifulSoup
import json
import re

# Ссылки на категории Лемана ПРО
# Добавьте сюда любые нужные вам категории
CATEGORIES = {
    "wall": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/stroitelnye-materialy/stenovye-bloki/gazobeton/",
    "roof": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/krovlya-i-fasad/krovlya/metallocherepitsa/",
    "finish": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/otdelochnye-materialy/oboi/",
    "foundation": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/stroitelnye-materialy/armatura/",
    "tiles": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/otdelochnye-materialy/plitka-keramogranit/plitka-keramicheskaya/",
    "paint": "https://lemanapro.ru/catalog/stroitelstvo-i-remont/otdelochnye-materialy/lakokrasochnye-materialy/kraski/"
}

def get_prices_from_category(url):
    """Заходит на страницу категории и собирает цены первых товаров"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все элементы с data-testid="price-integer" - это стабильный селектор Лемана ПРО
        price_elements = soup.find_all(attrs={"data-testid": "price-integer"})
        
        prices = []
        for el in price_elements:
            # Получаем текст цены (например: "7 687" или "7&nbsp;687")
            price_text = el.get_text(strip=True)
            # Убираем всё кроме цифр
            clean_price = re.sub(r'[^\d]', '', price_text)
            if clean_price:
                prices.append(float(clean_price))
        
        # Берём цены первых 6 товаров и считаем среднее
        if len(prices) >= 3:
            sample = prices[:6]
            return sum(sample) / len(sample)
        elif len(prices) > 0:
            return prices[0]
            
    except Exception as e:
        print(f"❌ Ошибка при парсинге {url}: {e}")
    
    return None

def main():
    print("🔄 Начинаем обновление цен с Лемана ПРО...")
    print("=" * 50)
    
    # Базовые цены-заглушки (будут заменены при успешном парсинге)
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
        print(f"\n Категория '{key}': {url}")
        avg_price = get_prices_from_category(url)
        
        if avg_price is not None:
            avg_price = round(avg_price)
            old_price = prices_data[key]["material"]
            prices_data[key]["material"] = avg_price
            updated = True
            print(f"   ✅ Средняя цена: {avg_price} ₽ (было: {old_price} ₽)")
        else:
            print(f"   ⚠️ Не удалось получить цены, оставлено старое значение")

    print("\n" + "=" * 50)
    
    if updated:
        # Сохраняем в JSON
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл prices.json успешно обновлён!")
    else:
        print("⚠️ Ни одна категория не обновилась.")

if __name__ == "__main__":
    main()

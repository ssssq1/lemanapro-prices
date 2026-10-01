from playwright.sync_api import sync_playwright
import json
import re

# Очищенные и проверенные URL
CATEGORIES = {
    "wall": "https://lemanapro.ru/catalogue/bloki-stroitelnye/gazobetonnyy-blok/",
    "roof": "https://lemanapro.ru/catalogue/metallocherepica/",
    "finish": "https://lemanapro.ru/catalogue/oboi/",
    "foundation": "https://lemanapro.ru/catalogue/armatura/",
    "tiles": "https://lemanapro.ru/catalogue/plitka-keramicheskaya/",
    "paint": "https://lemanapro.ru/catalogue/kraski/"
}

def get_prices_from_category(page, url):
    try:
        print(f"   🌐 Загрузка страницы...")
        # Ждем загрузки DOM, даем 5 секунд на отработку JavaScript с ценами
        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        title = page.title()
        # Проверка на Cloudflare
        if "Just a moment" in title or "Cloudflare" in title or "Проверка безопасности" in title:
            print(f"   ⛔ Обнаружена защита Cloudflare! (Title: {title})")
            return None

        prices = []
        
        # Способ 1: Точный селектор по data-testid
        elements = page.query_selector_all('[data-testid="price-integer"]')
        for el in elements:
            text = el.inner_text().strip()
            clean = re.sub(r'[^\d]', '', text)
            if clean: prices.append(float(clean))

        # Способ 2: Поиск элементов, содержащих знак рубля
        if len(prices) == 0:
            ruble_elements = page.query_selector_all('text="₽"')
            for el in ruble_elements[:30]: # Проверяем первые 30 совпадений
                text = el.inner_text().strip()
                clean = re.sub(r'[^\d]', '', text)
                if clean and len(clean) > 2: # Игнорируем цены типа "0" или "1"
                    prices.append(float(clean))
        
        # Способ 3: Регулярное выражение по всему тексту страницы
        if len(prices) == 0:
            body_text = page.inner_text("body")
            matches = re.findall(r'(\d{1,3}(?:\s\d{3})*)\s*₽', body_text)
            for match in matches[:30]:
                clean = re.sub(r'[^\d]', '', match)
                if clean: prices.append(float(clean))

        # Фильтруем адекватные цены (от 10 до 100 000 рублей), чтобы отсечь мусор
        valid_prices = [p for p in prices if 10 < p < 100000]
        
        if len(valid_prices) >= 3:
            sample = valid_prices[:5] # Берем среднее из первых 5 товаров
            return sum(sample) / len(sample)
        elif len(valid_prices) > 0:
            return valid_prices[0]
            
        print(f"   ⚠️ Страница загрузилась (Title: '{title}'), но цены не найдены.")
        # Для отладки выведем первые 200 символов тела страницы
        # print(f"   DEBUG Body start: {page.inner_text('body')[:200]}")
        return None
        
    except Exception as e:
        print(f"   ❌ Критическая ошибка: {str(e)}")
        return None

def main():
    print("🔄 Начинаем обновление цен (Playwright + Deep Search)...")
    print("=" * 65)
    
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0},
        "tiles": {"material": 900.0, "labor": 0.0},
        "paint": {"material": 400.0, "labor": 0.0}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        updated = False
        success_count = 0
        
        for key, url in CATEGORIES.items():
            print(f"\n📂 Категория '{key}':")
            avg_price = get_prices_from_category(page, url)
            
            if avg_price is not None:
                avg_price = round(avg_price)
                prices_data[key]["material"] = avg_price
                updated = True
                success_count += 1
                print(f"   ✅ Успех! Средняя цена: {avg_price} ₽")
            else:
                print(f"   ❌ Не удалось получить цены")
        
        browser.close()
    
    print("\n" + "=" * 65)
    print(f"📊 Итого: успешно {success_count} из {len(CATEGORIES)}")
    
    if updated:
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл prices.json успешно создан!")
    else:
        print("⚠️ Ни одна категория не обновилась. Файл не создан.")

if __name__ == "__main__":
    main()

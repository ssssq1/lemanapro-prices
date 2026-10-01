from playwright.sync_api import sync_playwright
import json
import re

# Ссылки на категории
CATEGORIES = {
    "wall": "https://lemanapro.ru/catalogue/bloki-stroitelnye/gazobetonnyy-blok/",
    "roof": "https://lemanapro.ru/catalogue/metallocherepica/",
    "finish": "https://rostov.lemanapro.ru/catalogue/oboi-kreaforta/",
    "foundation": "https://lemanapro.ru/catalogue/armatura/",
    "tiles": "https://lemanapro.ru/catalogue/plitka-keramicheskaya/",
    "paint": "https://lemanapro.ru/catalogue/kraski/"
}

def get_prices_from_category(page, url):
    try:
        # Переходим на страницу и ждем полной загрузки JavaScript
        page.goto(url, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(3000)  # Дополнительная пауза для прогрузки цен
        
        prices = []
        
        # Ищем элементы с ценами по стабильному атрибуту
        price_elements = page.query_selector_all('[data-testid="price-integer"]')
        
        for el in price_elements:
            text = el.inner_text()
            clean = re.sub(r'[^\d]', '', text)
            if clean:
                prices.append(float(clean))
        
        # Если не нашли, ищем любой текст с рублем на странице
        if len(prices) == 0:
            all_text = page.inner_text("body")
            matches = re.findall(r'(\d{1,3}(?:\s\d{3})*)\s*₽', all_text)
            for match in matches[:15]: # Берем первые 15 найденных цен
                clean = re.sub(r'[^\d]', '', match)
                if clean:
                    prices.append(float(clean))
        
        # Считаем среднее из первых 5 цен, чтобы избежать акционных "от"
        if len(prices) >= 3:
            sample = prices[:5]
            return sum(sample) / len(sample)
        elif len(prices) > 0:
            return prices[0]
            
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:100]}")
    
    return None

def main():
    print("🔄 Начинаем обновление цен (через невидимый браузер Playwright)...")
    print("=" * 65)
    
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0},
        "tiles": {"material": 900.0, "labor": 0.0},
        "paint": {"material": 400.0, "labor": 0.0}
    }

    # Запускаем невидимый браузер Chrome
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
                print(f"   ⚠️ Не удалось получить цены")
        
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

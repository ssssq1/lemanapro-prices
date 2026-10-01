from playwright.sync_api import sync_playwright
import json
import re

CATEGORIES = {
    "wall": "https://lemanapro.ru/catalogue/bloki-stroitelnye/gazobetonnyy-blok/",
    "roof": "https://lemanapro.ru/catalogue/metallocherepica/",
    "finish": "https://rostov.lemanapro.ru/catalogue/oboi-kreaforta/",
    "foundation": "https://lemanapro.ru/catalogue/armatura/",
    "tiles": "https://lemanapro.ru/catalogue/plitka-keramicheskaya/",
    "paint": "https://lemanapro.ru/catalogue/kraski/"
}

def get_prices_from_category(page, url):
    """Заходит на страницу и собирает цены через настоящий браузер"""
    try:
        page.goto(url, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(3000)  # Ждём загрузки JavaScript
        
        prices = []
        
        # Ищем элементы с ценами
        price_elements = page.query_selector_all('[data-testid="price-integer"]')
        
        for el in price_elements:
            text = el.inner_text()
            clean = re.sub(r'[^\d]', '', text)
            if clean:
                prices.append(float(clean))
        
        # Если не нашли, ищем по тексту с рублём
        if len(prices) == 0:
            all_text = page.inner_text("body")
            matches = re.findall(r'(\d{1,3}(?:\s\d{3})*)\s*₽', all_text)
            for match in matches[:10]:
                clean = re.sub(r'[^\d]', '', match)
                if clean:
                    prices.append(float(clean))
        
        if len(prices) >= 3:
            return sum(prices[:5]) / min(5, len(prices))
        elif len(prices) > 0:
            return prices[0]
            
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:100]}")
    
    return None

def main():
    print("🔄 Начинаем обновление цен с Лемана ПРО (через браузер Playwright)...")
    print("=" * 60)
    
    prices_data = {
        "foundation": {"material": 500.0, "labor": 0.0},
        "wall": {"material": 5500.0, "labor": 0.0},
        "roof": {"material": 800.0, "labor": 0.0},
        "finish": {"material": 1200.0, "labor": 0.0},
        "tiles": {"material": 900.0, "labor": 0.0},
        "paint": {"material": 400.0, "labor": 0.0}
    }

    with sync_playwright() as p:
        # Запускаем браузер в headless режиме (невидимый)
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
                print(f"   ✅ Цена: {avg_price} ₽")
            else:
                print(f"   ⚠️ Не удалось получить")
        
        browser.close()
    
    print("\n" + "=" * 60)
    print(f"📊 Итого: {success_count}/{len(CATEGORIES)} категорий")
    
    if updated:
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(prices_data, f, indent=4, ensure_ascii=False)
        print("✅ prices.json создан!")
    else:
        print("⚠️ Ни одна категория не обновилась")

if __name__ == "__main__":
    main()

        if avg_price is not None:
            # === ПОПРАВКИ НА ЕДИНИЦЫ ИЗМЕРЕНИЯ САЙТА ===
            if key == "wall":
                avg_price = avg_price / 2.5   # Делим на объем поддона, чтобы получить цену за 1 м³
            elif key == "roof":
                avg_price = avg_price / 2.5   # Делим на площадь листа, чтобы получить цену за 1 м²
            elif key == "foundation":
                avg_price = avg_price * 11.7  # Умножаем цену п.м. на длину хлыста (11.7м)
            elif key == "finish":
                avg_price = avg_price / 10.5  # Делим на площадь рулона, чтобы получить цену за 1 м²
            # =============================================
            
            avg_price = round(avg_price)
            prices_data[key]["material"] = avg_price
            updated = True
            success_count += 1
            print(f"   ✅ Успех! Скорректированная цена: {avg_price} ₽")

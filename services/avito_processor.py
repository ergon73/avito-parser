from bs4 import BeautifulSoup
from typing import List
from database.models import Listing
from config.settings import logger
from urllib.parse import urljoin

class AvitoProcessor:
    """Извлекает структурированные данные из HTML-кода страницы Avito."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        # Список стоп-слов для фильтрации объявлений об услугах
        self.stop_words = ['скупка', 'выкуп', 'обмен', 'trade-in', 'трейдин', 'ремонт', 'продажа']

    def process_html(self, html: str) -> List[Listing]:
        """
        Основной метод для парсинга HTML.
        Находит все объявления на странице и извлекает из них данные.
        """
        soup = BeautifulSoup(html, 'lxml')
        listings = []
        
        items_container = soup.find("div", {"data-marker": "catalog-serp"})
        if not items_container:
            logger.warning("Основной контейнер с объявлениями ('catalog-serp') не найден.")
            return []

        items = items_container.find_all("div", {"data-marker": "item"}, recursive=False)
        logger.info(f"Найдено {len(items)} карточек объявлений на странице.")

        for item_soup in items:
            try:
                # Пропускаем рекламные блоки, если они попали в выборку
                if item_soup.find("div", {"data-marker": "promo-item"}):
                    continue
                
                listing = self._parse_item(item_soup)
                if not listing or not listing.url or not listing.title:
                    continue

                # НОВАЯ ЛОГИКА: Фильтрация по стоп-словам в заголовке
                title_lower = listing.title.lower()
                if any(word in title_lower for word in self.stop_words):
                    logger.debug(f"Отфильтровано объявление по стоп-слову: '{listing.title}'")
                    continue
                
                listings.append(listing)

            except Exception as e:
                logger.error(f"Ошибка при обработке карточки объявления: {e}")
        
        return listings

    def _get_text(self, soup: BeautifulSoup, tag: str, attrs: dict) -> str:
        """Безопасно извлекает текст из тега."""
        element = soup.find(tag, attrs)
        if not element:
            return None
        
        if tag == "meta":
            return element.get('content', '').strip()
            
        return element.text.strip()

    def _parse_images(self, item_soup: BeautifulSoup) -> List[str]:
        """
        Извлекает ссылки на изображения из карусели, выбирая самые большие.
        """
        images = []
        # Находим контейнер с фото
        gallery_container = item_soup.find('div', {'data-marker': 'item-photo'})
        if not gallery_container:
            return []
            
        # Находим все теги <img> внутри контейнера
        img_tags = gallery_container.find_all("img")
        
        for img in img_tags[:3]:  # Берем только первые 3 фото, как в уроке
            if 'srcset' in img.attrs and img['srcset']:
                # В srcset ссылки на разные размеры, берем самую последнюю (самую большую)
                # Пример: "... 472w, ... 636w" -> берем "636w"
                srcset = img['srcset']
                parts = srcset.split(',')
                if parts:
                    largest_image_url = parts[-1].strip().split(' ')[0]
                    images.append(largest_image_url)
            elif 'src' in img.attrs:
                 # Если нет srcset, берем src как запасной вариант
                 images.append(img['src'])
                 
        return images

    def _parse_item(self, item_soup: BeautifulSoup) -> Listing:
        """Извлекает данные из одной карточки объявления."""
        
        link_tag = item_soup.find("a", {"data-marker": "item-title"})
        if not link_tag or not link_tag.has_attr('href'):
            return None

        relative_url = link_tag['href']
        absolute_url = urljoin(self.base_url, relative_url)
        
        # Заголовок извлекаем из ссылки (рабочий вариант)
        title = link_tag.get_text(strip=True) if link_tag else None
        price = self._get_text(item_soup, "meta", {"itemprop": "price"})
        
        # Ищем описание в meta теге
        description_meta = item_soup.find("meta", {"itemprop": "description"})
        description = description_meta.get('content', '').strip() if description_meta else None
        
        # ИСПРАВЛЕННЫЙ СЕЛЕКТОР: Ищет конкретный блок с геолокацией, игнорируя дату
        address_div = item_soup.select_one('div[class*="geo-root-"]')
        address = address_div.get_text(strip=True) if address_div else None
        
        # Если адрес не найден через geo-root, пробуем извлечь из URL
        if not address and link_tag and link_tag.has_attr('href'):
            url_parts = link_tag['href'].split('/')
            if len(url_parts) > 1:
                city_from_url = url_parts[1]  # Первая часть после домена
                if city_from_url and city_from_url not in ['all', 'www']:
                    address = city_from_url.replace('_', ' ').title()

        # Парсинг изображений из карусели
        images = self._parse_images(item_soup)

        return Listing(
            url=absolute_url,
            title=title,
            price=price,
            address=address,
            description=description,
            images=images
        )

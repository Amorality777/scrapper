import re
from math import ceil
from os.path import splitext

from core.parse.card import CommonCardParse
from core.parse.page import CommonPageParse
from some_scrapper import SITE_INFO, VALIDATION_FIELDS, BASE_URL
from some_scrapper.services.params import MONTHS, ORGANIZATIONS


class CommonInfo(CommonCardParse):
    scrapper = SITE_INFO['app']

    elements = [{
        'name': 'docs',
        'type': 'single',
        'path': './/div[@class="documents-number"]',
    }, {
        'name': 'page_size',
        'type': 'several',
        'path': './/div[@class="document-search-result"]',
    }]

    def transform_docs(self, value: str) -> None:
        """Обработка значения количества документов.

        Args:
            value (str): Начальное значение поля.

        Errors:
            ValueError: невозможно получить кол-во документов.
        """
        docs = value.split()[0]
        if not docs.isdigit():
            ValueError(f'Получено некорректное значение количества документов: {docs}, ожидается число.')
        self.card_info['docs'] = int(docs)

    def transform_page_size(self, value: list) -> None:
        """Обработка значения количества документов на странице.

        Args:
            value (list): Начальное значение поля.
        """
        self.card_info['page_size'] = len(value)

    def append_custom_attributes(self):
        """Добавление кастомных атрибутов, которых нет на сайте.

        Вычисление количества страниц.
        """
        self.card_info['pages'] = ceil(self.card_info.get('docs', 0) / self.card_info.get('page_size', 1))


class PageParser(CommonPageParse):
    replace_text = ('',)
    scrapper = SITE_INFO['app']
    validation_fields = VALIDATION_FIELDS
    path = '//div[@class="document-search-result"]'
    elements = [{
        'name': 'title',
        'path': './/a[@class="document-title"]',
        'type': 'simple'
    }, {
        'name': 'link',
        'path': './/a[@class="document-title"]/@href',
        'type': 'simple'
    }, {
        'name': 'attach_link',
        'path': './/a[@class="document-download"]/@href',
        'type': 'simple'
    }]

    def transform_link(self, value: str):
        """Формирование абсолютной ссылки на документ.

        Args:
            value: Начальное значение.
        """
        self.card_info['link'] = BASE_URL + value

    def transform_attach_link(self, value: str):
        """Формирование абсолютной ссылки на вложение.

        Args:
            value: Начальное значение.
        """
        self.card_info['filename'] = value.split('/')[-1]
        self.card_info['extension'] = splitext(self.card_info.get('filename'))[1]

        self.card_info['attach_link'] = BASE_URL + value

    def append_custom_attributes(self):
        """Добавление кастомных атрибутов, которых нет на сайте."""
        value = self.card_info['title']
        for key in ('type', 'number', 'date', 'main', 'organization'):
            if not hasattr(self, f'append_{key}'):
                continue
            self.card_info[key], string = getattr(self, f'append_{key}')(value)
            value = value.replace(string, '').strip()

    @staticmethod
    def append_type(value: str) -> tuple:
        """Добавление типа документа.

        Args:
            value (str): Общая строка поиска.
        """
        return (value.split(maxsplit=1)[0],) * 2

    def append_number(self, value: str) -> tuple:
        """Добавление номера документа.

        Args:
            value (str): Общая строка поиска.
        """
        patt = re.compile(r'(№|No|N)\s?(.+?)(\s|$)')
        res = patt.search(value)
        if res:
            return res.group(2), self.get_find_string(res)
        if self.card_info['type'] == 'Приказ':
            for string in value.split():
                if '/' not in string:
                    continue
                return (string,) * 2
        if self.card_info['type'] == 'СП':
            res = re.search(r'([\d.]+)', value)
            if res:
                return res.group(1), self.get_find_string(res)
        return '', ''

    def append_date(self, value: str) -> tuple:
        """Добавление даты документа.

        Args:
            value (str): Общая строка поиска.
        """
        patt_1 = re.compile(r'о?т?\s?(\d{1,2})\s([а-я]{3,8})\s(\d{4})')  # от 2 декабря 2020 года
        patt_2 = re.compile(r'о?т?\s?(\d{2})\.(\d{2})\.(\d{4})')  # от 02.12.2020
        for patt in (patt_1, patt_2):
            res = patt.search(value)
            if not res:
                continue
            month = MONTHS.get(res.group(2).lower(), res.group(2))
            string = self.get_find_string(res)
            for year in (' г.', ' года'):
                if year not in value:
                    continue
                string = string + year
                break
            if isinstance(month, int) or month.isdigit():
                return f'{int(res.group(1)):02d}.{int(month):02d}.{res.group(3)}', string
            return f'{int(res.group(1))} {month} {res.group(3)}', string
        return '', ''

    def append_main(self, value: str) -> tuple:
        """Добавление принявших органов документа.

        Args:
            value (str): Общая строка поиска.
        """
        res = re.search(r'к (СП [\d.]+)', value)
        if not res:
            return '', ''
        return res.group(1), self.get_find_string(res)

    @staticmethod
    def append_organization(value: str) -> tuple:
        """Добавление принявших органов документа.

        Args:
            value (str): Общая строка поиска.
        """
        result = set()
        for key, new_value in ORGANIZATIONS.items():
            if key in value:
                result.add(new_value)
        return list(result), ''

    @staticmethod
    def get_find_string(res: re.match) -> str:
        """Получение искомой строки.

        Args:
            res (re.match): Результат поиска.
        """
        return res.string[res.regs[0][0]: res.regs[0][1]]

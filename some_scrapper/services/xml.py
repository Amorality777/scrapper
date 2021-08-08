from core.xml_converter import XmlCompiled
from some_scrapper import SITE_INFO


class XmlServices(XmlCompiled):
    parser_name = SITE_INFO['app']

    def get_default_xml_tag(self) -> dict:
        """Получение списка атрибутов."""
        return {
            'title': {
                'attr': 1,
                'name': 'title'
            },
            'type': {
                'attr': 4,
                'name': 'type'
            },
            'number': {
                'attr': 6,
                'name': 'number'
            },
            'date': {
                'attr': 7,
                'name': 'date'
            },
            'organization': {
                'attr': 5,
                'name': 'organization'
            },
            'main': {
                'rule_name': 'main'
            }
        }

    def get_link(self):
        """Получение URL-а карточки."""
        return self.data['link']

    def append_attachment(self) -> None:
        """Добавление в xml объект конвертора вложение из временного хранилища."""
        value_xml = {
            'b64encode': False,
            'name': 'file',
            'type': 8,
            'filename': self.data.get('filename', ''),
            'extension': self.data.get('extension', ''),
            'size': self.data.get('size', ''),
        }
        self.convert_obj.add(self.data['file'], value_xml)

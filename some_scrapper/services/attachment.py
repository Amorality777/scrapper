import base64

from some_scrapper.services.request import AttachRequest


class ConvertAttach:
    key = 'attach_link'

    @classmethod
    def load_attachment(cls, card_info: dict):
        """Загрузка вложения с конвертацией в base64.

        Args:
            card_info (dict): Информация о документе.
        """
        if not card_info.get(cls.key):
            return
        grab_obj = AttachRequest.execute(card_info.get(cls.key))
        card_info['file'] = base64.b64encode(grab_obj.get_binary()).decode('utf-8')
        card_info['size'] = grab_obj.get_download_size()

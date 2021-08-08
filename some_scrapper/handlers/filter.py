from core.handler.filter import BaseFilterHandler


class FilterHandler(BaseFilterHandler):
    scip_types = ('Приказ', 'Письмо', 'СП', 'Изменение')

    def check_is_skip_card(self, card_info: dict) -> bool:
        """
        Проверка на пропуск карточки.

        Args:
            card_info: Информации о карточке
        """
        return bool(card_info.get('type') in self.scip_types)

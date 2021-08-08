import json
import warnings
from unittest import TestCase
from unittest.mock import Mock, patch
from itertools import product

from core.tests.helpers import TestSource
from some_scrapper import SITE_INFO
from some_scrapper.tasks import load_page
from project_name.settings import BASE_DIR


@patch('some_scrapper.services.process.Process.set_status', Mock())
@patch('some_scrapper.services.process.Process.set_count', Mock())
class TestLoadPage(TestCase):
    fields = ('title', 'link', 'attach_link', 'filename', 'extension', 'number', 'date', 'main', 'organization')

    def setup_class(self) -> None:
        self.grab_obj = TestSource.load_file(SITE_INFO['app'], 'grab_service', 'page.html')
        with open(f'{BASE_DIR}/some_scrapper/tests/sources/data.json', 'r') as f:
            self.data = json.loads(f.read())

    @patch('some_scrapper.services.process.Process.failure_or_kill', Mock(return_value=False))
    @patch('some_scrapper.services.request.PageRequest.execute')
    def test_correct_info(self, execute):
        execute.return_value = self.grab_obj
        card_list = load_page(page=1)
        for data, field in product(zip(card_list, self.data), self.fields):
            card_info, result = data
            try:
                if isinstance(card_info[field], list):
                    self.assertListEqual(sorted(card_info[field]), sorted(result[field]))
                else:
                    self.assertEqual(card_info[field], result[field])
            except AssertionError as exc:
                warnings.warn(f'Ошибка в поле: {field} \nКарточка в data.json: {result}\n{card_info}')
                raise exc
        for card_info in card_list:
            self.assertTrue(card_info.get('validation_hash'))

    @patch('some_scrapper.services.process.Process.failure_or_kill', Mock(return_value=False))
    @patch('some_scrapper.services.request.PageRequest.execute')
    def test_validation_hash(self, execute):
        execute.return_value = self.grab_obj
        card_list = load_page(page=1)

        for card_info in card_list:
            self.assertTrue(card_info.get('validation_hash'))

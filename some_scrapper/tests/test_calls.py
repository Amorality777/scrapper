from unittest import TestCase
from unittest.mock import Mock, patch

from core.tests.helpers import TestSource
from some_scrapper import SITE_INFO
from some_scrapper.tasks import init_search, load_page, collect_cards


@patch('some_scrapper.services.process.Process.set_status', Mock())
@patch('some_scrapper.services.process.Process.set_count', Mock())
@patch('some_scrapper.services.process.Process.failure_or_kill', Mock(return_value=False))
class TestCountDocs(TestCase):
    fields = ('title', 'link', 'attach_link', 'filename', 'extension', 'number', 'date', 'main', 'organization')

    def setUp(self) -> None:
        self.grab_obj = TestSource.load_file(SITE_INFO['app'], 'grab_service', 'page.html')

    @patch('some_scrapper.services.request.PageRequest.execute')
    @patch('some_scrapper.tasks.load_page.s')
    @patch('some_scrapper.tasks.collect_cards.s')
    def test_count_pages(self, collect_cards, _load_page, execute):
        execute.return_value = self.grab_obj
        init_search()
        self.assertEqual(_load_page.call_count, 24)
        self.assertEqual(collect_cards.call_count, 1)

    @patch('some_scrapper.services.request.PageRequest.execute')
    def test_count_cards(self, execute):
        execute.return_value = self.grab_obj
        card_list = load_page(page=1)
        self.assertEqual(len(card_list), 59)

    @patch('some_scrapper.tasks.save_doc.s')
    @patch('some_scrapper.tasks.create_archive.si')
    def test_count_docs(self, create_archive, save_doc):
        card_lists = [[1, 2, 3, 4, 5], [6, 7, 8, 9]]
        collect_cards(card_lists)
        self.assertEqual(save_doc.call_count, 9)
        self.assertEqual(create_archive.call_count, 1)

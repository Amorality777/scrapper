from unittest import TestCase

from core.tests.helpers import TestSource
from some_scrapper import SITE_INFO
from some_scrapper.services.parser import CommonInfo


class TestCommonInfo(TestCase):
    def test_run(self):
        grab_obj = TestSource.load_file(SITE_INFO['app'], 'grab_service', 'page.html')
        info = CommonInfo.collect('', {}, grab_obj.doc)
        self.assertEqual(info['docs'], 1839)
        self.assertEqual(info['pages'], 24)

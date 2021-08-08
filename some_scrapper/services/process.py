from core.services.process import BaseProcess
from some_scrapper import SITE_INFO


class Process(BaseProcess):
    scrapper = SITE_INFO['app']

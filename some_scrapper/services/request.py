from core.proxy import PERSONAL_PROXY
from core.services.request import GrabRequest
from some_scrapper import SITE_INFO


class PageRequest(GrabRequest):
    scrapper = SITE_INFO['app']


class AttachRequest(PageRequest):
    proxy_name = PERSONAL_PROXY[0]
    timeout = 60 * 10

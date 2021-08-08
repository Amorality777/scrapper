from core.views.actives import BaseActivesView
from core.views.archives import BaseArchivesView
from core.views.recurring import BaseRecurringView
from some_scrapper import SITE_INFO
from users.views.lists import BaseUsersListsView


class IndexView(BaseActivesView):
    site_info = SITE_INFO


class ArchivesView(BaseArchivesView):
    site_info = SITE_INFO


class RecurringView(BaseRecurringView):
    site_info = SITE_INFO


class UsersView(BaseUsersListsView):
    site_info = SITE_INFO

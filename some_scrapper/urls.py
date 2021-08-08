from django.urls import path

from some_scrapper.views import IndexView, ArchivesView, RecurringView, UsersView

app_name = "some_scrapper"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('archives/', ArchivesView.as_view(), name='archives'),
    path('recurrings/', RecurringView.as_view(), name='recurrings'),
    path('users/', UsersView.as_view(), name='users'),
]

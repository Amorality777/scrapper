from itertools import chain

from celery import chord

from core.exceptions import DEFAULT_ERROR
from core.models.periodic_tasks import PeriodicTask
from core.services.tasks import BaseTask, ExecutePrepareTasks
from core.tasks import create_archive
from some_scrapper import SITE_INFO, SEARCH_URL
from some_scrapper.handlers.filter import FilterHandler
from some_scrapper.models import Complete
from some_scrapper.services.attachment import ConvertAttach
from some_scrapper.services.parser import CommonInfo, PageParser
from some_scrapper.services.process import Process
from some_scrapper.services.request import PageRequest
from some_scrapper.services.xml import XmlServices
from project_name.celeryapp import app


class SomeScrapperTask(BaseTask):
    scrapper = SITE_INFO['app']

    @property
    def process_obj(self):
        """Получение объекта процесса."""
        return Process(self)

    errors_stages = {
        f'{scrapper}.tasks.init_search': 'error_init',
        f'{scrapper}.tasks.load_page': 'error_page',
        f'{scrapper}.tasks.collect_cards': 'error_card',
        f'{scrapper}.tasks.save_doc': 'error_doc',
    }


class SomeScrapperPrepareTasks(ExecutePrepareTasks):
    scrapper = SITE_INFO['app']
    task_path = "tasks"

    @staticmethod
    def get_info() -> dict:
        """Формирование информации о процессе на основании поисковых параметров."""
        return {'_description_': 'Периодический поиск новых документов.'}


@app.task(base=SomeScrapperTask, bind=True, ignore_result=True)
def prepare_search(self, search_params: dict, options: dict) -> None:
    """Подготовка запроса к поиску на сайте.

    Args:
        self: Аргумент задачи.
        search_params (dict): Поисковые параметры.
        options (dict): Опции.
    """
    SomeScrapperPrepareTasks.prepare_search(self, search_params, options)


@app.task(base=SomeScrapperTask, ignore_result=True, bind=True, autoretry_for=DEFAULT_ERROR,
          retry_kwargs={'max_retries': 20, 'countdown': 30})
def init_search(self, *args, **kwargs) -> None:
    """Поиск страниц со списком документов.

    Args:
        self: Аргумент задачи.
        args: Позиционные аргументы.
        kwargs: Именованные аргументы.

    """
    if self.process_obj.failure_or_kill():
        create_archive.delay(scrapper=self.scrapper)
        return
    self.process_obj.set_init_status()
    grab_obj = PageRequest.execute(SEARCH_URL).get_doc()
    info = CommonInfo.collect(SEARCH_URL, {}, grab_obj)
    self.process_obj.set_count('find_page', info['pages'])
    self.process_obj.set_count('find_card', info['docs'])

    tasks = [load_page.s(page=page) for page in range(1, info['pages'] + 1)]
    chord(tasks, collect_cards.s())()


@app.task(base=SomeScrapperTask, ignore_result=True, bind=True, autoretry_for=DEFAULT_ERROR,
          retry_kwargs={'max_retries': 20, 'countdown': 30})
def load_page(self, page: int) -> list:
    """Загрузка карточек на странице.

    Args:
        self: Аргумент задачи.
        page (int): Номер страницы.
    """
    if self.process_obj.failure_or_kill():
        create_archive.delay(scrapper=self.scrapper)
        return []

    self.process_obj.set_page_status()
    url = f'{SEARCH_URL}{page}'
    grab_obj = PageRequest.execute(url).get_doc()
    card_list = PageParser.collect_card(grab_obj)
    filter_obj = FilterHandler(card_list)
    filter_obj.filter_card()
    self.process_obj.set_count('skip_card', filter_obj.skip_card_count)
    self.process_obj.set_count('save_card', filter_obj.cards_success_count)
    self.process_obj.set_count('find_doc', filter_obj.cards_success_count)
    self.process_obj.set_count('save_page')
    return filter_obj.cards_success_list


@app.task(base=SomeScrapperTask, ignore_result=True, bind=True, autoretry_for=DEFAULT_ERROR,
          retry_kwargs={'max_retries': 20, 'countdown': 30})
def collect_cards(self, card_lists: list) -> None:
    """Обработка всех полученных документов.

    Args:
        self: Аргумент задачи.
        card_lists (list): Список документов.
    """
    if self.process_obj.failure_or_kill():
        create_archive.delay(scrapper=self.scrapper)
        return

    self.process_obj.set_doc_status()
    tasks = [save_doc.s(card_info) for card_info in chain.from_iterable(card_lists)]
    chord(tasks, create_archive.si(scrapper=self.scrapper))()


@app.task(base=SomeScrapperTask, ignore_result=True, bind=True, autoretry_for=DEFAULT_ERROR,
          retry_kwargs={'max_retries': 30, 'countdown': 20})
def save_doc(self, card_info: dict):
    """Сохранение документа.

    Args:
        self: Аргумент задачи.
        card_info (dict): Информация о документе.
    """
    if self.process_obj.failure_or_kill():
        create_archive.delay(scrapper=self.scrapper)
        return

    if Complete.do_validate(card_info):
        self.process_obj.set_count('already_doc')
        return
    ConvertAttach.load_attachment(card_info)
    XmlServices.create_and_save(self.process_obj.get_name(), self.request.id, card_info)
    Complete.create(card_info)
    self.process_obj.set_count('save_doc')


@app.task(base=SomeScrapperTask, bind=True, ignore_result=True)
def prepare_search_new(self) -> None:
    """Периодический поиск обновленных документов.

    Args:
        self: Аргумент задачи.
    """
    prepare_search.apply_async(({}, {}), countdown=3.0, queue='default')
    PeriodicTask.objects.update_last_run(self.name)

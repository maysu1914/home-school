import locale
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from string import Template

from win10toast import ToastNotifier

from app.utils import *


class HomeSchool:
    """
    Alarm when the lesson approaches and ends.
    """
    title = "Ev Okulu"
    notify_near_template = Template("${ders} dersiniz yaklaşıyor. ${baslangic}\nKitaplarınızı hazırlayın.")
    notify_started_template = Template("${ders} dersiniz başladı.")
    notify_finished_template = Template("${ders} dersiniz bitti.")
    on_lesson_template = Template("${ders} (${hoca}) dersiniz devam ediyor.")
    off_lesson_template = Template("Tenefüs vakti. Sonraki ders ${ders} (${hoca}). ${baslangic}")
    no_lesson_template = Template("Bugün başka dersiniz bulunmamaktadır.")
    syllabus_title_template = Template("${tarih} ${gun} ders programı:")
    syllabus_lesson_template = Template("${sayi}. [${baslangic} - ${bitis}] ${ders} (${hoca})")

    def __init__(self, ders_programi_path, language="tr.UTF-8"):
        """
        Set language,
        Read syllabus from JSON file,
        Set day name,
        Set alarm times,
        Set lesson clocks,
        :param ders_programi_path: JSON file path of the syllabus
        """
        locale.setlocale(locale.LC_ALL, language)
        self.toaster = ToastNotifier()
        # self.executor = ThreadPoolExecutor()

        self.interval = 0.5
        self.notification_duration = 30

        self.today = datetime.datetime.today()
        self.day_name = self.today.strftime("%A")
        self.ders_programi = self.get_today_syllabus(ders_programi_path)
        self.last_lesson_time = max([value['bitis'] for key, value in self.ders_programi.items()])

        self.last_lesson = {}

        self.set_last_lesson()

        self.show_syllabus()

    def show_syllabus(self):
        print(self.syllabus_title_template.substitute({'gun': self.day_name, 'tarih': self.today.strftime("%d/%m/%Y")}))
        for sayi, lesson in self.ders_programi.items():
            data = {
                'sayi': sayi,
                'baslangic': lesson['baslangic'].strftime('%H:%M'),
                'bitis': lesson['bitis'].strftime('%H:%M'),
                'ders': lesson['ders'],
                'hoca': lesson['hoca'],
            }
            print(self.syllabus_lesson_template.substitute(data))
        print('-' * 40)

    def get_today_syllabus(self, ders_programi_path):
        syllabus = get_dict_from_json_file(ders_programi_path)[self.day_name]
        for key, value in syllabus.items():
            start = get_updated_now_by_given_date(value['baslangic'], '%H:%M')
            finish = get_updated_now_by_given_date(value['bitis'], '%H:%M')
            syllabus[key]['baslangic'] = start
            syllabus[key]['bitis'] = finish
            syllabus[key]['durum'] = 'pending'  # pending, near, started, finished
        return syllabus

    def set_last_lesson(self):
        """
        sets the last lesson data to individual variable
        :return:
        """
        for key, value in self.ders_programi.items():
            if value['baslangic'] < datetime.datetime.now() < value['bitis']:
                self.ders_programi[key]['durum'] = 'started'
                self.last_lesson = value
                break

    def get_next_lesson(self):
        """
        returns the next lesson data if exist
        :return:
        """
        for key, value in self.ders_programi.items():
            if datetime.datetime.now() < value['baslangic']:
                return value
        return None

    def run(self):
        """
        Loop until the last lesson is finished.
        :return:
        """
        if not datetime.datetime.now() > self.last_lesson_time:
            threading.Timer(self.interval, self.run).start()
            self.start()

    def start(self):
        """
        Logic processes
        :return:
        """
        self.notification_control()
        self.lesson_control()

    def notification_control(self):
        """
        Check alarm conditions
        :return:
        """
        for key, value in self.ders_programi.items():
            if value['durum'] == 'pending':
                before_start = value['baslangic'] - datetime.timedelta(0, 0, 0, 0, 3)
                if before_start < datetime.datetime.now() < value['baslangic']:
                    self.ders_programi[key]['durum'] = 'near'
                    self.send_notification(value['durum'], lesson=value)
            elif value['durum'] == 'near':
                time_difference = abs((datetime.datetime.now() - value['baslangic']).total_seconds())
                if time_difference < 2:
                    self.ders_programi[key]['durum'] = 'started'
                    self.last_lesson = value
                    self.send_notification(value['durum'])
            elif value['durum'] == 'started':
                time_difference = abs((datetime.datetime.now() - value['bitis']).total_seconds())
                if time_difference < 2:
                    self.ders_programi[key]['durum'] = 'finished'
                    self.last_lesson = value
                    self.send_notification(value['durum'])

    def lesson_control(self):
        """
        Check lesson conditions
        :return:
        """
        if self.last_lesson:
            if self.last_lesson['baslangic'] < datetime.datetime.now() < self.last_lesson['bitis']:
                self.on_lesson()
                return
        self.off_lesson()
        return

    def send_notification(self, msg_type, lesson=None):
        """
        Sends notification
        :param lesson:
        :param msg_type: Alarm type
        :return:
        """
        if lesson:
            data = {'ders': lesson['ders'], 'baslangic': lesson['baslangic'].strftime('%H:%M')}
        else:
            data = {'ders': self.last_lesson['ders'], 'baslangic': self.last_lesson['baslangic'].strftime('%H:%M')}

        toast_messages = {'near': self.notify_near_template.substitute(data),
                          'started': self.notify_started_template.substitute(data),
                          'finished': self.notify_finished_template.substitute(data)}

        # we don't use built-in threaded parameter of toaster,
        # because it has protection to multi notification at in the same time
        # thus we create our own thread
        self.toaster._show_toast(title=self.title, msg=toast_messages[msg_type],
                                 duration=self.notification_duration, icon_path=None)

    def on_lesson(self):
        """
        Do something when the lesson is ongoing.
        :return:
        """
        trigger_process = 'CptHost.exe'  # Zoom meeting exe
        processes_to_kill = ['firefox.exe']

        if self.last_lesson:
            data = {'ders': self.last_lesson['ders'], 'hoca': self.last_lesson['hoca']}
            print(self.on_lesson_template.safe_substitute(data))

        kill_process(processes_to_kill, trigger_process)

    def off_lesson(self):
        """
        Do something when no lesson.
        :return:
        """
        next_lesson = self.get_next_lesson()
        if next_lesson:
            data = {'ders': next_lesson['ders'], 'hoca': next_lesson['hoca'],
                    'baslangic': next_lesson['baslangic'].time()}
            print(self.off_lesson_template.safe_substitute(data))
        else:
            print(self.no_lesson_template.safe_substitute())

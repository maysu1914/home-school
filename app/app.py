import locale
import threading
from concurrent.futures.thread import ThreadPoolExecutor

from win10toast import ToastNotifier

from app.utils import *


class HomeSchool:
    """
    Alarm when the lesson approaches and ends.
    """
    title = "Ev Okulu"

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
        self.today = datetime.datetime.today().strftime("%A")
        self.toaster = ToastNotifier()
        self.interval = 0.5
        self.notification_duration = 30
        self.ders_programi = self.get_today_syllabus(ders_programi_path)
        self.last_lesson_time = max([value['bitis'] for key, value in self.ders_programi.items()])

        self.last_lesson = {}
        self.wmi_thread = None

        self.set_last_lesson()

    def get_today_syllabus(self, ders_programi_path):
        syllabus = get_dict_from_json_file(ders_programi_path)[self.today]
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
        prev_lesson = {}
        for key, value in self.ders_programi.items():
            if value['baslangic'] < datetime.datetime.now() < value['bitis']:
                self.ders_programi[key]['durum'] = 'started'
                self.last_lesson = value
                break
            elif prev_lesson and datetime.datetime.now() > prev_lesson['bitis']:
                self.last_lesson = prev_lesson
            prev_lesson = value

    def get_next_lesson(self):
        """
        returns the next lesson data if exist
        :return:
        """
        if self.last_lesson:
            next_lesson_id = str(self.last_lesson['id'] + 1)
            if next_lesson_id in self.ders_programi:
                return self.ders_programi[next_lesson_id]
            else:
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
        self.alarm_control()
        self.lesson_control()

    def alarm_control(self):
        """
        Check alarm conditions
        :return:
        """
        for key, value in self.ders_programi.items():
            if value['durum'] == 'pending':
                before_start = value['baslangic'] - datetime.timedelta(0, 0, 0, 0, 3)
                if before_start < datetime.datetime.now() < value['baslangic']:
                    self.ders_programi[key]['durum'] = 'near'
                    self.call_alarm(value['durum'], lesson=value)
            elif value['durum'] == 'near':
                time_difference = abs((datetime.datetime.now() - value['baslangic']).total_seconds())
                if time_difference < 2:
                    self.ders_programi[key]['durum'] = 'started'
                    self.last_lesson = value
                    self.call_alarm(value['durum'])
            elif value['durum'] == 'started':
                time_difference = abs((datetime.datetime.now() - value['bitis']).total_seconds())
                if time_difference < 2:
                    self.ders_programi[key]['durum'] = 'finished'
                    self.last_lesson = value
                    self.call_alarm(value['durum'])

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

    def call_alarm(self, type, lesson=None):
        """
        Calling alarm
        :param lesson:
        :param type: Alarm type
        :return:
        """
        # we don't use built-in threaded paramter of toaster,
        # because it has protection to multi notification in the same time
        if type == 'near':
            ThreadPoolExecutor().submit(self.toaster._show_toast, title=self.title,
                                        msg="%s dersiniz yaklaşıyor. %s\nKitaplarınızı hazırlayın." % (
                                            lesson['ders'], lesson['baslangic'].strftime('%H:%M')),
                                        duration=self.notification_duration, icon_path=None)
        elif type == 'started':
            ThreadPoolExecutor().submit(self.toaster._show_toast, title=self.title,
                                        msg="%s dersiniz başladı." % self.last_lesson['ders'],
                                        duration=self.notification_duration, icon_path=None)
        else:
            ThreadPoolExecutor().submit(self.toaster._show_toast, title=self.title,
                                        msg="%s dersiniz bitti." % self.last_lesson['ders'],
                                        duration=self.notification_duration, icon_path=None)

    def on_lesson(self):
        """
        Do something when the lesson is ongoing.
        :return:
        """
        print('on lesson')
        trigger_process = 'CptHost.exe'  # Zoom meeting exe
        processes_to_kill = ['firefox.exe']
        if not self.wmi_thread:
            self.wmi_thread = ThreadPoolExecutor().submit(kill_process, processes_to_kill, trigger_process)
        elif not self.wmi_thread.running():
            self.wmi_thread = None

    def off_lesson(self):
        """
        Do something when no lesson.
        :return:
        """
        next_lesson = self.get_next_lesson()
        print('out lesson', next_lesson['ders'] if next_lesson else 'There no upcoming lesson')

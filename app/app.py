import datetime
import locale
import threading
from concurrent.futures.thread import ThreadPoolExecutor

import vlc
from win10toast import ToastNotifier

from app.utils import *


class HomeSchool:
    """
    Alarm when the lesson approaches and ends.
    """
    title = "Home School"

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
        self.alarm_path = "resources/meb_okul_zili.mp3"
        self.toaster = ToastNotifier()
        self.ders_programi = get_dict_from_json_file(ders_programi_path)
        self.today = datetime.datetime.today().strftime("%A")
        self.alarms = []
        self.lesson_times = []
        self.set_alarms()
        self.set_lesson_times()
        self.interval = 0.5
        self.wmi_thread = None

    def set_alarms(self):
        """
        Read lesson clocks from syllabus,
        set alarms 3 min before to lesson starts,
        and lesson ends.
        :return:
        """
        for key, value in self.ders_programi[self.today].items():
            start = get_updated_now_by_given_date(value['baslangic'], '%H:%M')
            before_start = start - datetime.timedelta(0, 0, 0, 0, 3)
            finish = get_updated_now_by_given_date(value['bitis'], '%H:%M')
            self.alarms.append({'type': 'before_start', 'lesson': key, 'time': before_start, 'status': False})
            self.alarms.append({'type': 'start', 'lesson': key, 'time': start, 'status': False})
            self.alarms.append({'type': 'finish', 'lesson': key, 'time': finish, 'status': False})

    def set_lesson_times(self):
        """
        Set lesson clocks for future usage,
        do something while the lesson continues.
        :return:
        """
        for key, value in self.ders_programi[self.today].items():
            start = get_updated_now_by_given_date(value['baslangic'], '%H:%M')
            finish = get_updated_now_by_given_date(value['bitis'], '%H:%M')
            self.lesson_times.append((start, finish))

    def run(self):
        """
        Loop until the last lesson is finished.
        :return:
        """
        if not datetime.datetime.now() > self.alarms[-1]['time']:
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
        for index, alarm in zip(range(len(self.alarms)), self.alarms):
            if not alarm['status']:
                # try to call alarm before 2 seconds or in 2 seconds
                time_difference = abs((datetime.datetime.now() - alarm['time']).total_seconds())
                if time_difference < 2:
                    self.alarms[index]['status'] = True
                    self.call_alarm(self.ders_programi[self.today][alarm['lesson']], alarm['type'])

    def lesson_control(self):
        """
        Check lesson conditions
        :return:
        """
        for index, lesson_time in zip(range(1, len(self.lesson_times) + 1), self.lesson_times):
            if lesson_time[0] < datetime.datetime.now() < lesson_time[1]:
                # print(self.ders_programi[self.today][str(index)])
                self.on_lesson()
                return
        self.off_lesson()
        return

    def call_alarm(self, lesson, type):
        """
        Calling alarm
        :param type: Alarm type
        :param lesson: Data of trigger lesson from syllabus
        :return:
        """
        vlc.MediaPlayer(self.alarm_path).play()
        if type == 'before_start':
            self.toaster.show_toast(title=self.title,
                                    msg="%s dersiniz yaklaşıyor. %s\nKitaplarınızı hazırlayın." % (
                                        lesson['ders'], lesson['baslangic']),
                                    duration=120, threaded=True)
        elif type == 'start':
            self.toaster.show_toast(title=self.title,
                                    msg="%s dersiniz başladı." % (lesson['ders']),
                                    duration=60, threaded=True)
        else:
            self.toaster.show_toast(title=self.title,
                                    msg="%s dersiniz bitti. %s" % (lesson['ders'], lesson['bitis']),
                                    duration=60, threaded=True)

    def on_lesson(self):
        """
        Do something when the lesson is ongoing.
        :return:
        """
        # print('on lesson')
        trigger_process = 'CptHost.exe'  # Zoom meeting exe
        processes_to_kill = ['firefox.exe', 'chrome.exe', 'msedge.exe']
        if not self.wmi_thread:
            self.wmi_thread = ThreadPoolExecutor().submit(kill_process, processes_to_kill, trigger_process)
        elif not self.wmi_thread.running():
            self.wmi_thread = None

    def off_lesson(self):
        """
        Do something when no lesson.
        :return:
        """
        # print('out lesson')
        processes = {}  # process name and path
        if not self.wmi_thread:
            self.wmi_thread = ThreadPoolExecutor().submit(start_process, processes)
        elif not self.wmi_thread.running():
            self.wmi_thread = None

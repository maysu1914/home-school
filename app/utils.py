import datetime
import json

import pythoncom
import win32con
import wmi


def get_dict_from_json_file(path):
    """
    Read JSON file
    :param path:
    :return:
    """
    with open(path, encoding="UTF-8") as json_file:
        data = json.load(json_file)
    return data


def get_updated_now_by_given_date(given_string_values, values_format):
    """
    This function is update the now date with given date string and format,
    but it is work big to low idea, it means, if user gave only hour data,
    and format, then, minutes, seconds and milliseconds will be zero while,
    year, month, and day remains same. If user gave year and month; year,
    and month will change to user data, lower datas (day, hour, min etc),
    will be zero (reset)
    :param given_string_values: date string ("12:10") ("2020060910")
    :param values_format: date format ("%H:%M") ("%Y%m%d%H%M")
    :return: updated date object (datetime.datetime(2021, 3, 3, 12, 10))
    """
    # possible options: Year(2020,21), Month(01,Jan,January), Hour(22,10 pm)
    options = ['%Y%y', '%m%b%B', '%d', '%H%I', '%p', '%M', '%S', '%f']
    for _format in values_format.split('%'):
        if _format:
            for index, option in zip(range(len(options)), options):
                check_format = '%' + _format[0]
                if check_format in option:
                    options[index] = check_format
    options = ''.join(options)

    for _format in ''.join(values_format.split('%'))[::-1]:
        if _format:
            check_format = '%' + _format[0]
            if check_format in options:
                options = options.replace(options[options.index(check_format):], '')

    str_now = datetime.datetime.now().strftime(options)
    updated_date = datetime.datetime.strptime(given_string_values + str_now, values_format + options)
    return updated_date


def kill_process(processes_to_kill, trigger_process=None):
    """
    A process killer. It takes 1 required and 1 optional argument.
    Processes to kill is a must and should be a list.
    The trigger process is optional, when it exists the whole operation depends on it.
    :param processes_to_kill:
    :param trigger_process:
    :return:
    """
    killed = []
    not_killed = []

    # Initializing the wmi constructor
    pythoncom.CoInitialize()
    f = wmi.WMI()
    if trigger_process and not f.Win32_Process(Name=trigger_process):
        print("'%s' trigger process not found." % trigger_process)
        return

    for process_to_kill in processes_to_kill:
        # Iterating through all the running processes
        for process in f.Win32_Process(Name=process_to_kill):
            process.Terminate()
            killed.append(process.Name)

    if killed:
        print('Processes killed: %s' % (', '.join(killed)))
    else:
        print('No processes killed.')

    return


def start_process(processes_to_start):
    # Initializing the wmi constructor
    pythoncom.CoInitialize()
    f = wmi.WMI()

    for process, path in processes_to_start.items():
        if not f.Win32_Process(Name=process):
            process_startup = f.Win32_ProcessStartup.new(ShowWindow=win32con.SW_SHOWNORMAL)
            process_id, result = f.Win32_Process.Create(
                CommandLine=path,
                ProcessStartupInformation=process_startup
            )
            if result == 0:
                print("Process started successfully: %d" % process_id)
            else:
                print("Problem creating process: %d" % result)
        else:
            print('%s is already running.' % process)
    return

import datetime
import json

import pythoncom
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


def kill_process(processes_to_kill):
    killed = []
    not_killed = []

    # Initializing the wmi constructor
    pythoncom.CoInitialize()
    f = wmi.WMI()

    for process_to_kill in processes_to_kill:
        # Iterating through all the running processes
        for process in f.Win32_Process(Name=process_to_kill):
            process.Terminate()
            killed.append(process.Name)

    if killed:
        return 'Processes killed: %s' % (', '.join(killed))
    else:
        return 'No process killed.'

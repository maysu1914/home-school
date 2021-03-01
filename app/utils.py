import json


def get_dict_from_json_file(path):
    """
    Read JSON file
    :param path:
    :return:
    """
    with open(path, encoding="UTF-8") as json_file:
        data = json.load(json_file)
    return data

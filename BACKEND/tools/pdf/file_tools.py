import json


def file_write(path, content):

    with open(path, "w", encoding="utf-8") as f:

        if isinstance(content, (dict, list)):
            json.dump(content, f, indent=2, default=str)

        else:
            f.write(content)


def file_read(path):

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
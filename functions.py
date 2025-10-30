import os


def recursively_get_files(path):
    walk_list = os.walk(path)
    file_list = []
    for (root, dirs, files) in walk_list:
        for item in files:
            file_list.append(os.path.join(root, item))
    return file_list

import os


def user_folder(author=None, folder=None):

    destination = os.path.join(os.getenv('UPLOAD_FOLDER')) + '\\' + str(author.get('id')) + '\\'
    if folder is not None:
        destination = destination + folder + '\\'
    if not os.path.exists(destination):
        os.makedirs(destination)
    if not os.path.exists(destination):
        return None
    else:
        return destination


def check_path(author, path):
    destination = os.path.join(os.getenv('UPLOAD_FOLDER')) + '\\' + str(author.get('id')) + '\\'
    if path is not None:
        destination = destination + path
    if not os.path.exists(destination):
        return None, True
    else:
        return destination, not os.path.isfile(destination)


def path_to_dict(path):
    d = {os.path.basename(path): {}}
    if os.path.isdir(path):
        d[os.path.basename(path)]['type'] = "directory"
        d[os.path.basename(path)]['children'] = [path_to_dict(os.path.join(path, x)) for x in os.listdir(path)]
    else:
        d[os.path.basename(path)]['type'] = "file"
    return d

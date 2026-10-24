FOLDERS = {
    "root_a": {"parent": None, "owner_id": "alice"},
    "sub_a": {"parent": "root_a", "owner_id": None},
    "deep_a": {"parent": "sub_a", "owner_id": None},
    "root_b": {"parent": None, "owner_id": "bob"},
}
FILES = {
    "f1": {"folder": "deep_a", "data": "alice-private-data"},
    "f2": {"folder": "root_b", "data": "bob-private-data"},
}


def _file(file_id):
    item = FILES.get(file_id)
    if item is None:
        raise LookupError(file_id)
    return item


def _root_owner(folder_id):
    folder = FOLDERS[folder_id]
    if folder["parent"] is None:
        return folder["owner_id"]
    return _root_owner(folder["parent"])


def _authorize(requester_id, item):
    if _root_owner(item["folder"]) != requester_id:
        raise PermissionError("forbidden")


def get_file(requester_id, file_id):
    item = _file(file_id)
    _authorize(requester_id, item)
    return {"data": item["data"]}


def _ping(n):
    if n <= 0:
        return 0
    return _pong(n - 1) + 1


def _pong(n):
    if n <= 0:
        return 0
    return _ping(n - 1) + 1


def folder_depth(folder_id):
    parent = FOLDERS[folder_id]["parent"]
    if parent is None:
        return 0
    return folder_depth(parent) + 1


def bounce(n):
    return _ping(n)

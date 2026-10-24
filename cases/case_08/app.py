ENTRIES = {
    "e1": {"owner_id": "alice", "label": "diary", "content": "alice-private-entry"},
    "e2": {"owner_id": "bob", "label": "notes", "content": "bob-private-entry"},
    "e3": {"owner_id": None, "label": "draft", "content": "orphan-entry"},
}
USERS = {"alice": {"active": True}, "bob": {"active": True}}


def _fetch(entry_id):
    entry = ENTRIES.get(entry_id)
    if entry is None:
        raise LookupError(entry_id)
    return entry


def open_entry(requester_id, entry_id):
    entry = _fetch(entry_id)
    if not entry.get("owner_id"):
        raise PermissionError("forbidden")
    if requester_id not in USERS or not USERS[requester_id]["active"]:
        raise PermissionError("forbidden")
    return {"label": entry["label"], "content": entry["content"]}


def deactivate(user_id):
    if user_id in USERS:
        USERS[user_id]["active"] = False
    return USERS.get(user_id)


def labels():
    return [entry["label"] for entry in ENTRIES.values()]


def orphan_ids():
    return [entry_id for entry_id, entry in ENTRIES.items() if entry["owner_id"] is None]


def preview(text):
    return text.split("-")[0]

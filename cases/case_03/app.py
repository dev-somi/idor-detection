MESSAGES = {
    "m1": {"owner_id": "alice", "subject": "hello", "text": "alice-private-text"},
    "m2": {"owner_id": "bob", "subject": "lunch", "text": "bob-private-text"},
}
FOLDERS = {"inbox": ["m1", "m2"], "archive": []}


def _lookup(message_id):
    message = MESSAGES.get(message_id)
    if message is None:
        raise LookupError(message_id)
    return message


def _ensure_owner(requester_id, message):
    if message["owner_id"] != requester_id:
        raise PermissionError("forbidden")


def _present(message):
    return {"subject": message["subject"], "text": message["text"]}


def read_message(requester_id, message_id):
    message = _lookup(message_id)
    _ensure_owner(requester_id, message)
    return _present(message)


def move_to_archive(message_id):
    if message_id in FOLDERS["inbox"]:
        FOLDERS["inbox"].remove(message_id)
        FOLDERS["archive"].append(message_id)
    return FOLDERS


def unread_count(folder):
    return len(FOLDERS.get(folder, []))


def subjects():
    return [message["subject"] for message in MESSAGES.values()]


def word_count(text):
    return len([word for word in text.split() if word])

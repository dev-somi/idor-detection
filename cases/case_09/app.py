USERS = {
    "alice": {"org": "acme", "role": "member"},
    "bob": {"org": "acme", "role": "member"},
    "carol": {"org": "globex", "role": "member"},
}
NOTES = {
    "n1": {"owner_id": "alice", "org": "acme", "text": "alice-private-note"},
    "n2": {"owner_id": "carol", "org": "globex", "text": "carol-private-note"},
}


def _note(note_id):
    note = NOTES.get(note_id)
    if note is None:
        raise LookupError(note_id)
    return note


def _can_view(requester_id, note):
    user = USERS.get(requester_id)
    if user is None:
        return False
    return user["org"] == note["org"]


def show_note(requester_id, note_id):
    note = _note(note_id)
    if not _can_view(requester_id, note):
        raise PermissionError("forbidden")
    return {"text": note["text"]}


def members_of(org):
    return sorted(uid for uid, user in USERS.items() if user["org"] == org)


def promote(user_id):
    USERS[user_id]["role"] = "admin"
    return USERS[user_id]


def note_count(org):
    return sum(1 for note in NOTES.values() if note["org"] == org)


def initials(user_id):
    return user_id[:2].upper()

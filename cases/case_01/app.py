RECORDS = {
    "r1": {"owner_id": "alice", "title": "Q3 plan", "body": "alice-private-body"},
    "r2": {"owner_id": "bob", "title": "Trip", "body": "bob-private-body"},
}
USERS = {"alice": {"name": "Alice"}, "bob": {"name": "Bob"}}


def normalize_id(raw):
    return raw.strip().lower()


def load_record(record_id):
    record = RECORDS.get(record_id)
    if record is None:
        raise LookupError(record_id)
    return record


def to_view(record):
    return {"title": record["title"], "body": record["body"]}


def get_record(requester_id, record_id):
    record = load_record(normalize_id(record_id))
    return to_view(record)


def count_records_by_user(user_id):
    total = 0
    for record in RECORDS.values():
        if record["owner_id"] == user_id:
            total += 1
    return total


def list_titles():
    return sorted(record["title"] for record in RECORDS.values())


def rename_user(user_id, new_name):
    if user_id not in USERS:
        raise LookupError(user_id)
    USERS[user_id]["name"] = new_name.strip()
    return USERS[user_id]


def summarize(text, limit=20):
    if len(text) <= limit:
        return text
    return text[:limit] + "..."

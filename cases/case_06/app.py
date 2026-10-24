DOCUMENTS = {
    "d1": {"owner_id": "alice", "name": "contract", "content": "alice-private-content"},
    "d2": {"owner_id": "bob", "name": "resume", "content": "bob-private-content"},
}
TAGS = {"d1": ["legal"], "d2": ["career"]}


def _read(doc_id):
    document = DOCUMENTS.get(doc_id)
    if document is None:
        raise LookupError(doc_id)
    return document


def is_owner(requester_id, document):
    return document["owner_id"] == requester_id


def _payload(document):
    return {"name": document["name"], "content": document["content"]}


def download_document(requester_id, doc_id):
    document = _read(doc_id)
    is_owner(requester_id, document)
    return _payload(document)


def tag_document(doc_id, tag):
    TAGS.setdefault(doc_id, [])
    if tag not in TAGS[doc_id]:
        TAGS[doc_id].append(tag)
    return TAGS[doc_id]


def documents_with_tag(tag):
    return [doc_id for doc_id, tags in TAGS.items() if tag in tags]


def name_length(doc_id):
    return len(_read(doc_id)["name"])


def all_names():
    return [document["name"] for document in DOCUMENTS.values()]

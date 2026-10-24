PHOTOS = {
    "ph1": {"owner_id": "alice", "caption": "beach", "location": "alice-private-location"},
    "ph2": {"owner_id": "bob", "caption": "park", "location": "bob-private-location"},
}


class Acl:
    def __init__(self, rules):
        self.rules = rules

    def allows(self, requester_id, photo):
        return photo["owner_id"] == requester_id


ACL = Acl(rules={})


def _photo(photo_id):
    photo = PHOTOS.get(photo_id)
    if photo is None:
        raise LookupError(photo_id)
    return photo


def photo_meta(requester_id, photo_id):
    photo = _photo(photo_id)
    if not ACL.allows(requester_id, photo):
        raise PermissionError("forbidden")
    return {"caption": photo["caption"], "location": photo["location"]}


def captions():
    return [photo["caption"] for photo in PHOTOS.values()]


def rename_caption(photo_id, caption):
    _photo(photo_id)["caption"] = caption.strip()
    return PHOTOS[photo_id]


def photo_count():
    return len(PHOTOS)

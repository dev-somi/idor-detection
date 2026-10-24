PRODUCTS = {
    "p1": {"owner_id": "alice", "name": "Lamp", "description": "alice-listing-description", "stock": 4},
    "p2": {"owner_id": "bob", "name": "Desk", "description": "bob-listing-description", "stock": 0},
}
REVIEWS = {"p1": [5, 4], "p2": [3]}


def _find(product_id):
    product = PRODUCTS.get(product_id)
    if product is None:
        raise LookupError(product_id)
    return product


def _card(product):
    return {"name": product["name"], "description": product["description"]}


def view_product(requester_id, product_id):
    product = _find(product_id)
    return _card(product)


def update_stock(requester_id, product_id, stock):
    product = _find(product_id)
    if product["owner_id"] != requester_id:
        raise PermissionError("forbidden")
    product["stock"] = stock
    return product["stock"]


def average_rating(product_id):
    scores = REVIEWS.get(product_id, [])
    if not scores:
        return None
    return sum(scores) / len(scores)


def in_stock():
    return [pid for pid, product in PRODUCTS.items() if product["stock"] > 0]


def search(keyword):
    keyword = keyword.lower()
    return [pid for pid, product in PRODUCTS.items() if keyword in product["name"].lower()]

ORDERS = {
    "o1": {"owner_id": "alice", "items": ["pen"], "address": "alice-private-address"},
    "o2": {"owner_id": "bob", "items": ["cup", "plate"], "address": "bob-private-address"},
}
PRICES = {"pen": 3, "cup": 7, "plate": 9}


def _get_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        raise LookupError(order_id)
    return order


def _require_match(left_id, right_id):
    if left_id != right_id:
        raise PermissionError("forbidden")


def _guard(requester_id, order):
    _require_match(order["owner_id"], requester_id)
    return order


def _shape(order):
    return {"items": list(order["items"]), "address": order["address"]}


def order_detail(requester_id, order_id):
    order = _guard(requester_id, _get_order(order_id))
    return _shape(order)


def order_total(order_id):
    order = _get_order(order_id)
    return sum(PRICES[item] for item in order["items"])


def popular_items():
    counts = {}
    for order in ORDERS.values():
        for item in order["items"]:
            counts[item] = counts.get(item, 0) + 1
    return sorted(counts, key=counts.get, reverse=True)


def add_price(item, price):
    if price < 0:
        raise ValueError(price)
    PRICES[item] = price
    return PRICES

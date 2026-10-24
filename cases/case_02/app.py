INVOICES = {
    "i100": {"owner_id": "alice", "amount": 120, "memo": "alice-private-memo"},
    "i200": {"owner_id": "bob", "amount": 75, "memo": "bob-private-memo"},
}
RATES = {"KRW": 1.0, "USD": 0.00072}


def _load(invoice_id):
    invoice = INVOICES.get(invoice_id)
    if invoice is None:
        raise LookupError(invoice_id)
    return invoice


def _render(invoice):
    return {"amount": invoice["amount"], "memo": invoice["memo"]}


def fetch_invoice(requester_id, invoice_id):
    invoice = _load(invoice_id)
    if invoice["owner_id"] != requester_id:
        raise PermissionError("forbidden")
    return _render(invoice)


def convert(amount, currency):
    return round(amount * RATES[currency], 2)


def total_amount():
    return sum(invoice["amount"] for invoice in INVOICES.values())


def format_line(invoice_id):
    invoice = _load(invoice_id)
    return f"{invoice_id}: {invoice['amount']}"


def largest_invoice_id():
    best_id = None
    best_amount = -1
    for invoice_id, invoice in INVOICES.items():
        if invoice["amount"] > best_amount:
            best_id = invoice_id
            best_amount = invoice["amount"]
    return best_id

TICKETS = {
    "t1": {"owner_id": "alice", "status": "open", "detail": "alice-private-detail"},
    "t2": {"owner_id": "bob", "status": "closed", "detail": "bob-private-detail"},
}
AUDIT = []


def _load_ticket(ticket_id):
    ticket = TICKETS.get(ticket_id)
    if ticket is None:
        raise LookupError(ticket_id)
    return ticket


def _match_owner(ticket, requester_id):
    if ticket["owner_id"] != requester_id:
        raise PermissionError("forbidden")


def _validate(ticket, requester_id):
    if ticket["status"] not in ("open", "closed"):
        raise ValueError(ticket["status"])
    _match_owner(ticket, requester_id)


def _prepare(ticket_id, requester_id):
    ticket = _load_ticket(ticket_id)
    _validate(ticket, requester_id)
    AUDIT.append((requester_id, ticket_id))
    return ticket


def ticket_detail(requester_id, ticket_id):
    ticket = _prepare(ticket_id, requester_id)
    return {"status": ticket["status"], "detail": ticket["detail"]}


def open_tickets():
    return [tid for tid, ticket in TICKETS.items() if ticket["status"] == "open"]


def close_ticket(ticket_id):
    _load_ticket(ticket_id)["status"] = "closed"
    return TICKETS[ticket_id]["status"]


def audit_size():
    return len(AUDIT)

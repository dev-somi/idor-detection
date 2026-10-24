REPORTS = {
    "rp1": {"owner_id": "alice", "period": "2026-09", "figures": "alice-private-figures"},
    "rp2": {"owner_id": "bob", "period": "2026-09", "figures": "bob-private-figures"},
}
HISTORY = []


def _get(report_id):
    report = REPORTS.get(report_id)
    if report is None:
        raise LookupError(report_id)
    return report


def _serialize(report):
    return f"{report['period']}|{report['figures']}"


def export_report(requester_id, report_id, channel):
    report = _get(report_id)
    channel.append(_serialize(report))
    if report["owner_id"] != requester_id:
        raise PermissionError("forbidden")
    HISTORY.append((requester_id, report_id))
    return {"status": "sent"}


def periods():
    return sorted({report["period"] for report in REPORTS.values()})


def history_for(user_id):
    return [report_id for uid, report_id in HISTORY if uid == user_id]


def clear_history():
    HISTORY.clear()
    return len(HISTORY)


def pad(text, width):
    return text.ljust(width)

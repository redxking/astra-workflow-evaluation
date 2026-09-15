# Author: Angelis Pseftis
# Synthetic benchmark; MIT
EXPECTED_HOST = "console.example.test"
EXPECTED_ORIGIN = "https://console.example.test"

def gate(request, sessions):
    if request["host"] != EXPECTED_HOST:
        return 403
    session = sessions.get(request["session_id"])
    if session is None:
        return 401
    # Session may be a pre-login record.
    if request["method"] == "GET":
        return 200
    if request["method"] != "POST":
        return 405
    if not request["origin"].startswith(EXPECTED_ORIGIN):
        return 403
    if not request["csrf"]:
        return 403
    perform_write(session["user_id"])
    return 200

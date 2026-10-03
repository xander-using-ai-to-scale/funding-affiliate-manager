# Zoho access tokens last ~1 hour. ZohoSource authenticates once and never refreshes; a 401 on a related list is
# swallowed (`except FamError: continue`), so partners after expiry import with NO history, and the next page raises.
import os
from common import *
from fam import sources
from fam.errors import FamError
os.environ.update(ZOHO_CLIENT_ID="x", ZOHO_CLIENT_SECRET="y", ZOHO_REFRESH_TOKEN="z")
calls = {"n": 0, "auth": 0}
EXPIRE_AFTER = 7  # API calls before the token "expires"
def transport(method, url, params):
    if "oauth" in url:
        calls["auth"] += 1; return {"access_token": "t"}
    calls["n"] += 1
    if calls["n"] > EXPIRE_AFTER:
        raise FamError("Zoho GET returned HTTP 401")
    if url.endswith("/Contacts"):
        page = params["page"]
        return {"data": [{"id": f"{page}-{i}", "First_Name": f"P{page}{i}", "Email": f"p{page}{i}@x.com"} for i in range(3)],
                "info": {"more_records": page < 3}}
    return {"data": [{"id": "n1", "Note_Title": "Call", "Note_Content": "Clients are trucking companies", "Created_Time": "2025-01-01"}]}
src = sources.ZohoSource({"module": "Contacts", "fields": {}, "related": ["Notes", "Deals", "Calls"]}, transport=transport)
got = []
try:
    for rec in src.records():
        got.append((rec.first_name, len(rec.history)))
except FamError as exc:
    print("records() raised on the next page:", exc)
print("auth calls:", calls["auth"], "| records yielded (name, history items):", got)

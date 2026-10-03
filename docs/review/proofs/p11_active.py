# An active producer whose record lacks last_deal_date (zoho-map.json leaves it blank) is tagged quiet and,
# because rank() sorts by lifetime deals first, lands at the top of wave 1 with "I'm now your partner manager".
import tempfile, csv
from common import *
from fam import sources, kickoff, drafting
with tempfile.TemporaryDirectory() as tmp:
    s, g = make(tmp)
    p = Path(tmp)/"partners.csv"
    rows = [dict(external_id="z1", first_name="Top", last_name="Producer", email="top@x.com", phone="+15555550101",
                 tier="CEO", join_date="2021-03-01", deals_submitted="48", last_deal_date="", last_contact_date=ago(60)),
            dict(external_id="z2", first_name="Quiet", last_name="Partner", email="q@x.com", phone="+15555550102",
                 tier="Apprentice", join_date="2023-03-01", deals_submitted="0", last_deal_date="", last_contact_date=ago(400))]
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    e = engine(s, g)
    print(sources.import_records(e, sources.CsvSource(p).records()))
    wave = kickoff.draft_wave(e, 250, drafter=drafting.TemplateDrafter())
    for d in wave["drafts"]: print(" ", d["name"], "->", d["body"][:120])

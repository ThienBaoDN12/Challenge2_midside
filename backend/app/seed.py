"""Reproducible demo seed (NFR-12). Names and IDs match the frontend mock data.

Seeded listings go through the same extractor + projection code as real uploads.
"""
import json

from . import db
from .services import extractor, vault
from .services import listings as lst
from .services import templates as tpl
from .util import iso, iso_in

ORGS = [
    ("org_mekong", "Mekong Agro", "Việt Nam", "seller", "coffee", "Sustainable coffee producer and exporter working with family farms across Vietnam."),
    ("org_daklak", "Dak Lak Cooperative", "Việt Nam", "seller", "coffee", "Robusta cooperative in Dak Lak."),
    ("org_highland", "Highland Origin Co.", "Việt Nam", "seller", "coffee", "Specialty and commercial coffee."),
    ("org_ppi", "Phnom Penh Imports", "Campuchia", "buyer", "coffee", "Importer and distributor for Phnom Penh retail."),
]
USERS = [  # (id, email, name, org, role)
    ("usr_lan", "lan@mekongagro.vn", "Nguyen Lan", "org_mekong", "manager"),
    ("usr_minh", "minh@mekongagro.vn", "Tran Minh", "org_mekong", "staff"),
    ("usr_dara", "dara@ppimports.com.kh", "Dara Chhim", "org_ppi", "manager"),
    ("usr_sokha", "sokha@ppimports.com.kh", "Sokha Lim", "org_ppi", "staff"),
    ("usr_daklak", "an@daklakcoop.vn", "Pham An", "org_daklak", "manager"),
    ("usr_highland", "binh@highlandorigin.vn", "Vo Binh", "org_highland", "manager"),
]
INVITES = [  # C3 states: pending and expired
    ("inv_hoang", "hoang@mekongagro.vn", "staff", iso_in(5)),
    ("inv_vy", "vy@mekongagro.vn", "staff", iso_in(-2)),
]


def coffee(product, qty, valid_until, port="Cat Lai, HCMC", grade="Screen 18", moq=5, incoterm="FOB",
           price=4100, floor=3850, cost=3600, delivery="2026-11-15 → 2026-11-28", payment="T/T 30% deposit, 70% before shipment"):
    return {
        "template": "coffee_green_v3",
        "fields": {
            "product": {"value": product}, "quantity": {"value": qty, "unit": "ton"},
            "valid_until": {"value": valid_until}, "grade": {"value": grade},
            "moq": {"value": moq, "unit": "ton"}, "port_of_loading": {"value": port},
            "incoterm": {"value": incoterm}, "delivery_window": {"value": delivery},
            "payment_terms": {"value": payment}, "certification": {"value": "4C"},
            "indicative_price": {"value": price, "unit": "USD/ton"},
            "floor_price": {"value": floor, "unit": "USD/ton"}, "cost_price": {"value": cost, "unit": "USD/ton"},
            "supplier_households": {"value": "124 households"},
        },
    }


PUBLIC = ["product", "quantity", "valid_until", "grade", "moq", "port_of_loading", "incoterm",
          "delivery_window", "payment_terms"]  # 9 of 14 public (AT-06)

LISTINGS = [  # (id, org, status, file)
    ("LST-VN-0161", "org_mekong", "published", coffee("Robusta Coffee Grade 1", 20, "2026-11-30")),
    ("LST-VN-0158", "org_mekong", "draft", coffee("Robusta Coffee Screen 16", 12, "2026-12-18")),
    ("LST-VN-0142", "org_mekong", "paused", coffee("Arabica Coffee Grade 1", 8, "2026-12-15")),
    ("LST-VN-0119", "org_mekong", "expired", coffee("Robusta Coffee Grade 2", 50, "2026-06-20")),
    ("LST-VN-0154", "org_daklak", "published", coffee("Robusta Coffee Screen 18", 35, "2026-12-10", incoterm="DAP")),
    ("LST-VN-0147", "org_highland", "published", coffee("Robusta Coffee Grade 1", 24, "2026-12-15", port="Da Nang")),
]


def seed() -> None:
    if db.one("SELECT 1 FROM organizations LIMIT 1"):
        return
    with db.transaction():
        for o in ORGS:
            db.run("INSERT INTO organizations (id, name, country, side, product_group, description) VALUES (?, ?, ?, ?, ?, ?)", o)
        for uid, email, name, org, role in USERS:
            db.run("INSERT INTO users (id, identity_subject, email, name) VALUES (?, ?, ?, ?)", (uid, f"tide|{uid}", email, name))
            db.run("INSERT INTO memberships (user_id, org_id, role) VALUES (?, ?, ?)", (uid, org, role))
        db.run("INSERT INTO users (id, identity_subject, email, name, is_platform_admin) VALUES ('usr_admin', 'tide|admin', 'admin@trustgate.ai', 'Platform Admin', 1)")
        for iid, email, role, exp in INVITES:
            db.run("INSERT INTO invites (id, token, org_id, email, role, status, invited_by, expires_at) VALUES (?, ?, 'org_mekong', ?, ?, 'pending', 'usr_lan', ?)",
                   (iid, f"demo-{iid}", email, role, exp))

        t = tpl.by_id("coffee_green_v3")
        for listing_id, org, status, payload in LISTINGS:
            raw = json.dumps(payload).encode()
            result = extractor.extract("seed.json", raw, t)
            ciphertext, digest = vault.encrypt(raw)
            file_id, snap_id = f"file_{listing_id}", f"snap_{listing_id}"
            db.run("INSERT INTO confidential_files VALUES (?, ?, ?, 'seed.json', ?, ?, ?, 'seed', ?)",
                   (file_id, org, t["id"], ciphertext, digest, len(raw), iso()))
            db.run("INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, '[]', ?)",
                   (snap_id, file_id, org, t["id"], db.dumps(result["fields"]), iso()))
            valid_until = payload["fields"]["valid_until"]["value"]
            db.run("INSERT INTO listings VALUES (?, ?, ?, 'coffee', ?, 1, ?, ?)", (listing_id, org, t["id"], status, valid_until, iso()))
            db.run("INSERT INTO listing_versions VALUES (?, 1, ?, ?, ?, ?)",
                   (listing_id, snap_id, db.dumps(PUBLIC), db.dumps(lst.projection(t, result["fields"], PUBLIC)), iso()))

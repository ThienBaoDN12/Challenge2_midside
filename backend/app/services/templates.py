"""Fixed, versioned templates per product type (FR-07).

Field flags:
  required       – must be present in the confidential file
  sensitive      – private by default; making it public needs a confirmation (FR-13)
  blocked        – platform policy forbids publishing/sharing it (FR-13, §8)
  locked_public  – minimum discoverable fields, always public (FR-13)
"""

QTY_UNITS = ["ton", "kg"]
PRICE_UNITS = ["USD/ton", "USD/kg"]


def f(key, label, type_="text", *, units=None, required=False, sensitive=False, blocked=False, locked=False):
    return {
        "key": key,
        "label": label,
        "type": type_,
        "unit_options": units or [],
        "required": required,
        "sensitive": sensitive,
        "blocked": blocked,
        "locked_public": locked,
    }


COMMON_TAIL = [
    f("port_of_loading", "Port of Loading", required=True),
    f("incoterm", "Incoterm", "enum", units=["FOB", "CIF", "DAP", "EXW"]),
    f("delivery_window", "Delivery Window"),
    f("payment_terms", "Payment Terms"),
    f("certification", "Certification"),
    f("indicative_price", "Indicative Price", "number", units=PRICE_UNITS),
    f("floor_price", "Floor Price", "number", units=PRICE_UNITS, required=True, sensitive=True),
    f("cost_price", "Cost Price", "number", units=PRICE_UNITS, sensitive=True),
    f("supplier_households", "Farmer Household List", sensitive=True, blocked=True),
]

TEMPLATES = [
    {
        # Default product template from SRS §15.2: green coffee, template v3, 14 fields
        "id": "coffee_green_v3",
        "product_type": "coffee",
        "label": "Cà phê nhân xanh",
        "version": 3,
        "fields": [
            f("product", "Product", required=True, locked=True),
            f("quantity", "Quantity", "number", units=QTY_UNITS, required=True, locked=True),
            f("valid_until", "Validity Date", "date", required=True, locked=True),
            f("grade", "Grade", required=True),
            f("moq", "MOQ", "number", units=QTY_UNITS, required=True),
            *COMMON_TAIL,
        ],
    },
    {
        "id": "pepper_black_v1",
        "product_type": "pepper",
        "label": "Hồ tiêu đen",
        "version": 1,
        "fields": [
            f("product", "Product", required=True, locked=True),
            f("quantity", "Quantity", "number", units=QTY_UNITS, required=True, locked=True),
            f("valid_until", "Validity Date", "date", required=True, locked=True),
            f("grade", "Density (g/l)", required=True),
            f("moq", "MOQ", "number", units=QTY_UNITS, required=True),
            *COMMON_TAIL,
        ],
    },
    {
        "id": "cashew_raw_v1",
        "product_type": "cashew",
        "label": "Hạt điều",
        "version": 1,
        "fields": [
            f("product", "Product", required=True, locked=True),
            f("quantity", "Quantity", "number", units=QTY_UNITS, required=True, locked=True),
            f("valid_until", "Validity Date", "date", required=True, locked=True),
            f("grade", "Grade", required=True),
            f("moq", "MOQ", "number", units=QTY_UNITS, required=True),
            *COMMON_TAIL,
        ],
    },
    {
        "id": "rice_white_v1",
        "product_type": "rice",
        "label": "Gạo",
        "version": 1,
        "fields": [
            f("product", "Product", required=True, locked=True),
            f("quantity", "Quantity", "number", units=QTY_UNITS, required=True, locked=True),
            f("valid_until", "Validity Date", "date", required=True, locked=True),
            f("grade", "Broken %", required=True),
            f("moq", "MOQ", "number", units=QTY_UNITS, required=True),
            *COMMON_TAIL,
        ],
    },
]


def by_id(template_id: str) -> dict | None:
    return next((t for t in TEMPLATES if t["id"] == template_id), None)


def by_product(product_type: str) -> dict | None:
    return next((t for t in TEMPLATES if t["product_type"] == product_type), None)


def field_map(template: dict) -> dict[str, dict]:
    return {fd["key"]: fd for fd in template["fields"]}


def sample_file(template: dict) -> dict:
    """Downloadable JSON template (the .xlsx variant is built in the router)."""
    return {
        "template": template["id"],
        "fields": {
            fd["key"]: {"value": "", "unit": fd["unit_options"][0] if fd["unit_options"] and fd["type"] == "number" else None}
            for fd in template["fields"]
        },
    }

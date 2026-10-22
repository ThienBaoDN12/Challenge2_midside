"""Deterministic field extraction from a confidential file (FR-08, FR-10, FR-11).

Pure code: no LLM, no network, no formula evaluation, no URL fetching.
Accepted formats:
  .json  {"template": "<id>", "fields": {"<key>": {"value": ..., "unit": ...}}}
  .xlsx  first sheet, header row "key | value | unit", cell A1 of sheet "meta" or
         a row with key "template" naming the template id.
"""
import io
import json
import re
from datetime import date

from . import templates as tpl


class ExtractError(Exception):
    def __init__(self, errors: list[dict]):
        super().__init__("extract failed")
        self.errors = errors


def _err(line, field, message):
    return {"line": line, "field": field, "message": message}


def _read_json(raw: bytes):
    try:
        text = raw.decode("utf-8")
        data = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ExtractError([_err(None, None, "File JSON không hợp lệ. Tải lại file mẫu để đối chiếu.")])
    if not isinstance(data, dict) or not isinstance(data.get("fields"), dict):
        raise ExtractError([_err(None, None, "File không đúng mẫu: thiếu khối \"fields\".")])
    rows = []
    for key, cell in data["fields"].items():
        # Line number of the key in the original text, so errors point at the file line.
        m = re.search(r'"%s"\s*:' % re.escape(key), text)
        line = text.count("\n", 0, m.start()) + 1 if m else None
        if isinstance(cell, dict):
            rows.append((line, key, cell.get("value"), cell.get("unit")))
        else:
            rows.append((line, key, cell, None))
    return data.get("template"), rows


def _read_xlsx(raw: bytes):
    try:
        from openpyxl import load_workbook

        # data_only: read cached values, never evaluate formulas
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    except Exception:
        raise ExtractError([_err(None, None, "File Excel không đọc được. Tải lại file mẫu để đối chiếu.")])
    ws = wb.worksheets[0]
    template_id, rows = None, []
    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if not row or row[0] is None:
            continue
        key = str(row[0]).strip()
        if idx == 1 and key.lower() == "key":
            continue  # header
        value = row[1] if len(row) > 1 else None
        unit = row[2] if len(row) > 2 else None
        if key == "template":
            template_id = str(value).strip() if value else None
            continue
        rows.append((idx, key, value, unit))
    return template_id, rows


def _parse_value(fd: dict, value, unit, line) -> tuple[object, str | None, dict | None]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, None, None
    if fd["type"] == "number":
        try:
            num = float(str(value).replace(",", ""))
        except ValueError:
            return None, None, _err(line, fd["key"], f"Trường {fd['label']} phải là số (dòng {line}).")
        if num < 0:
            return None, None, _err(line, fd["key"], f"Trường {fd['label']} không được âm (dòng {line}).")
        if fd["unit_options"]:
            if not unit:
                return None, None, _err(line, fd["key"], f"Thiếu đơn vị cho trường {fd['label']} (dòng {line}).")
            if unit not in fd["unit_options"]:
                opts = ", ".join(fd["unit_options"])
                return None, None, _err(line, fd["key"], f"Đơn vị \"{unit}\" không hợp lệ cho {fd['label']} (dòng {line}). Chọn: {opts}.")
        return num, unit, None
    if fd["type"] == "date":
        v = value.isoformat()[:10] if hasattr(value, "isoformat") else str(value).strip()
        try:
            date.fromisoformat(v)
        except ValueError:
            return None, None, _err(line, fd["key"], f"Ngày {fd['label']} phải theo dạng YYYY-MM-DD (dòng {line}).")
        return v, None, None
    if fd["type"] == "enum" and fd["unit_options"] and str(value) not in fd["unit_options"]:
        opts = ", ".join(fd["unit_options"])
        return None, None, _err(line, fd["key"], f"Giá trị {fd['label']} không hợp lệ (dòng {line}). Chọn: {opts}.")
    return str(value).strip(), None, None


def extract(filename: str, raw: bytes, expected_template: dict) -> dict:
    """Returns {"fields": [{key,value,unit}], "dropped_columns": [...]} or raises ExtractError."""
    name = filename.lower()
    if name.endswith(".json"):
        template_id, rows = _read_json(raw)
    elif name.endswith(".xlsx"):
        template_id, rows = _read_xlsx(raw)
    else:
        raise ExtractError([_err(None, None, "File không đúng mẫu. Chỉ nhận .xlsx hoặc .json tải từ hệ thống.")])

    if template_id != expected_template["id"]:
        raise ExtractError([_err(None, "template", f"File không đúng mẫu {expected_template['label']} v{expected_template['version']}. Tải lại file mẫu để đối chiếu.")])

    fields = tpl.field_map(expected_template)
    errors, extracted, dropped, seen = [], [], [], set()
    for line, key, value, unit in rows:
        fd = fields.get(key)
        if not fd:
            dropped.append(key)  # FR-11: unknown column dropped and reported
            continue
        seen.add(key)
        parsed, parsed_unit, error = _parse_value(fd, value, unit, line)
        if error:
            errors.append(error)
        elif parsed is None:
            if fd["required"]:
                errors.append(_err(line, key, f"Thiếu trường bắt buộc {fd['label']} (dòng {line}). Tải lại file mẫu để đối chiếu."))
        else:
            extracted.append({"key": key, "value": parsed, "unit": parsed_unit})

    for key, fd in fields.items():
        if fd["required"] and key not in seen:
            errors.append(_err(None, key, f"Thiếu trường bắt buộc {fd['label']}. Tải lại file mẫu để đối chiếu."))

    if errors:
        raise ExtractError(errors)  # FR-10: no snapshot on any error
    return {"fields": extracted, "dropped_columns": dropped}

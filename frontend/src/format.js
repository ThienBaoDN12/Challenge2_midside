// Display helpers for backend values (units stay explicit, NFR-05)
const UNIT_LABEL = { ton: "Tons", kg: "kg" };

export function fmtNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString("en-US") : String(value ?? "");
}

export function fmtDate(iso) {
  if (!iso || !/^\d{4}-\d{2}-\d{2}/.test(iso)) return iso ?? "—";
  const d = new Date(`${iso.slice(0, 10)}T00:00:00`);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function fmtTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtValue(value, unit) {
  if (value === null || value === undefined || value === "") return "—";
  if (unit && unit.includes("/")) {
    const [cur, per] = unit.split("/");
    return `${fmtNumber(value)} ${cur} / ${per}`;
  }
  if (unit) return `${fmtNumber(value)} ${UNIT_LABEL[unit] ?? unit}`;
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) return fmtDate(value);
  return String(value);
}

export function fmtField(field) {
  return field ? fmtValue(field.value, field.unit) : "—";
}

export function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

export function title(listing) {
  const pf = listing.public_fields;
  return `${pf.product?.value ?? listing.product_type} · ${fmtField(pf.quantity)}`;
}

export function capitalize(s = "") {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Backend status -> label used by the existing ConnectionStatusBadge styles
export const REQUEST_STATUS = {
  pending: "Pending",
  accepted: "Accepted",
  declined: "Declined",
  expired: "Expired",
  withdrawn: "Withdrawn",
};

export function timeLeft(iso) {
  const ms = new Date(iso) - new Date();
  if (ms <= 0) return "Expired";
  const d = Math.floor(ms / 86400000);
  const h = Math.floor((ms % 86400000) / 3600000);
  return `${d}d ${h}h left`;
}

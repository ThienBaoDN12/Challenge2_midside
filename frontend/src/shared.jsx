import { Children } from "react";
import Dropdown from "./components/Dropdown.jsx";
import {
  CircleAlert,
  ListFilter,
  ArrowRight,
  Check,
  ChevronDown,
  Clock,
  FileText,
  Lock,
  Mail,
  Plus,
  ShieldCheck,
  Sparkles,
  User,
  Users,
  X,
} from "lucide-react";
export const screenMeta = {
  onboarding: {
    code: "C1",
    label: "Onboarding",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  invitation: {
    code: "C2",
    label: "Staff invitation",
    org: "Mekong Agro",
    role: "Seller Staff",
    side: "seller",
  },
  members: {
    code: "C3",
    label: "Team members",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "seller-workspace": {
    code: "S1",
    label: "Listings",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "listing-upload": {
    code: "S2",
    label: "Upload",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "listing-fields": {
    code: "S3",
    label: "Fields",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "listing-publish": {
    code: "S4",
    label: "Publish",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "seller-inbox": {
    code: "S5",
    label: "Connection inbox",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "buyer-workspace": {
    code: "B1",
    label: "Buyer workspace",
    org: "Phnom Penh Imports",
    role: "Buyer Manager",
    side: "buyer",
  },
  "buyer-detail": {
    code: "B2",
    label: "Listing detail",
    org: "Phnom Penh Imports",
    role: "Buyer Manager",
    side: "buyer",
  },
  "buyer-recommendations": {
    code: "B3",
    label: "Recommendations",
    org: "Phnom Penh Imports",
    role: "Buyer Manager",
    side: "buyer",
  },
  "buyer-inbox": {
    code: "B4",
    label: "Connection inbox",
    org: "Phnom Penh Imports",
    role: "Buyer Manager",
    side: "buyer",
  },
  "deal-room": {
    code: "R1",
    label: "Deal Room",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "contract-edit": {
    code: "R3",
    label: "Create contract",
    org: "Mekong Agro",
    role: "Seller Manager",
    side: "seller",
  },
  "contract-review": {
    code: "R4",
    label: "Review contract",
    org: "Phnom Penh Imports",
    role: "Buyer Manager",
    side: "buyer",
  },
};
export const team = [
  {
    initials: "NL",
    name: "Nguyen Lan",
    email: "lan@mekongagro.vn",
    role: "Manager",
    status: "Active",
  },
  {
    initials: "TM",
    name: "Tran Minh",
    email: "minh@mekongagro.vn",
    role: "Staff",
    status: "Active",
  },
  {
    initials: "LH",
    name: "Le Hoang",
    email: "hoang@mekongagro.vn",
    role: "Staff",
    status: "Pending Acceptance",
  },
  {
    initials: "PV",
    name: "Pham Vy",
    email: "vy@mekongagro.vn",
    role: "Staff",
    status: "Expired",
  },
];
const ICONS = {
  alert: CircleAlert,
  arrow: ArrowRight,
  check: Check,
  chevron: ChevronDown,
  clock: Clock,
  close: X,
  file: FileText,
  lock: Lock,
  mail: Mail,
  plus: Plus,
  spark: Sparkles,
  shield: ShieldCheck,
  team: Users,
  user: User,
};
// Compact dropdown used for status filters and sort controls
export function FilterSelect({ label = "Status", value, options, onChange }) {
  return (
    <Dropdown
      variant="pill"
      ariaLabel={label}
      icon={<ListFilter size={15} strokeWidth={1.8} />}
      prefix={label}
      options={options}
      value={value}
      onChange={onChange}
    />
  );
}

export function Icon({ name, size = 18 }) {
  const LucideIcon = ICONS[name];
  return <LucideIcon aria-hidden="true" size={size} strokeWidth={1.7} />;
}
export function Logo() {
  return (
    <div className="logo-lockup" aria-label="TrustGate AI">
      <span className="logo-mark">
        <Icon name="shield" size={20} />
      </span>
      <span className="logo-wordmark">
        TrustGate <strong>AI</strong>
      </span>
    </div>
  );
}
export function Button({
  children,
  kind = "primary",
  type = "button",
  onClick,
}) {
  return (
    <button className={`button button-${kind}`} type={type} onClick={onClick}>
      {children}
    </button>
  );
}
export function Field({ label, value, placeholder, type = "text", onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange?.(event.target.value)}
      />
    </label>
  );
}
export function SelectField({ label, value, children, onChange }) {
  // Accept <option> children so existing call sites stay unchanged
  const options = Children.toArray(children).map((child) => {
    const text = String(child.props.children);
    return { value: child.props.value ?? text, label: text };
  });
  return (
    <div className="field">
      <span>{label}</span>
      <Dropdown
        ariaLabel={label}
        options={options}
        value={value}
        onChange={onChange}
      />
    </div>
  );
}
export const listings = [
  {
    id: "LST-VN-0161",
    version: "v1",
    title: "Robusta Coffee 20 Tons",
    status: "Published",
    category: "Coffee",
    quantity: "20 Tons",
    validity: "Nov 30, 2026",
    interest: "8 buyer matches",
  },
  {
    id: "LST-VN-0158",
    version: "v2",
    title: "Black Pepper 12 Tons",
    status: "Draft",
    category: "Black Pepper",
    quantity: "12 Tons",
    validity: "Dec 18, 2026",
    interest: "Not visible yet",
  },
  {
    id: "LST-VN-0142",
    version: "v3",
    title: "Arabica Coffee 8 Tons",
    status: "Paused",
    category: "Coffee",
    quantity: "8 Tons",
    validity: "Oct 15, 2026",
    interest: "3 active rooms",
  },
  {
    id: "LST-VN-0119",
    version: "v1",
    title: "White Rice 50 Tons",
    status: "Expired",
    category: "Rice",
    quantity: "50 Tons",
    validity: "Jun 20, 2026",
    interest: "Closed",
  },
];
export function FlowSteps({ current, onNavigate }) {
  const screens = ["listing-upload", "listing-fields", "listing-publish"];
  return (
    <div
      className="flow-steps"
      aria-label={`Listing creation step ${current} of 3`}
    >
      {["Template & upload", "Review fields", "Preview & publish"].map(
        (label, index) => {
          const step = index + 1;
          return (
            <button
              className={`flow-step ${step === current ? "active" : step < current ? "done" : ""}`}
              key={label}
              type="button"
              onClick={() => onNavigate(screens[index])}
            >
              <span>
                {step < current ? <Icon name="check" size={13} /> : step}
              </span>
              {label}
            </button>
          );
        },
      )}
    </div>
  );
}
export function Toggle({ checked, locked = false, label, onChange }) {
  return (
    <button
      aria-label={label}
      aria-pressed={checked}
      className={`toggle ${checked ? "on" : ""} ${locked ? "locked" : ""}`}
      type="button"
      onClick={() => !locked && onChange?.()}
    >
      <span />
    </button>
  );
}
export function ConnectionStatusBadge({ status, detail }) {
  return (
    <span className={`connection-status ${status.toLowerCase()}`}>
      <span />
      {status}
      {detail && <small>{detail}</small>}
    </span>
  );
}
export function LegalDisclaimer() {
  return (
    <div className="legal-disclaimer">
      <Icon name="shield" size={16} />
      <span>
        <strong>In-system confirmation</strong>
        This is an in-system confirmation only, not a digital signature, and
        does not replace a formal legal contract.
      </span>
    </div>
  );
}

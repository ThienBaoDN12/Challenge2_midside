import { useState } from "react";
import { api } from "../api";
import Dropdown from "../components/Dropdown.jsx";
import Stepper from "../components/Stepper.jsx";
import { ArrowIcon, EyeIcon, LockIcon } from "../components/Icons.jsx";

// Seeded demo accounts (backend/app/seed.py) — TideCloak stand-in
const DEMO_EMAILS = {
  "seller-manager": "lan@mekongagro.vn",
  "seller-staff": "minh@mekongagro.vn",
  "buyer-manager": "dara@ppimports.com.kh",
  "buyer-staff": "sokha@ppimports.com.kh",
};

const ROLES = [
  {
    id: "seller-manager",
    label: "Seller Manager",
    sub: "Full workspace control",
    side: "seller",
  },
  {
    id: "seller-staff",
    label: "Seller Staff",
    sub: "Joins by invitation",
    side: "seller",
  },
  {
    id: "buyer-manager",
    label: "Buyer Manager",
    sub: "Full workspace control",
    side: "buyer",
  },
  {
    id: "buyer-staff",
    label: "Buyer Staff",
    sub: "Joins by invitation",
    side: "buyer",
  },
];
const COUNTRY = { seller: "Vietnam", buyer: "Cambodia" };
const isStaff = (id) => id.endsWith("staff");

export default function Login({ onLogin, onOpenInvite }) {
  const [step, setStep] = useState(1);
  const [side, setSide] = useState("seller");
  const [org, setOrg] = useState("Mekong Agro");
  const [roleId, setRoleId] = useState("seller-manager");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const role = ROLES.find((r) => r.id === roleId);

  function selectRole(r) {
    setRoleId(r.id);
    setSide(r.side);
  }

  async function signIn() {
    setLoading(true);
    setError(null);
    try {
      // TODO: replace with the real TideCloak OIDC redirect
      const session = await api.login(DEMO_EMAILS[roleId]);
      // Existing members go straight to their workspace; a new account sets up its organization
      if (session.organization) return onLogin(session);
      setStep(2);
    } catch (e) {
      setError(
        e.status
          ? e.message
          : "Cannot reach the backend. Start it with: uvicorn app.main:app --reload",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <main className="shell">
        <Intro />
        <section className="card" aria-labelledby="stepTitle">
          <Stepper current={step} />
          <div className="card__body">
            {step === 1 && (
              <div className="step is-visible">
                <p className="eyebrow eyebrow--center">Step 1 of 3</p>
                <h2 className="step__title" id="stepTitle">
                  Sign in to continue
                </h2>
                <p className="step__lead">
                  TideCloak assigns your workspace and permissions from your
                  organization role.
                </p>

                <div className="roles" role="radiogroup" aria-label="Role">
                  {ROLES.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      role="radio"
                      aria-checked={r.id === roleId}
                      className={`role ${r.id === roleId ? "is-selected" : ""}`}
                      onClick={() => selectRole(r)}
                    >
                      <span className="role__check" />
                      <span className="role__body">
                        <b>{r.label}</b>
                        <small>{r.sub}</small>
                      </span>
                      <span className={`role__tag role__tag--${r.side}`}>
                        {r.side === "seller" ? "VN" : "KH"}
                      </span>
                    </button>
                  ))}
                </div>

                {error && <p className="hint">{error}</p>}

                {isStaff(roleId) && (
                  <p className="hint">
                    Staff can't create an organization. New here?{" "}
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        onOpenInvite();
                      }}
                    >
                      Open your invitation
                    </a>
                    .
                  </p>
                )}

                <button
                  type="button"
                  className="cta"
                  onClick={signIn}
                  disabled={loading}
                >
                  <span className="cta__badge">T</span>
                  <span className="cta__label">
                    {loading
                      ? "Connecting to TideCloak…"
                      : `Sign in as ${role.label}`}
                  </span>
                  <ArrowIcon className="cta__arrow" />
                </button>

                <p className="footnote">
                  <LockIcon /> Single sign‑on · Encrypted session ·{" "}
                  <a href="#">Create an account</a>
                </p>
              </div>
            )}

            {step === 2 && (
              <div className="step is-visible">
                <p className="eyebrow eyebrow--center">Step 2 of 3</p>
                <h2 className="step__title">Which side do you trade on?</h2>
                <p className="step__lead">
                  This sets your country and workspace. You can't change it
                  later.
                </p>
                <div className="sides">
                  {["seller", "buyer"].map((s) => (
                    <button
                      key={s}
                      type="button"
                      data-side={s}
                      className={`side ${side === s ? "is-selected" : ""}`}
                      onClick={() => setSide(s)}
                    >
                      <span
                        className={`side__flag ${s === "buyer" ? "side__flag--buyer" : ""}`}
                      >
                        {s === "seller" ? "VN" : "KH"}
                      </span>
                      <b>{s === "seller" ? "Seller" : "Buyer"}</b>
                      <small>
                        {s === "seller"
                          ? "Vietnam · publish sell listings"
                          : "Cambodia · find sellers with AI"}
                      </small>
                    </button>
                  ))}
                </div>
                <div className="actions">
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => setStep(1)}
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => setStep(3)}
                  >
                    Continue
                  </button>
                </div>
              </div>
            )}

            {step === 3 && (
              <ProfileForm
                side={side}
                defaultOrg={org}
                onBack={() => setStep(2)}
                onSubmit={async (profile) => {
                  setOrg(profile.name);
                  onLogin(await api.createOrg({ ...profile, side }));
                }}
              />
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function Intro() {
  return (
    <section className="intro">
      <p className="eyebrow">Organization setup</p>
      <h1 className="intro__title">Build trust from the first exchange.</h1>
      <p className="intro__lead">
        Create a verified workspace for secure cross‑border trade. Your details
        stay private until you choose to share them.
      </p>
      <ul className="assurances">
        <li>
          <span className="assurances__icon">
            <LockIcon />
          </span>
          <div>
            <strong>Confidential · Encrypted</strong>
            <span>Private files never reach the AI.</span>
          </div>
        </li>
        <li>
          <span className="assurances__icon assurances__icon--sage">
            <EyeIcon />
          </span>
          <div>
            <strong>You choose what's public</strong>
            <span>Partners and AI see only the fields you publish.</span>
          </div>
        </li>
      </ul>
    </section>
  );
}

function ProfileForm({ side, defaultOrg, onBack, onSubmit }) {
  const [org, setOrg] = useState(defaultOrg);
  const [group, setGroup] = useState("Coffee");
  const [description, setDescription] = useState("");

  return (
    <form
      className="step is-visible"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (org.trim())
          onSubmit({
            name: org.trim(),
            product_group: group.toLowerCase(),
            description,
          });
      }}
    >
      <p className="eyebrow eyebrow--center">Step 3 of 3</p>
      <h2 className="step__title">Organization profile</h2>
      <div className="badges">
        <span className="badge badge--ok">✓ Email verified</span>
        <span className="badge badge--muted">Business not verified</span>
      </div>
      <label className="field">
        <span>Organization name</span>
        <input value={org} onChange={(e) => setOrg(e.target.value)} required />
      </label>
      <div className="field-row">
        <label className="field">
          <span>Country</span>
          <input value={COUNTRY[side]} readOnly />
        </label>
        <div className="field">
          <span>Product group</span>
          <Dropdown
            ariaLabel="Product group"
            options={["Coffee", "Pepper", "Cashew", "Rice"]}
            value={group}
            onChange={setGroup}
          />
        </div>
      </div>
      <label className="field">
        <span>Description</span>
        <textarea
          rows={3}
          placeholder="What you trade, capacity, certifications…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      <p className="fine">
        You'll be the <b>Manager</b> of this organization.
      </p>
      <div className="actions">
        <button type="button" className="btn-ghost" onClick={onBack}>
          Back
        </button>
        <button type="submit" className="btn-primary" disabled={!org.trim()}>
          Enter workspace
        </button>
      </div>
    </form>
  );
}

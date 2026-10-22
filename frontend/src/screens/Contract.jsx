import { useEffect, useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks";
import { fmtNumber, fmtValue } from "../format";
import {
  Icon,
  Button,
  Field,
  SelectField,
  ConnectionStatusBadge,
  LegalDisclaimer,
  ApiStatus,
  ErrorNote,
} from "../shared";

const KG = { ton: 1000, kg: 1 };

// Live preview only; the backend recomputes the total and rejects mismatches (FR-40)
function previewTotal(terms) {
  const q = terms.quantity;
  const p = terms.unit_price;
  if (!q?.value || !p?.value || !q.unit || !p.unit) return null;
  const [currency, per] = p.unit.split("/");
  const total = (Number(q.value) * KG[q.unit] * Number(p.value)) / KG[per];
  return Number.isFinite(total)
    ? `${fmtNumber(Math.round(total * 100) / 100)} ${currency}`
    : null;
}

export function ContractEditor({ roomId, onBack, onSent }) {
  const prefill = useApi(() => api.prefillContract(roomId), [roomId]);
  const history = useApi(() => api.contracts(roomId), [roomId]);
  const [terms, setTerms] = useState(null);
  const [file, setFile] = useState(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  const previous = history.data?.versions[0];
  const nextVersion = (previous?.version ?? 0) + 1;

  // Start from the previous version after a revision request, otherwise from the prefill
  useEffect(() => {
    if (terms || !prefill.data || !history.data) return;
    const base = previous ? previous.terms : prefill.data.terms;
    const filled = Object.fromEntries(base.map((t) => [t.key, { ...t }]));
    // Unit / currency are required: default to what the dropdowns show
    if (filled.quantity && !filled.quantity.unit) filled.quantity.unit = "ton";
    if (filled.unit_price && !filled.unit_price.unit) filled.unit_price.unit = "USD/ton";
    setTerms(filled);
  }, [prefill.data, history.data, previous, terms]);

  if (!terms) {
    return (
      <main className="page contract-page">
        <ApiStatus
          loading={prefill.loading || history.loading}
          error={prefill.error || history.error}
          onRetry={prefill.reload}
        />
      </main>
    );
  }

  const set = (key, patch) =>
    setTerms((t) => ({ ...t, [key]: { ...t[key], ...patch } }));
  const v = (key) => (terms[key]?.value ?? "") + "";
  const total = previewTotal(terms);
  const notes = previous?.term_notes ?? {};

  const send = async () => {
    setSending(true);
    setError(null);
    const body = Object.values(terms).map(({ key, value, unit }) => ({
      key,
      value,
      unit,
    }));
    try {
      if (file) {
        const draft = await api.draftContract(roomId, body);
        await api.attachPdf(roomId, draft.id, file);
        await api.sendDraft(roomId, draft.id);
      } else {
        await api.sendContract(roomId, body);
      }
      onSent();
    } catch (e) {
      setError(e);
    } finally {
      setSending(false);
    }
  };

  return (
    <main className="page contract-page">
      <LegalDisclaimer />
      <button className="back-action" type="button" onClick={onBack}>
        <Icon name="arrow" size={14} /> Back to Deal Room
      </button>

      <div className="contract-page-heading">
        <div>
          <p className="eyebrow">{roomId} · Seller Manager</p>
          <h1>Create Contract v{nextVersion}</h1>
          <p>
            Structured terms prefilled from the listing and room-shared
            information.
          </p>
        </div>
      </div>

      {previous?.status === "revision_requested" && (
        <section className="buyer-feedback">
          <div className="feedback-head">
            <Icon name="mail" size={18} />
            <div>
              <strong>
                Buyer’s clause-by-clause feedback · v{previous.version}
              </strong>
              <span>Revision requested by the Buyer Manager</span>
            </div>
          </div>
          {previous.note && (
            <div>
              <span>General note</span>
              <p>“{previous.note}”</p>
            </div>
          )}
          {Object.entries(notes).map(([key, note]) => (
            <div key={key}>
              <span>{terms[key]?.label ?? key}</span>
              <p>“{note}”</p>
            </div>
          ))}
        </section>
      )}

      <section className="contract-editor">
        <div className="contract-editor-head">
          <div>
            <p className="eyebrow">Contract Terms Summary</p>
            <h2>Commercial terms</h2>
          </div>
          <div className="source-tags">
            {Object.values(terms).some((t) => t.origin === "listing") && (
              <span>Listing</span>
            )}
            {Object.values(terms).some((t) => t.origin === "shared") && (
              <span>Shared in Room</span>
            )}
          </div>
        </div>

        <div className="contract-form-grid">
          <Field
            label="Product"
            value={v("product")}
            onChange={(x) => set("product", { value: x })}
          />
          <Field
            label="Grade / Quality"
            value={v("quality")}
            onChange={(x) => set("quality", { value: x })}
          />
          <Field
            label="Quantity"
            value={v("quantity")}
            onChange={(x) => set("quantity", { value: x })}
          />
          <SelectField
            label="Unit · Required"
            value={terms.quantity?.unit ?? "ton"}
            onChange={(x) => set("quantity", { unit: x })}
          >
            <option value="ton">Tons</option>
            <option value="kg">Kilograms</option>
          </SelectField>
          <Field
            label="Unit Price"
            value={v("unit_price")}
            onChange={(x) => set("unit_price", { value: x })}
          />
          <SelectField
            label="Currency / Unit · Required"
            value={terms.unit_price?.unit ?? "USD/ton"}
            onChange={(x) => set("unit_price", { unit: x })}
          >
            {(prefill.data?.price_units ?? ["USD/ton"]).map((u) => (
              <option key={u}>{u}</option>
            ))}
          </SelectField>
          <label className="field calculated-field">
            <span>Total Value · Auto-calculated</span>
            <span className="calculated-value">{total ?? "—"}</span>
            <small>Quantity × Unit Price · verified by the server</small>
          </label>
          <SelectField
            label="Incoterms / Delivery Terms"
            value={v("incoterm") || "DAP"}
            onChange={(x) => set("incoterm", { value: x })}
          >
            <option>DAP</option>
            <option>FOB</option>
            <option>CIF</option>
            <option>EXW</option>
          </SelectField>
          <Field
            label="Delivery Location"
            value={v("delivery_location")}
            onChange={(x) => set("delivery_location", { value: x })}
          />
          <Field
            label="Delivery Date"
            value={v("delivery_date")}
            onChange={(x) => set("delivery_date", { value: x })}
          />
          <label className="field contract-wide-field">
            <span>Payment Terms</span>
            <textarea
              rows={3}
              value={v("payment_terms")}
              onChange={(e) => set("payment_terms", { value: e.target.value })}
            />
          </label>
        </div>

        <label className={`contract-pdf-slot ${file ? "has-file" : ""}`}>
          <input
            accept=".pdf"
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <span>
            <Icon name={file ? "check" : "file"} size={20} />
          </span>
          <div>
            <strong>{file?.name || "Attach Reference Contract PDF"}</strong>
            <small>
              {file
                ? "Reference attached"
                : "Optional · PDF only · Does not replace structured terms"}
            </small>
          </div>
        </label>

        <ErrorNote error={error} />
      </section>

      <div className="contract-submit-bar">
        <span>
          <Icon name="lock" size={14} /> Contract · Versioned
        </span>
        <Button onClick={send} disabled={sending}>
          {sending ? "Sending…" : "Send to Buyer for Confirmation"}
          {!sending && <Icon name="arrow" size={16} />}
        </Button>
      </div>
    </main>
  );
}

const STATUS_TEXT = {
  draft: "Draft",
  pending: "Awaiting Buyer Confirmation",
  confirmed: "Confirmed",
  revision_requested: "Revision Requested",
  declined: "Declined",
  cancelled: "Cancelled",
};
const BADGE = {
  draft: "Pending",
  pending: "Pending",
  confirmed: "Accepted",
  revision_requested: "Pending",
  declined: "Declined",
  cancelled: "Expired",
};

export function ContractReview({ role, roomId, onBack, onNewVersion }) {
  const buyerManager = role === "Buyer Manager";
  const {
    data,
    error: loadError,
    loading,
    reload,
  } = useApi(() => api.contracts(roomId), [roomId], 5000);
  const [version, setVersion] = useState(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [actionMode, setActionMode] = useState(null);
  const [termNotes, setTermNotes] = useState({});
  const [declineReason, setDeclineReason] = useState("");
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const versions = data?.versions ?? [];
  const contract = versions.find((c) => c.version === version) ?? versions[0];

  if (!contract) {
    return (
      <main className="page contract-page review-contract-page">
        <button className="back-action" type="button" onClick={onBack}>
          <Icon name="arrow" size={14} /> Back to Deal Room
        </button>
        <ApiStatus loading={loading} error={loadError} onRetry={reload} />
        {data && (
          <section className="inbox-empty">
            <Icon name="file" size={22} />
            <h2>No contract yet</h2>
            <p>The Seller Manager has not sent a contract in this room.</p>
          </section>
        )}
      </main>
    );
  }

  const act = async (fn) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      setActionMode(null);
      await reload(true);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  const explain = async () => {
    if (explanation) return setExplanation(null);
    setExplanation({ answer: "Thinking…", sources: [] });
    try {
      setExplanation(
        await api.ask(roomId, "Giải thích các điều khoản hợp đồng"),
      );
    } catch (e) {
      setExplanation({ answer: e.message, sources: [] });
    }
  };
  const canDecide = contract.actions.decide;
  const latest = versions[0];
  const product = contract.terms.find((t) => t.key === "product")?.value;
  const qty = contract.terms.find((t) => t.key === "quantity");

  return (
    <main className="page contract-page review-contract-page">
      <LegalDisclaimer />
      <button className="back-action" type="button" onClick={onBack}>
        <Icon name="arrow" size={14} /> Back to Deal Room
      </button>

      <div className="contract-page-heading">
        <div>
          <p className="eyebrow">{roomId} · Contract review</p>
          <h1>Review Contract Terms</h1>
          <p>
            Compare structured terms with the listing and room-shared
            information.
          </p>
        </div>
        <div className="contract-review-state">
          <ConnectionStatusBadge
            status={BADGE[contract.status]}
            detail={STATUS_TEXT[contract.status]}
          />
          <div className="version-selector">
            <span>Version history</span>
            {[...versions].reverse().map((c) => (
              <button
                key={c.id}
                className={c.version === contract.version ? "active" : ""}
                type="button"
                onClick={() => setVersion(c.version)}
              >
                {c.version_label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <section className="contract-review-card">
        <div className="contract-editor-head">
          <div>
            <p className="eyebrow">
              Contract Terms Summary · {contract.version_label}
            </p>
            <h2>
              {product} · {fmtValue(qty?.value, qty?.unit)}
            </h2>
          </div>
          <button className="ask-contract-ai" type="button" onClick={explain}>
            <Icon name="spark" size={15} /> Ask Private AI to Explain Terms
          </button>
        </div>

        {explanation && (
          <div className="contract-ai-explanation">
            <span className="ai-avatar">
              <Icon name="spark" size={17} />
            </span>
            <div>
              <strong>Private AI explanation</strong>
              <p style={{ whiteSpace: "pre-line" }}>{explanation.answer}</p>
              {explanation.sources?.length > 0 && (
                <span className="citation-pill">
                  Source: Contract v{explanation.sources[0].version} · Terms
                  summary
                </span>
              )}
            </div>
          </div>
        )}

        <div className="contract-terms-table">
          <div className="contract-term-row contract-term-head">
            <span>Clause</span>
            <span>Structured term</span>
            <span>Comparison</span>
          </div>
          {contract.terms.map((t) => (
            <div className="contract-term-row" key={t.key}>
              <span>{t.label}</span>
              <strong>{fmtValue(t.value, t.unit)}</strong>
              <span>
                {t.differs_from_listing ? (
                  <span className="differs-pill">
                    {t.from_shared
                      ? "From Shared Info"
                      : "Differs from Listing"}
                  </span>
                ) : (
                  <span className="aligned-term">
                    <Icon name="check" size={12} /> Aligned
                  </span>
                )}
              </span>
              {actionMode === "revision" && (
                <label className="clause-comment">
                  <span>Revision note for {t.label}</span>
                  <input
                    placeholder={`Add feedback on ${t.label.toLowerCase()}…`}
                    value={termNotes[t.key] ?? ""}
                    onChange={(e) =>
                      setTermNotes({ ...termNotes, [t.key]: e.target.value })
                    }
                  />
                </label>
              )}
            </div>
          ))}
          <div className="contract-term-row">
            <span>Total Value</span>
            <strong>
              {fmtNumber(contract.total)} {contract.currency}
            </strong>
            <span>
              <span className="aligned-term">
                <Icon name="check" size={12} /> System-calculated
              </span>
            </span>
          </div>
        </div>

        <ErrorNote error={error} />

        {contract.status === "confirmed" ? (
          <div className="contract-confirmed-banner">
            <Icon name="check" size={18} />
            <span>
              <strong>Deal Confirmed</strong>
              {roomId} has been updated to Deal Closed / Confirmed.
            </span>
          </div>
        ) : !canDecide ? (
          <div className="contract-readonly">
            <Icon
              name={
                contract.status === "declined"
                  ? "close"
                  : contract.status === "revision_requested"
                    ? "mail"
                    : "lock"
              }
              size={15}
            />
            <span>
              <strong>{STATUS_TEXT[contract.status]}</strong>
              {contract.status === "revision_requested"
                ? "Clause feedback was sent to the Seller Manager for a new version."
                : contract.status === "declined"
                  ? `${contract.note ? `“${contract.note}” · ` : ""}The room remains active.`
                  : buyerManager
                    ? "This version is no longer awaiting your decision."
                    : "Read-only view · Contract actions are available to Buyer Manager only."}
            </span>
            {role === "Seller Manager" &&
              contract.id === latest.id &&
              ["revision_requested", "declined"].includes(contract.status) && (
                <Button onClick={onNewVersion}>
                  Create v{latest.version + 1} <Icon name="arrow" size={15} />
                </Button>
              )}
          </div>
        ) : (
          <div className="contract-actions">
            {actionMode === "decline" && (
              <label className="field decline-contract-reason">
                <span>Decline reason · Optional</span>
                <textarea
                  placeholder="Explain why this contract cannot be confirmed"
                  rows={3}
                  value={declineReason}
                  onChange={(event) => setDeclineReason(event.target.value)}
                />
              </label>
            )}
            {actionMode === "revision" && (
              <div className="revision-note">
                <Icon name="mail" size={15} />
                Add comments beneath each clause, then send them to Seller
                Manager for a new version.
              </div>
            )}
            {!actionMode && (
              <label className="contract-acknowledgement">
                <input
                  checked={acknowledged}
                  type="checkbox"
                  onChange={(event) => setAcknowledged(event.target.checked)}
                />
                <span>I understand this is an in-system confirmation</span>
              </label>
            )}
            <div className="contract-action-buttons">
              {!actionMode && (
                <>
                  <button
                    className="button button-primary"
                    disabled={!acknowledged || busy}
                    type="button"
                    onClick={() =>
                      act(() => api.confirmContract(roomId, contract.id))
                    }
                  >
                    Confirm Contract <Icon name="check" size={15} />
                  </button>
                  <Button
                    kind="secondary"
                    onClick={() => setActionMode("revision")}
                  >
                    Request Revision
                  </Button>
                  <button
                    className="decline-contract"
                    type="button"
                    onClick={() => setActionMode("decline")}
                  >
                    Decline Contract
                  </button>
                </>
              )}
              {actionMode === "revision" && (
                <>
                  <Button
                    disabled={
                      busy || !Object.values(termNotes).some((n) => n.trim())
                    }
                    onClick={() =>
                      act(() =>
                        api.requestRevision(roomId, contract.id, termNotes),
                      )
                    }
                  >
                    Send Revision Request
                  </Button>
                  <Button kind="ghost" onClick={() => setActionMode(null)}>
                    Cancel
                  </Button>
                </>
              )}
              {actionMode === "decline" && (
                <>
                  <button
                    className="button button-primary"
                    disabled={busy}
                    type="button"
                    onClick={() =>
                      act(() =>
                        api.declineContract(
                          roomId,
                          contract.id,
                          declineReason || null,
                        ),
                      )
                    }
                  >
                    Confirm Decline
                  </button>
                  <Button kind="ghost" onClick={() => setActionMode(null)}>
                    Cancel
                  </Button>
                </>
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

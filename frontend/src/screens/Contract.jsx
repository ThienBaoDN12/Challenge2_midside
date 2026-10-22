import { useState } from "react";
import {
  Icon,
  Button,
  Field,
  SelectField,
  Toggle,
  ConnectionStatusBadge,
  LegalDisclaimer,
  FilterSelect,
} from "../shared";
export function ContractEditor({ onBack, onSent }) {
  const [quantity, setQuantity] = useState("20");
  const [unitPrice, setUnitPrice] = useState("2150");
  const [versionTwo, setVersionTwo] = useState(false);
  const [showPolicy, setShowPolicy] = useState(true);
  const [fileName, setFileName] = useState("");
  const [sent, setSent] = useState(false);
  const total = (Number(quantity) || 0) * (Number(unitPrice) || 0);
  const totalFormatted = total.toLocaleString("en-US");
  const sendContract = () => {
    setSent(true);
    window.setTimeout(onSent, 900);
  };
  return (
    <main className="page contract-page">
      <LegalDisclaimer />
      <button className="back-action" type="button" onClick={onBack}>
        <Icon name="arrow" size={14} /> Back to Deal Room
      </button>

      <div className="contract-page-heading">
        <div>
          <p className="eyebrow">DR-0402 · Seller Manager</p>
          <h1>{versionTwo ? "Create Contract v2" : "Create Contract v1"}</h1>
          <p>Structured terms from LST-VN-0161 and room-shared information.</p>
        </div>
        <label className="contract-version-toggle">
          <span>
            <strong>Create v2</strong>
            After Buyer Revision Request
          </span>
          <Toggle
            checked={versionTwo}
            label="Create contract v2 after buyer revision request"
            onChange={() => setVersionTwo(!versionTwo)}
          />
        </label>
      </div>

      {versionTwo && (
        <section className="buyer-feedback">
          <div className="feedback-head">
            <Icon name="mail" size={18} />
            <div>
              <strong>Buyer’s clause-by-clause feedback · v1</strong>
              <span>Requested by Dara Chhim · Phnom Penh Imports</span>
            </div>
          </div>
          <div>
            <span>Unit Price</span>
            <p>
              “Please revise to 2,100 USD / ton based on the discussed volume.”
            </p>
          </div>
          <div>
            <span>Payment Terms</span>
            <p>“Request 20% deposit and 80% against shipping documents.”</p>
          </div>
          <div>
            <span>Delivery Date</span>
            <p>“Please confirm arrival no later than November 28.”</p>
          </div>
        </section>
      )}

      <section className="contract-editor">
        <div className="contract-editor-head">
          <div>
            <p className="eyebrow">Contract Terms Summary</p>
            <h2>Commercial terms</h2>
          </div>
          <div className="source-tags">
            <span>Listing LST-VN-0161 v1</span>
            <span>Shared in Room</span>
          </div>
        </div>

        <div className="contract-form-grid">
          <Field label="Product" value="Robusta Coffee" />
          <Field label="Grade / Quality" value="Grade 1 · Screen 18" />
          <Field label="Quantity" value={quantity} onChange={setQuantity} />
          <SelectField label="Unit · Required" value="Tons">
            <option>Tons</option>
            <option>Kilograms</option>
          </SelectField>
          <Field label="Unit Price" value={unitPrice} onChange={setUnitPrice} />
          <SelectField label="Currency · Required" value="USD">
            <option>USD</option>
          </SelectField>
          <label className="field calculated-field">
            <span>Total Value · Auto-calculated</span>
            <span className="calculated-value">{totalFormatted} USD</span>
            <small>Quantity × Unit Price</small>
          </label>
          <SelectField label="Incoterms / Delivery Terms" value="DAP">
            <option>DAP</option>
            <option>FOB</option>
            <option>CIF</option>
          </SelectField>
          <Field label="Delivery Location" value="Phnom Penh, Cambodia" />
          <Field label="Delivery Date" value="Nov 28, 2026" />
          <label className="field contract-wide-field">
            <span>Payment Terms</span>
            <textarea
              defaultValue={
                versionTwo
                  ? "20% deposit · 80% against shipping documents"
                  : "30% deposit · 70% against shipping documents"
              }
              key={versionTwo ? "v2" : "v1"}
              rows={3}
            />
          </label>
        </div>

        <label className={`contract-pdf-slot ${fileName ? "has-file" : ""}`}>
          <input
            accept=".pdf"
            type="file"
            onChange={(event) =>
              setFileName(event.target.files?.[0]?.name ?? "")
            }
          />
          <span>
            <Icon name={fileName ? "check" : "file"} size={20} />
          </span>
          <div>
            <strong>{fileName || "Attach Reference Contract PDF"}</strong>
            <small>
              {fileName
                ? "Reference attached"
                : "Optional · PDF only · Does not replace structured terms"}
            </small>
          </div>
        </label>

        <div className="policy-example-toggle">
          <span>Policy check example</span>
          <Toggle
            checked={showPolicy}
            label="Toggle total value policy check"
            onChange={() => setShowPolicy(!showPolicy)}
          />
        </div>
        {showPolicy && (
          <div className="contract-policy-alert">
            <span>
              <Icon name="alert" size={16} />
            </span>
            <div>
              <strong>Total value mismatch</strong>
              <p>
                The system has recalculated the total: {totalFormatted} USD.
              </p>
            </div>
          </div>
        )}
      </section>

      <div className="contract-submit-bar">
        <span>
          <Icon name="lock" size={14} /> Contract · Versioned
        </span>
        <Button onClick={sendContract}>
          {sent
            ? "Awaiting Buyer Confirmation"
            : "Send to Buyer for Confirmation"}
          {!sent && <Icon name="arrow" size={16} />}
        </Button>
      </div>
    </main>
  );
}
export function ContractReview({ role, dealConfirmed, onConfirm, onBack }) {
  const buyerManager = role === "Buyer Manager";
  const [version, setVersion] = useState("v1");
  const [acknowledged, setAcknowledged] = useState(false);
  const [status, setStatus] = useState(
    dealConfirmed ? "Confirmed" : "Awaiting Buyer Confirmation",
  );
  const [actionMode, setActionMode] = useState(null);
  const [aiExplanation, setAiExplanation] = useState(false);
  const [declineReason, setDeclineReason] = useState("");
  const terms = [
    ["Product", "Robusta Coffee"],
    ["Grade / Quality", "Grade 1 · Screen 18"],
    ["Quantity", "20 Tons"],
    ["Unit Price", version === "v2" ? "2,100 USD / ton" : "2,150 USD / ton"],
    ["Total Value", version === "v2" ? "42,000 USD" : "43,000 USD"],
    ["Incoterms", "DAP"],
    ["Delivery Location", "Phnom Penh, Cambodia"],
    ["Delivery Date", "Nov 28, 2026"],
    [
      "Payment Terms",
      version === "v2"
        ? "20% deposit · 80% against documents"
        : "30% deposit · 70% against documents",
    ],
  ];
  const differs = ["Unit Price", "Delivery Location", "Payment Terms"];
  const confirmContract = () => {
    if (!acknowledged) return;
    setStatus("Confirmed");
    onConfirm();
  };
  return (
    <main className="page contract-page review-contract-page">
      <LegalDisclaimer />
      <button className="back-action" type="button" onClick={onBack}>
        <Icon name="arrow" size={14} /> Back to Deal Room
      </button>

      <div className="contract-page-heading">
        <div>
          <p className="eyebrow">DR-0402 · Contract review</p>
          <h1>Review Contract Terms</h1>
          <p>
            Compare structured terms with the listing and room-shared
            information.
          </p>
        </div>
        <div className="contract-review-state">
          <ConnectionStatusBadge
            status={status === "Confirmed" ? "Accepted" : "Pending"}
            detail={status}
          />
          <div className="version-selector">
            <span>Version history</span>
            <button
              className={version === "v1" ? "active" : ""}
              type="button"
              onClick={() => setVersion("v1")}
            >
              v1
            </button>
            <button
              className={version === "v2" ? "active" : ""}
              type="button"
              onClick={() => setVersion("v2")}
            >
              v2
            </button>
          </div>
        </div>
      </div>

      <section className="contract-review-card">
        <div className="contract-editor-head">
          <div>
            <p className="eyebrow">Contract Terms Summary · {version}</p>
            <h2>Robusta Coffee · 20 Tons</h2>
          </div>
          <button
            className="ask-contract-ai"
            type="button"
            onClick={() => setAiExplanation(!aiExplanation)}
          >
            <Icon name="spark" size={15} /> Ask Private AI to Explain Terms
          </button>
        </div>

        {aiExplanation && (
          <div className="contract-ai-explanation">
            <span className="ai-avatar">
              <Icon name="spark" size={17} />
            </span>
            <div>
              <strong>Private AI explanation</strong>
              <p>
                DAP means the seller arranges delivery to Phnom Penh while the
                buyer handles import clearance. The payment balance is due
                against shipping documents.
              </p>
              <span className="citation-pill">
                Source: Contract {version} · Incoterms & Payment Terms
              </span>
            </div>
          </div>
        )}

        <div className="contract-terms-table">
          <div className="contract-term-row contract-term-head">
            <span>Clause</span>
            <span>Structured term</span>
            <span>Comparison</span>
          </div>
          {terms.map(([label, value]) => (
            <div className="contract-term-row" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
              <span>
                {differs.includes(label) ? (
                  <span className="differs-pill">Differs from Listing</span>
                ) : (
                  <span className="aligned-term">
                    <Icon name="check" size={12} /> Aligned
                  </span>
                )}
              </span>
              {actionMode === "revision" && (
                <label className="clause-comment">
                  <span>Revision note for {label}</span>
                  <input
                    placeholder={`Add feedback on ${label.toLowerCase()}…`}
                  />
                </label>
              )}
            </div>
          ))}
        </div>

        {!buyerManager ? (
          <div className="contract-readonly">
            <Icon name="lock" size={15} />
            <span>
              <strong>{status}</strong>
              Read-only view · Contract actions are available to Buyer Manager
              only.
            </span>
          </div>
        ) : status === "Confirmed" ? (
          <div className="contract-confirmed-banner">
            <Icon name="check" size={18} />
            <span>
              <strong>Deal Confirmed</strong>
              DR-0402 has been updated to Deal Closed / Confirmed.
            </span>
          </div>
        ) : status === "Revision Requested" ? (
          <div className="contract-readonly">
            <Icon name="mail" size={15} />
            <span>
              <strong>Revision Requested</strong>
              Clause feedback was sent to Seller Manager for Contract v2.
            </span>
          </div>
        ) : status === "Declined" ? (
          <div className="contract-readonly">
            <Icon name="close" size={15} />
            <span>
              <strong>Contract Declined</strong>
              The reason was sent to Seller Manager. DR-0402 remains Active.
            </span>
          </div>
        ) : (
          <div className="contract-actions">
            {actionMode === "decline" && (
              <label className="field decline-contract-reason">
                <span>Decline reason · Required</span>
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
                Manager for v2.
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
                    disabled={!acknowledged}
                    type="button"
                    onClick={confirmContract}
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
                    onClick={() => {
                      setStatus("Revision Requested");
                      setActionMode(null);
                    }}
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
                    disabled={!declineReason.trim()}
                    type="button"
                    onClick={() => {
                      setStatus("Declined");
                      setActionMode(null);
                    }}
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

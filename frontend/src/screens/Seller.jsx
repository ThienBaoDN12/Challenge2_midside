import { useState } from "react";
import {
  Icon,
  Button,
  listings,
  FlowSteps,
  Toggle,
  ConnectionStatusBadge,
  FilterSelect,
} from "../shared";
export function SellerWorkspace({ role, onCreate }) {
  const [tab, setTab] = useState("listings");
  const manager = role === "SM";
  return (
    <main className="page workspace-page">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">Seller workspace</p>
          <h1>Sales listings</h1>
          <p>
            Manage what buyers can discover while confidential data stays
            protected.
          </p>
        </div>
      </div>

      <div className="workspace-toolbar">
        <div className="workspace-tabs" role="tablist">
          <button
            aria-selected={tab === "listings"}
            className={tab === "listings" ? "active" : ""}
            role="tab"
            type="button"
            onClick={() => setTab("listings")}
          >
            Active & drafts <span>4</span>
          </button>
          <button
            aria-selected={tab === "matches"}
            className={tab === "matches" ? "active" : ""}
            role="tab"
            type="button"
            onClick={() => setTab("matches")}
          >
            <Icon name="spark" size={15} /> Find Buyers with AI
          </button>
        </div>
        {manager && (
          <Button onClick={onCreate}>
            <Icon name="plus" size={16} /> Create Sales Listing
          </Button>
        )}
      </div>

      {!manager && (
        <div className="readonly-note">
          <Icon name="lock" size={15} />
          Staff view · Public listing fields are read-only
        </div>
      )}

      {tab === "listings" ? (
        <section className="listing-grid">
          {listings.map((listing) => (
            <article className="listing-card" key={listing.id}>
              <div className="listing-card-head">
                <span className="listing-id">
                  {listing.id} · {listing.version}
                </span>
                <span
                  className={`listing-status ${listing.status.toLowerCase()}`}
                >
                  {listing.status}
                </span>
              </div>
              <h2>{listing.title}</h2>
              <div className="public-label">
                <Icon name="shield" size={13} /> Public
              </div>
              <div className="listing-facts">
                <div>
                  <span>Product</span>
                  <strong>{listing.category}</strong>
                </div>
                <div>
                  <span>Quantity</span>
                  <strong>{listing.quantity}</strong>
                </div>
                <div>
                  <span>Valid until</span>
                  <strong>{listing.validity}</strong>
                </div>
              </div>
              <div className="listing-foot">
                <span>{listing.interest}</span>
                {manager && (
                  <button type="button">
                    {listing.status === "Draft" ? "Edit" : "Edit / Pause"}{" "}
                    <Icon name="arrow" size={14} />
                  </button>
                )}
              </div>
            </article>
          ))}
        </section>
      ) : (
        <section className="ai-matches">
          <span className="ai-symbol">
            <Icon name="spark" size={25} />
          </span>
          <div>
            <p className="eyebrow">Privacy-safe discovery</p>
            <h2>Find buyers without exposing private terms.</h2>
            <p>
              TrustGate AI matches only against fields marked Public.
              Confidential files and private snapshots are never read by AI.
            </p>
          </div>
          <span className="tag verified">8 positive matches</span>
        </section>
      )}
    </main>
  );
}
export function ListingUpload({ onContinue, onNavigate }) {
  const [category, setCategory] = useState("Coffee");
  const [policy, setPolicy] = useState("ready");
  const [uploaded, setUploaded] = useState(false);
  return (
    <main className="page creation-page">
      <div className="creation-heading">
        <div>
          <p className="eyebrow">Create sales listing</p>
          <h1>Start with a trusted template.</h1>
          <p>
            Use the fixed format so every field can be validated before anything
            is shared.
          </p>
        </div>
        <FlowSteps current={1} onNavigate={onNavigate} />
      </div>

      <div className="upload-layout">
        <section className="template-panel">
          <div className="panel-number">01</div>
          <h2>Choose a product category</h2>
          <p>
            The template includes the correct units and validation rules for
            your product.
          </p>
          <div className="category-grid">
            {["Coffee", "Black Pepper", "Cashew", "Rice"].map((item) => (
              <button
                className={category === item ? "selected" : ""}
                key={item}
                type="button"
                onClick={() => setCategory(item)}
              >
                <span className="choice-check">
                  {category === item && <Icon name="check" size={13} />}
                </span>
                {item}
              </button>
            ))}
          </div>
          <button className="download-action" type="button">
            <Icon name="file" size={17} />
            <span>
              Download Fixed Template
              <small>.xlsx / .json</small>
            </span>
            <Icon name="arrow" size={15} />
          </button>
          <div className="required-list">
            <span>Required fields</span>
            <div>
              <Icon name="check" size={13} /> Product name
            </div>
            <div>
              <Icon name="check" size={13} /> Quantity & unit
            </div>
            <div>
              <Icon name="check" size={13} /> MOQ
            </div>
            <div>
              <Icon name="check" size={13} /> Validity date
            </div>
          </div>
        </section>

        <section className="upload-panel">
          <div className="panel-number">02</div>
          <h2>Upload confidential file</h2>
          <p>
            Your source file is stored encrypted and never becomes visible to
            buyers.
          </p>
          <label
            className={`drop-zone ${uploaded ? "uploaded" : ""}`}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              setUploaded(true);
            }}
          >
            <input
              type="file"
              accept=".xlsx,.json"
              onChange={() => setUploaded(true)}
            />
            <span className="upload-icon">
              <Icon name={uploaded ? "check" : "file"} size={24} />
            </span>
            <strong>
              {uploaded
                ? "seller_coffee_nov26.xlsx"
                : "Drop your completed template here"}
            </strong>
            <span>
              {uploaded
                ? "Validated · 34 KB"
                : "or choose a .xlsx / .json file · Max 1 MB"}
            </span>
          </label>
          <div className="parser-note">
            <Icon name="lock" size={16} />
            <span>
              <strong>Encrypted storage</strong>
              Parsed by deterministic code. AI never reads your confidential
              file.
            </span>
          </div>
          <div className="policy-preview">
            <span>Preview policy check</span>
            <div>
              <button
                className={policy === "ready" ? "active" : ""}
                type="button"
                onClick={() => setPolicy("ready")}
              >
                Ready
              </button>
              <button
                className={policy === "error" ? "active" : ""}
                type="button"
                onClick={() => setPolicy("error")}
              >
                Error
              </button>
              <button
                className={policy === "ignored" ? "active" : ""}
                type="button"
                onClick={() => setPolicy("ignored")}
              >
                Ignored fields
              </button>
            </div>
          </div>
          {policy === "error" && (
            <div className="policy-block error">
              <Icon name="close" size={18} />
              <span>
                <strong>Validation Error</strong>
                Missing required field: MOQ (Row 4) or Invalid unit. Please
                download the template to compare.
              </span>
            </div>
          )}
          {policy === "ignored" && (
            <div className="policy-block notice">
              <Icon name="file" size={18} />
              <span>
                <strong>Ignored Fields</strong>
                Unrecognized fields ignored: [Internal_Warehouse_Note].
              </span>
            </div>
          )}
        </section>
      </div>
      <div className="creation-actions">
        <span>
          <Icon name="lock" size={14} /> Private Snapshot
        </span>
        <Button onClick={onContinue}>
          Review parsed fields <Icon name="arrow" size={16} />
        </Button>
      </div>
    </main>
  );
}
export const parsedRows = [
  {
    name: "Product",
    value: "Robusta Coffee Grade 1",
    unit: "—",
    tag: "Standard",
    locked: true,
  },
  {
    name: "Quantity",
    value: "20",
    unit: "Tons",
    tag: "Standard",
    locked: true,
  },
  {
    name: "Validity Date",
    value: "Nov 30, 2026",
    unit: "—",
    tag: "Standard",
    locked: true,
  },
  { name: "Grade", value: "Screen 18", unit: "—", tag: "Standard" },
  {
    name: "Port of Loading",
    value: "Cat Lai, HCMC",
    unit: "—",
    tag: "Standard",
  },
  {
    name: "Floor Price",
    value: "$3,850",
    unit: "/ ton",
    tag: "Confidential · Encrypted",
    sensitive: true,
  },
  {
    name: "Cost Price",
    value: "$3,600",
    unit: "/ ton",
    tag: "Confidential · Encrypted",
    sensitive: true,
  },
  {
    name: "Farmer Household List",
    value: "124 households",
    unit: "—",
    tag: "Confidential · Encrypted",
    sensitive: true,
  },
  {
    name: "Farmer Personal ID",
    value: "124 records",
    unit: "—",
    tag: "Confidential · Encrypted",
    blocked: true,
  },
];
export function ListingFields({ onContinue, onNavigate }) {
  const [publicFields, setPublicFields] = useState([
    "Product",
    "Quantity",
    "Validity Date",
    "Grade",
    "Port of Loading",
  ]);
  const [warning, setWarning] = useState(null);
  const requestToggle = (name, blocked) => {
    if (blocked) {
      setWarning("blocked");
      return;
    }
    if (name === "Floor Price" && !publicFields.includes(name)) {
      setWarning("floor");
      return;
    }
    setPublicFields((fields) =>
      fields.includes(name)
        ? fields.filter((field) => field !== name)
        : [...fields, name],
    );
  };
  return (
    <main className="page creation-page fields-page">
      <div className="creation-heading">
        <div>
          <p className="eyebrow">Private snapshot</p>
          <h1>Choose what becomes public.</h1>
          <p>
            Private by default. Only selected fields can be used by buyers and
            Discovery AI.
          </p>
        </div>
        <FlowSteps current={2} onNavigate={onNavigate} />
      </div>

      {warning === "floor" && (
        <div className="sensitive-warning">
          <Icon name="shield" size={20} />
          <span>
            <strong>Sensitive data warning</strong>
            Making Floor Price public exposes it to all buyers and Discovery AI.
            Confirm?
          </span>
          <button type="button" onClick={() => setWarning(null)}>
            Keep private
          </button>
          <Button
            onClick={() => {
              setPublicFields((fields) => [...fields, "Floor Price"]);
              setWarning(null);
            }}
          >
            Confirm
          </Button>
        </div>
      )}
      {warning === "blocked" && (
        <div className="sensitive-warning blocked-warning">
          <Icon name="lock" size={20} />
          <span>
            <strong>Protected by policy</strong>
            This field cannot be made public under platform privacy policy.
          </span>
          <button type="button" onClick={() => setWarning(null)}>
            Dismiss
          </button>
        </div>
      )}

      <section className="parsed-table">
        <div className="parsed-row parsed-header">
          <span>Field name</span>
          <span>Value</span>
          <span>Unit</span>
          <span>Sensitivity tag</span>
          <span>Visibility</span>
        </div>
        {parsedRows.map((row) => {
          const isPublic = row.locked || publicFields.includes(row.name);
          return (
            <div className="parsed-row" key={row.name}>
              <span className="parsed-name">
                {row.name}
                {row.locked && (
                  <small>
                    <Icon name="lock" size={11} /> Minimum field
                  </small>
                )}
              </span>
              <strong>{row.value}</strong>
              <span>{row.unit}</span>
              <span>
                <span
                  className={`data-tag ${row.sensitive || row.blocked ? "confidential" : "standard"}`}
                >
                  {row.tag}
                </span>
              </span>
              <span className="visibility-control">
                <span>{isPublic ? "Public" : "Private"}</span>
                <Toggle
                  checked={isPublic}
                  locked={row.locked}
                  label={`${row.name} ${isPublic ? "public" : "private"}`}
                  onChange={() => requestToggle(row.name, row.blocked)}
                />
              </span>
            </div>
          );
        })}
      </section>
      <div className="creation-actions">
        <span>
          <Icon name="shield" size={14} /> 5 public · 4 private
        </span>
        <Button onClick={onContinue}>
          Preview listing <Icon name="arrow" size={16} />
        </Button>
      </div>
    </main>
  );
}
export function PreviewField({ label, value }) {
  return (
    <div className="preview-field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
export function ListingPublish({ onNavigate }) {
  const [published, setPublished] = useState(false);
  return (
    <main className="page creation-page publish-page">
      <div className="creation-heading">
        <div>
          <p className="eyebrow">Final review</p>
          <h1>Preview before you publish.</h1>
          <p>
            A clear separation between discovery data and protected commercial
            terms.
          </p>
        </div>
        <FlowSteps current={3} onNavigate={onNavigate} />
      </div>

      <div className="publish-state">
        <span>Preview state</span>
        <button
          className={!published ? "active" : ""}
          type="button"
          onClick={() => setPublished(false)}
        >
          Draft
        </button>
        <button
          className={published ? "active" : ""}
          type="button"
          onClick={() => setPublished(true)}
        >
          Published v2
        </button>
      </div>

      {published && (
        <div className="version-banner">
          <span className="version-check">
            <Icon name="check" size={16} />
          </span>
          <span>
            <strong>Listing updated to v2</strong>
            Active Deal Rooms have been notified with a field diff.
          </span>
          <span className="tag verified">Contract · Versioned</span>
        </div>
      )}

      <section className="preview-split">
        <div className="preview-column public-preview">
          <div className="preview-column-head">
            <span className="preview-icon public">
              <Icon name="spark" size={19} />
            </span>
            <div>
              <span className="data-tag public">Public</span>
              <h2>What Buyers & AI Will See</h2>
            </div>
          </div>
          <p>Searchable information used for trusted buyer matching.</p>
          <div className="preview-fields">
            <PreviewField label="Product" value="Robusta Coffee Grade 1" />
            <PreviewField label="Quantity" value="20 Tons" />
            <PreviewField label="Validity" value="Nov 30, 2026" />
            <PreviewField label="Grade" value="Screen 18" />
            <PreviewField label="Port of Loading" value="Cat Lai, HCMC" />
          </div>
        </div>
        <div className="preview-column private-preview">
          <div className="preview-column-head">
            <span className="preview-icon private">
              <Icon name="lock" size={19} />
            </span>
            <div>
              <span className="data-tag private">Confidential · Encrypted</span>
              <h2>Kept Private</h2>
            </div>
          </div>
          <p>
            Only visible to your organization unless explicitly shared in a Deal
            Room.
          </p>
          <div className="preview-fields">
            <PreviewField label="Floor Price" value="$3,850 / ton" />
            <PreviewField label="Cost Price" value="$3,600 / ton" />
            <PreviewField label="Supplier Households" value="124 households" />
          </div>
          <div className="private-assurance">
            <Icon name="shield" size={16} />
            Excluded from buyer search and Discovery AI
          </div>
        </div>
      </section>
      <div className="publish-actions">
        <span>
          <Icon name="lock" size={14} /> Confidential source retained as Private
          Snapshot
        </span>
        <div>
          <Button kind="ghost">Save Draft</Button>
          <Button onClick={() => setPublished(true)}>
            {published ? "Published v2" : "Publish Listing"}{" "}
            <Icon name="arrow" size={16} />
          </Button>
        </div>
      </div>
    </main>
  );
}
export function SellerConnectionInbox({ role, onEnterRoom }) {
  const manager = role === "SM";
  const [tab, setTab] = useState("received");
  const [filter, setFilter] = useState(manager ? "Pending" : "Accepted");
  const [status, setStatus] = useState(manager ? "Pending" : "Accepted");
  const [processing, setProcessing] = useState(false);
  const [roomActive, setRoomActive] = useState(!manager);
  const [declining, setDeclining] = useState(false);
  const [declineReason, setDeclineReason] = useState("");
  const acceptRequest = () => {
    if (processing) return;
    setProcessing(true);
    window.setTimeout(() => {
      setProcessing(false);
      setStatus("Accepted");
      setFilter("Accepted");
      setRoomActive(true);
    }, 850);
  };
  const confirmDecline = () => {
    setStatus("Declined");
    setFilter("Declined");
    setDeclining(false);
  };
  const visible = tab === "received" && filter === status;
  return (
    <main className="page workspace-page connection-page">
      <div className="workspace-heading connection-heading">
        <div>
          <p className="eyebrow">Seller connections</p>
          <h1>Connection inbox</h1>
          <p>
            Review buyer interest before creating a private, versioned Deal
            Room.
          </p>
        </div>
        <span className="expiry-note">
          <Icon name="clock" size={14} /> Requests auto-expire after 7 days
        </span>
      </div>

      {roomActive && (
        <div className="deal-room-banner">
          <span>
            <Icon name="check" size={16} />
          </span>
          <div>
            <strong>Deal Room DR-0402 Created</strong>
            <small>
              Angkor Bean Trading has been notified and the request snapshot is
              preserved.
            </small>
          </div>
          <Button kind="secondary" onClick={onEnterRoom}>
            Enter Deal Room
          </Button>
        </div>
      )}

      <div className="inbox-controls">
        <div className="inbox-tabs">
          <button
            className={tab === "received" ? "active" : ""}
            type="button"
            onClick={() => setTab("received")}
          >
            Received <span>1</span>
          </button>
          <button
            className={tab === "sent" ? "active" : ""}
            type="button"
            onClick={() => setTab("sent")}
          >
            Sent
          </button>
        </div>
        <div className="status-filters">
          <FilterSelect
            value={filter}
            options={[
              "Pending",
              "Accepted",
              "Declined",
              "Expired",
              "Withdrawn",
            ]}
            onChange={setFilter}
          />
        </div>
      </div>

      {visible ? (
        <div className="seller-request-layout">
          <section className="request-list-card">
            <div className="request-list-head">
              <span className="member-avatar">AB</span>
              <div>
                <h2>Angkor Bean Trading</h2>
                <p>Cambodia · Buyer organization</p>
              </div>
              <ConnectionStatusBadge
                status={status}
                detail={status === "Pending" ? "5d 18h left" : undefined}
              />
            </div>
            <div className="request-listing-ref">
              <span>Listing requested</span>
              <strong>LST-VN-0161 · Robusta Coffee 20 Tons</strong>
              <small>Snapshot at time of request · v1</small>
            </div>
            <div className="request-timestamp">
              Received Jun 18, 2026 · 10:24 ICT
            </div>
          </section>

          <section className="request-detail">
            <div className="request-detail-head">
              <div>
                <p className="eyebrow">Request detail</p>
                <h2>Angkor Bean Trading · Cambodia</h2>
              </div>
              <span className="data-tag private">Private Snapshot</span>
            </div>

            <div className="buyer-message">
              <span>Buyer’s message</span>
              <p>
                “Hello, we are interested in discussing availability and
                delivery to Phnom Penh before November 30. Please let us know if
                the listed volume remains available.”
              </p>
            </div>

            <div className="listing-change-warning">
              <div className="change-warning-head">
                <span>
                  <Icon name="file" size={17} />
                </span>
                <div>
                  <strong>Listing Changed After Request</strong>
                  <p>
                    LST-VN-0161 was updated to v2. Review the field diff before
                    accepting.
                  </p>
                </div>
                <span className="tag unverified">v1 → v2</span>
              </div>
              <div className="version-diff">
                <div className="diff-column old">
                  <span>Snapshot requested · v1</span>
                  <div>
                    <small>Validity date</small>
                    <strong>Nov 30, 2026</strong>
                  </div>
                  <div>
                    <small>Port of loading</small>
                    <strong>Cat Lai, HCMC</strong>
                  </div>
                </div>
                <div className="diff-arrow">
                  <Icon name="arrow" size={17} />
                </div>
                <div className="diff-column new">
                  <span>Current listing · v2</span>
                  <div>
                    <small>Validity date</small>
                    <strong>Dec 15, 2026</strong>
                  </div>
                  <div>
                    <small>Port of loading</small>
                    <strong>Cat Lai or Da Nang</strong>
                  </div>
                </div>
              </div>
            </div>

            {manager && status === "Pending" ? (
              <div className="seller-request-actions">
                {declining && (
                  <label className="field decline-field">
                    <span>Decline reason · Optional</span>
                    <textarea
                      placeholder="Share context with the buyer"
                      rows={2}
                      value={declineReason}
                      onChange={(event) => setDeclineReason(event.target.value)}
                    />
                  </label>
                )}
                <div>
                  <button
                    className="button button-primary"
                    disabled={processing}
                    type="button"
                    onClick={acceptRequest}
                  >
                    {processing ? "Processing..." : "Accept & Create Deal Room"}
                    {!processing && <Icon name="arrow" size={16} />}
                  </button>
                  {declining ? (
                    <>
                      <button
                        className="decline-action"
                        type="button"
                        onClick={() => setDeclining(false)}
                      >
                        Cancel
                      </button>
                      <button
                        className="decline-action confirm"
                        type="button"
                        onClick={confirmDecline}
                      >
                        Confirm decline
                      </button>
                    </>
                  ) : (
                    <button
                      className="decline-action"
                      type="button"
                      onClick={() => setDeclining(true)}
                    >
                      Decline
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="staff-request-state">
                <span>
                  <strong>Request status</strong>
                  {roomActive
                    ? "Accepted · Deal Room active"
                    : `${status} · Awaiting Manager action`}
                </span>
                {roomActive && (
                  <Button onClick={onEnterRoom}>Enter Deal Room</Button>
                )}
              </div>
            )}
          </section>
        </div>
      ) : (
        <section className="inbox-empty">
          <Icon name="mail" size={22} />
          <h2>No {filter.toLowerCase()} requests</h2>
          <p>
            {tab === "sent"
              ? "Your organization has not sent any seller connection requests."
              : `There are no received requests with ${filter.toLowerCase()} status.`}
          </p>
        </section>
      )}
    </main>
  );
}

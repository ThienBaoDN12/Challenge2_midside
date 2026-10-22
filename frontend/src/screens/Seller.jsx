import { useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks";
import {
  capitalize,
  fmtDate,
  fmtField,
  fmtTime,
  fmtValue,
  REQUEST_STATUS,
  timeLeft,
  title,
} from "../format";
import {
  Icon,
  Button,
  FlowSteps,
  Toggle,
  ConnectionStatusBadge,
  FilterSelect,
  ApiStatus,
  ErrorNote,
} from "../shared";

const STATUS_LABEL = {
  published: "Published",
  draft: "Draft",
  paused: "Paused",
  expired: "Expired",
};
// Lifecycle action offered on each listing card (§6)
const NEXT_ACTION = {
  draft: ["Publish", "publishListing"],
  published: ["Pause", "pauseListing"],
  paused: ["Resume", "resumeListing"],
};

export function SellerWorkspace({ role, onCreate }) {
  const [tab, setTab] = useState("listings");
  const [busy, setBusy] = useState(null);
  const [actionError, setActionError] = useState(null);
  const { data, error, loading, reload } = useApi(() => api.myListings());
  const manager = role === "SM" && data?.can_manage !== false;
  const listings = data?.listings ?? [];

  const runAction = async (listing) => {
    const [, fn] = NEXT_ACTION[listing.status];
    setBusy(listing.id);
    setActionError(null);
    try {
      await api[fn](listing.id);
      await reload(true);
    } catch (e) {
      setActionError(e);
    } finally {
      setBusy(null);
    }
  };

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
            Active & drafts <span>{listings.length}</span>
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
      <ErrorNote error={actionError} />

      {tab === "listings" ? (
        <>
          <ApiStatus loading={loading} error={error} onRetry={reload} />
          {data && (
            <section className="listing-grid">
              {listings.map((listing) => {
                const action = NEXT_ACTION[listing.status];
                return (
                  <article className="listing-card" key={listing.id}>
                    <div className="listing-card-head">
                      <span className="listing-id">
                        {listing.id} · {listing.version_label}
                      </span>
                      <span className={`listing-status ${listing.status}`}>
                        {STATUS_LABEL[listing.status]}
                      </span>
                    </div>
                    <h2>{title(listing)}</h2>
                    <div className="public-label">
                      <Icon name="shield" size={13} /> Public
                    </div>
                    <div className="listing-facts">
                      <div>
                        <span>Product</span>
                        <strong>{capitalize(listing.product_type)}</strong>
                      </div>
                      <div>
                        <span>Quantity</span>
                        <strong>
                          {fmtField(listing.public_fields.quantity)}
                        </strong>
                      </div>
                      <div>
                        <span>Valid until</span>
                        <strong>{fmtDate(listing.valid_until)}</strong>
                      </div>
                    </div>
                    <div className="listing-foot">
                      <span>
                        {listing.status === "published"
                          ? `${listing.open_rooms} active room${listing.open_rooms === 1 ? "" : "s"}`
                          : listing.status === "draft"
                            ? "Not visible yet"
                            : "Hidden from search"}
                      </span>
                      {manager && action && (
                        <button
                          type="button"
                          disabled={busy === listing.id}
                          onClick={() => runAction(listing)}
                        >
                          {busy === listing.id ? "Saving…" : action[0]}{" "}
                          <Icon name="arrow" size={14} />
                        </button>
                      )}
                    </div>
                  </article>
                );
              })}
            </section>
          )}
        </>
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
          <span className="tag unverified">Coming in T/H2</span>
        </section>
      )}
    </main>
  );
}

const CATEGORIES = [
  ["Coffee", "coffee_green_v3"],
  ["Black Pepper", "pepper_black_v1"],
  ["Cashew", "cashew_raw_v1"],
  ["Rice", "rice_white_v1"],
];
const DEMO_FILES = [
  ["valid", "Valid file"],
  ["missing_moq", "Missing MOQ"],
  ["extra_column", "Extra column"],
];

function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function ListingUpload({ draft, onUploaded, onContinue, onNavigate }) {
  const [templateId, setTemplateId] = useState("coffee_green_v3");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);
  const { data: templates } = useApi(() => api.templates());
  const template = templates?.find((t) => t.id === templateId);
  const snapshot = draft?.snapshot;

  const upload = async (f) => {
    if (!f) return;
    setFile(f);
    setUploading(true);
    setError(null);
    try {
      onUploaded(await api.uploadFile(templateId, f));
    } catch (e) {
      setError(e);
    } finally {
      setUploading(false);
    }
  };

  const uploadDemo = async (variant) => {
    const content = await api.sampleFile(templateId, variant);
    const blob = new Blob([JSON.stringify(content, null, 2)], {
      type: "application/json",
    });
    upload(new File([blob], `${templateId}_${variant}.json`));
  };

  const download = async () => {
    const json = await api.templateFile(templateId);
    saveBlob(
      new Blob([JSON.stringify(json, null, 2)], { type: "application/json" }),
      `${templateId}.json`,
    );
  };

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
            {CATEGORIES.map(([label, id]) => (
              <button
                className={templateId === id ? "selected" : ""}
                key={id}
                type="button"
                onClick={() => setTemplateId(id)}
              >
                <span className="choice-check">
                  {templateId === id && <Icon name="check" size={13} />}
                </span>
                {label}
              </button>
            ))}
          </div>
          <button className="download-action" type="button" onClick={download}>
            <Icon name="file" size={17} />
            <span>
              Download Fixed Template
              <small>
                {template ? `${template.label} v${template.version}` : ".json"}
              </small>
            </span>
            <Icon name="arrow" size={15} />
          </button>
          <div className="required-list">
            <span>Required fields</span>
            {(template?.fields ?? [])
              .filter((f) => f.required)
              .map((f) => (
                <div key={f.key}>
                  <Icon name="check" size={13} /> {f.label}
                  {f.unit_options.length > 0 &&
                    f.type === "number" &&
                    " & unit"}
                </div>
              ))}
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
            className={`drop-zone ${snapshot && !error ? "uploaded" : ""}`}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              upload(event.dataTransfer.files?.[0]);
            }}
          >
            <input
              type="file"
              accept=".xlsx,.json"
              onChange={(event) => upload(event.target.files?.[0])}
            />
            <span className="upload-icon">
              <Icon name={snapshot && !error ? "check" : "file"} size={24} />
            </span>
            <strong>
              {uploading
                ? "Validating…"
                : file
                  ? file.name
                  : "Drop your completed template here"}
            </strong>
            <span>
              {snapshot && !error && file
                ? `Validated · ${Math.max(1, Math.round(file.size / 1024))} KB · ${snapshot.fields.length} fields`
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
            <span>Demo files</span>
            <div>
              {DEMO_FILES.map(([variant, label]) => (
                <button
                  key={variant}
                  type="button"
                  disabled={uploading}
                  onClick={() => uploadDemo(variant)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          {error && (
            <div className="policy-block error">
              <Icon name="close" size={18} />
              <span>
                <strong>Validation Error</strong>
                {(error.details?.errors ?? [{ message: error.message }])
                  .map((e) => e.message)
                  .join(" ")}
              </span>
            </div>
          )}
          {!error && snapshot?.dropped_columns.length > 0 && (
            <div className="policy-block notice">
              <Icon name="file" size={18} />
              <span>
                <strong>Ignored Fields</strong>
                Unrecognized fields ignored: [
                {snapshot.dropped_columns.join(", ")}].
              </span>
            </div>
          )}
        </section>
      </div>
      <div className="creation-actions">
        <span>
          <Icon name="lock" size={14} /> Private Snapshot
        </span>
        <Button onClick={onContinue} disabled={!snapshot || !!error}>
          Review parsed fields <Icon name="arrow" size={16} />
        </Button>
      </div>
    </main>
  );
}

const TAG_LABEL = {
  standard: "Standard",
  required: "Required",
  sensitive: "Confidential · Encrypted",
  blocked: "Blocked by policy",
};

export function ListingFields({ draft, onChange, onContinue, onNavigate }) {
  const [warning, setWarning] = useState(null); // { type, field }
  if (!draft) return <NoDraft onNavigate={onNavigate} />;
  const { snapshot, publicKeys, confirmed } = draft;

  const setKeys = (keys, extraConfirmed = []) =>
    onChange({
      ...draft,
      publicKeys: keys,
      confirmed: [...new Set([...confirmed, ...extraConfirmed])],
    });

  const requestToggle = (row) => {
    if (row.blocked) return setWarning({ type: "blocked", field: row });
    const on = publicKeys.includes(row.key);
    if (!on && row.sensitive)
      return setWarning({ type: "sensitive", field: row });
    setKeys(
      on ? publicKeys.filter((k) => k !== row.key) : [...publicKeys, row.key],
    );
  };
  const publicCount = snapshot.fields.filter(
    (r) => r.locked_public || publicKeys.includes(r.key),
  ).length;

  return (
    <main className="page creation-page fields-page">
      <div className="creation-heading">
        <div>
          <p className="eyebrow">
            Private snapshot · {snapshot.template_label}
          </p>
          <h1>Choose what becomes public.</h1>
          <p>
            Private by default. Only selected fields can be used by buyers and
            Discovery AI.
          </p>
        </div>
        <FlowSteps current={2} onNavigate={onNavigate} />
      </div>

      {warning?.type === "sensitive" && (
        <div className="sensitive-warning">
          <Icon name="shield" size={20} />
          <span>
            <strong>Sensitive data warning</strong>
            Making {warning.field.label} public exposes it to all buyers and
            Discovery AI. Confirm?
          </span>
          <button type="button" onClick={() => setWarning(null)}>
            Keep private
          </button>
          <Button
            onClick={() => {
              setKeys([...publicKeys, warning.field.key], [warning.field.key]);
              setWarning(null);
            }}
          >
            Confirm
          </Button>
        </div>
      )}
      {warning?.type === "blocked" && (
        <div className="sensitive-warning blocked-warning">
          <Icon name="lock" size={20} />
          <span>
            <strong>Protected by policy</strong>
            {warning.field.label} cannot be made public under platform privacy
            policy.
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
        {snapshot.fields.map((row) => {
          const isPublic = row.locked_public || publicKeys.includes(row.key);
          return (
            <div className="parsed-row" key={row.key}>
              <span className="parsed-name">
                {row.label}
                {row.locked_public && (
                  <small>
                    <Icon name="lock" size={11} /> Minimum field
                  </small>
                )}
              </span>
              <strong>{fmtValue(row.value)}</strong>
              <span>{row.unit ?? "—"}</span>
              <span>
                <span
                  className={`data-tag ${row.sensitive || row.blocked ? "confidential" : "standard"}`}
                >
                  {TAG_LABEL[row.tag]}
                </span>
              </span>
              <span className="visibility-control">
                <span>{isPublic ? "Public" : "Private"}</span>
                <Toggle
                  checked={isPublic}
                  locked={row.locked_public}
                  label={`${row.label} ${isPublic ? "public" : "private"}`}
                  onChange={() => requestToggle(row)}
                />
              </span>
            </div>
          );
        })}
      </section>
      <div className="creation-actions">
        <span>
          <Icon name="shield" size={14} /> {publicCount} public ·{" "}
          {snapshot.fields.length - publicCount} private
        </span>
        <Button onClick={onContinue}>
          Preview listing <Icon name="arrow" size={16} />
        </Button>
      </div>
    </main>
  );
}

function NoDraft({ onNavigate }) {
  return (
    <main className="page creation-page">
      <section className="inbox-empty">
        <Icon name="file" size={22} />
        <h2>Upload a confidential file first</h2>
        <p>The private snapshot is created from your uploaded template.</p>
        <Button onClick={() => onNavigate("listing-upload")}>
          Go to upload
        </Button>
      </section>
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

export function ListingPublish({ draft, onNavigate, onDone }) {
  const [result, setResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const body = draft && {
    snapshot_id: draft.snapshot.id,
    public_keys: draft.publicKeys,
    confirm_sensitive: draft.confirmed,
  };
  const preview = useApi(
    () => (body ? api.previewListing(body) : Promise.resolve(null)),
    [draft],
  );
  if (!draft) return <NoDraft onNavigate={onNavigate} />;

  const save = async (publish) => {
    setSaving(true);
    setSaveError(null);
    try {
      setResult(await api.createListing({ ...body, publish }));
    } catch (e) {
      setSaveError(e);
    } finally {
      setSaving(false);
    }
  };

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

      {result && (
        <div className="version-banner">
          <span className="version-check">
            <Icon name="check" size={16} />
          </span>
          <span>
            <strong>
              {result.id} {result.version_label}{" "}
              {result.status === "published" ? "published" : "saved as draft"}
            </strong>
            {result.status === "published"
              ? "Buyers and Discovery AI can now find the public fields."
              : "Not visible to buyers until you publish it."}
          </span>
          <Button kind="secondary" onClick={onDone}>
            Back to listings
          </Button>
        </div>
      )}
      <ErrorNote error={saveError || preview.error} />

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
            {preview.data?.public.map((f) => (
              <PreviewField
                key={f.key}
                label={f.label}
                value={fmtValue(f.value, f.unit)}
              />
            ))}
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
            {preview.data?.private.map((f) => {
              const row = draft.snapshot.fields.find((r) => r.key === f.key);
              return (
                <PreviewField
                  key={f.key}
                  label={f.label}
                  value={fmtValue(row?.value, row?.unit)}
                />
              );
            })}
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
        {!result && (
          <div>
            <Button kind="ghost" disabled={saving} onClick={() => save(false)}>
              Save Draft
            </Button>
            <Button disabled={saving} onClick={() => save(true)}>
              {saving ? "Publishing…" : "Publish Listing"}{" "}
              <Icon name="arrow" size={16} />
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}

const FILTERS = ["Pending", "Accepted", "Declined", "Expired", "Withdrawn"];

export function SellerConnectionInbox({ role, onEnterRoom }) {
  const manager = role === "SM";
  const [tab, setTab] = useState("received");
  const [filter, setFilter] = useState("Pending");
  const [selectedId, setSelectedId] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [declining, setDeclining] = useState(false);
  const [declineReason, setDeclineReason] = useState("");
  const [actionError, setActionError] = useState(null);
  const [createdRoom, setCreatedRoom] = useState(null);

  const list = useApi(
    () => api.connections(tab, filter.toLowerCase()),
    [tab, filter],
    5000,
  );
  const requests = list.data ?? [];
  const selected = requests.find((r) => r.id === selectedId) ?? requests[0];
  const detail = useApi(
    () => (selected ? api.connection(selected.id) : Promise.resolve(null)),
    [selected?.id, selected?.status],
  );
  const req = detail.data;

  const accept = async (confirmVersion) => {
    if (processing) return;
    setProcessing(true);
    setActionError(null);
    try {
      const res = await api.acceptConnection(req.id, confirmVersion);
      setCreatedRoom(res.room_id);
      setFilter("Accepted");
    } catch (e) {
      setActionError(e);
    } finally {
      setProcessing(false);
    }
  };
  const confirmDecline = async () => {
    setActionError(null);
    try {
      await api.declineConnection(req.id, declineReason || null);
      setDeclining(false);
      setFilter("Declined");
    } catch (e) {
      setActionError(e);
    }
  };

  // Diff rows: from 409 details on accept, or from the request view
  const changes = actionError?.details?.changes ?? req?.changes ?? [];
  const confirmVersion = actionError?.details?.confirm_version;

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

      {createdRoom && (
        <div className="deal-room-banner">
          <span>
            <Icon name="check" size={16} />
          </span>
          <div>
            <strong>Deal Room {createdRoom} Created</strong>
            <small>
              The buyer has been notified and the request snapshot is preserved.
            </small>
          </div>
          <Button kind="secondary" onClick={() => onEnterRoom(createdRoom)}>
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
            Received {tab === "received" && <span>{requests.length}</span>}
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
          <FilterSelect value={filter} options={FILTERS} onChange={setFilter} />
        </div>
      </div>

      <ApiStatus
        loading={list.loading && !list.data}
        error={list.error}
        onRetry={list.reload}
      />

      {list.data && requests.length > 0 && req ? (
        <div className="seller-request-layout">
          <section className="request-list-card">
            {requests.map((r) => (
              <button
                type="button"
                key={r.id}
                className="request-list-head"
                style={{
                  width: "100%",
                  border: 0,
                  background: "none",
                  textAlign: "left",
                  cursor: "pointer",
                  opacity: r.id === req.id ? 1 : 0.6,
                }}
                onClick={() => {
                  setSelectedId(r.id);
                  setActionError(null);
                  setDeclining(false);
                }}
              >
                <span className="member-avatar">
                  {r.buyer_org.slice(0, 2).toUpperCase()}
                </span>
                <div>
                  <h2>{r.buyer_org}</h2>
                  <p>
                    {r.id} · {r.listing_id}
                  </p>
                </div>
                <ConnectionStatusBadge
                  status={REQUEST_STATUS[r.status]}
                  detail={
                    r.status === "pending"
                      ? timeLeft(r.expires_at)
                      : (r.room_id ?? undefined)
                  }
                />
              </button>
            ))}
            <div className="request-listing-ref">
              <span>Listing requested</span>
              <strong>
                {req.listing_id} · {req.listing_snapshot.product?.value} ·{" "}
                {fmtField(req.listing_snapshot.quantity)}
              </strong>
              <small>
                Snapshot at time of request · v{req.listing_version}
              </small>
            </div>
            <div className="request-timestamp">
              Received {fmtDate(req.created_at.slice(0, 10))} ·{" "}
              {fmtTime(req.created_at)}
            </div>
          </section>

          <section className="request-detail">
            <div className="request-detail-head">
              <div>
                <p className="eyebrow">Request detail · {req.id}</p>
                <h2>{req.buyer_org} · Cambodia</h2>
              </div>
              <span className="data-tag private">Private Snapshot</span>
            </div>

            <div className="buyer-message">
              <span>Buyer’s message</span>
              <p>“{req.message || "No message"}”</p>
            </div>

            {changes.length > 0 && (
              <div className="listing-change-warning">
                <div className="change-warning-head">
                  <span>
                    <Icon name="file" size={17} />
                  </span>
                  <div>
                    <strong>Listing Changed After Request</strong>
                    <p>
                      {req.listing_id} was updated to v
                      {req.current_listing_version}. Review the field diff
                      before accepting.
                    </p>
                  </div>
                  <span className="tag unverified">
                    v{req.listing_version} → v{req.current_listing_version}
                  </span>
                </div>
                <div className="version-diff">
                  <div className="diff-column old">
                    <span>Snapshot requested · v{req.listing_version}</span>
                    {changes.map((c) => (
                      <div key={c.key}>
                        <small>{c.label}</small>
                        <strong>
                          {c.before
                            ? fmtValue(c.before.value, c.before.unit)
                            : "Not public"}
                        </strong>
                      </div>
                    ))}
                  </div>
                  <div className="diff-arrow">
                    <Icon name="arrow" size={17} />
                  </div>
                  <div className="diff-column new">
                    <span>
                      Current listing · v{req.current_listing_version}
                    </span>
                    {changes.map((c) => (
                      <div key={c.key}>
                        <small>{c.label}</small>
                        <strong>
                          {c.after
                            ? fmtValue(c.after.value, c.after.unit)
                            : "Not public"}
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {actionError && !confirmVersion && (
              <ErrorNote error={actionError} />
            )}

            {manager && req.status === "pending" ? (
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
                    onClick={() =>
                      accept(
                        confirmVersion ??
                          (req.listing_changed
                            ? req.current_listing_version
                            : undefined),
                      )
                    }
                  >
                    {processing
                      ? "Processing..."
                      : req.listing_changed
                        ? `Accept v${req.current_listing_version} & Create Deal Room`
                        : "Accept & Create Deal Room"}
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
                  {req.room_id
                    ? `Accepted · Deal Room ${req.room_id} active`
                    : req.status === "pending"
                      ? "Pending · Awaiting Manager action"
                      : `${REQUEST_STATUS[req.status]}${req.reason ? ` · “${req.reason}”` : ""}`}
                </span>
                {req.room_id && (
                  <Button onClick={() => onEnterRoom(req.room_id)}>
                    Enter Deal Room
                  </Button>
                )}
              </div>
            )}
          </section>
        </div>
      ) : (
        list.data && (
          <section className="inbox-empty">
            <Icon name="mail" size={22} />
            <h2>No {filter.toLowerCase()} requests</h2>
            <p>
              {tab === "sent"
                ? "Your organization has not sent any connection requests."
                : `There are no received requests with ${filter.toLowerCase()} status.`}
            </p>
          </section>
        )
      )}
    </main>
  );
}

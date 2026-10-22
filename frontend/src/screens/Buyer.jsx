import { useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks";
import {
  fmtDate,
  fmtField,
  fmtTime,
  initials,
  REQUEST_STATUS,
  timeLeft,
  title,
} from "../format";
import { PreviewField } from "./Seller";
import {
  Icon,
  Button,
  Field,
  SelectField,
  ConnectionStatusBadge,
  FilterSelect,
  ApiStatus,
  ErrorNote,
} from "../shared";

function ago(iso) {
  const mins = Math.round((Date.now() - new Date(iso)) / 60000);
  if (mins < 60) return `${Math.max(1, mins)}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return fmtDate(iso.slice(0, 10));
}

export function DiscoveryCard({ result, onOpen }) {
  const listing = result.listing ?? result;
  const pf = listing.public_fields;
  return (
    <article className="discovery-card">
      <div className="discovery-card-head">
        <span>
          {listing.id} · {listing.version_label}
        </span>
        {result.score !== undefined && (
          <span className="match-score">{result.score}% match</span>
        )}
      </div>
      <h3>{pf.product?.value}</h3>
      <p>
        {listing.seller.name} ·{" "}
        <strong>
          {listing.seller.business_verified
            ? "Business Verified"
            : "Business Unverified"}
        </strong>
      </p>
      <div className="discovery-facts">
        <div>
          <span>Quantity</span>
          <strong>{fmtField(pf.quantity)}</strong>
        </div>
        <div>
          <span>Available until</span>
          <strong>{fmtDate(listing.valid_until)}</strong>
        </div>
        <div>
          <span>Loading port</span>
          <strong>{fmtField(pf.port_of_loading)}</strong>
        </div>
      </div>
      {result.matched && (
        <div className="criteria-list">
          {result.matched.map((criterion) => (
            <span className="criteria matched" key={criterion}>
              <Icon name="check" size={12} /> {criterion}
            </span>
          ))}
          {result.unmet.map((criterion) => (
            <span className="criteria unmet" key={criterion}>
              <Icon name="alert" size={14} /> {criterion}
            </span>
          ))}
        </div>
      )}
      <div className="discovery-card-foot">
        <span>Updated {ago(listing.updated_at)}</span>
        <button type="button" onClick={() => onOpen(listing.id)}>
          View public listing <Icon name="arrow" size={14} />
        </button>
      </div>
    </article>
  );
}

const PROMPTS = [
  "Robusta Coffee 20 tons delivered to Phnom Penh before 30/11",
  "Robusta Coffee delivered to Phnom Penh",
  "Durian 100 tons before Dec 1",
];
const PRODUCTS = [
  ["coffee", "Coffee"],
  ["pepper", "Black Pepper"],
  ["cashew", "Cashew"],
  ["rice", "Rice"],
];

export function BuyerWorkspace({ onOpenListing }) {
  const [mode, setMode] = useState("ai");
  const [query, setQuery] = useState(PROMPTS[0]);
  const [criteria, setCriteria] = useState(null);
  const [ai, setAi] = useState(null);
  const [aiError, setAiError] = useState(null);
  const [searching, setSearching] = useState(false);
  const [filters, setFilters] = useState({
    product_type: "coffee",
    min_quantity: "20",
    unit: "ton",
    available_before: "2026-11-30",
  });
  const [standard, setStandard] = useState(null);

  const runAi = async (text, extra = null, relax = null) => {
    setSearching(true);
    setAiError(null);
    try {
      const merged = extra ? { ...(criteria ?? {}), ...extra } : null;
      const res = await api.discover(text, merged, relax);
      setCriteria(res.status === "needs_clarification" ? res.criteria : merged);
      setAi(res);
    } catch (e) {
      setAiError(e);
    } finally {
      setSearching(false);
    }
  };
  const runStandard = async () => {
    setSearching(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== ""),
      );
      setStandard(await api.search(params));
    } catch (e) {
      setStandard({ results: [], error: e });
    } finally {
      setSearching(false);
    }
  };

  return (
    <main className="page workspace-page discovery-page">
      <div className="workspace-heading discovery-heading">
        <div>
          <p className="eyebrow">Buyer workspace</p>
          <h1>Find the right seller, faster.</h1>
          <p>
            Discovery AI searches public listing fields only. Private snapshots
            remain inaccessible.
          </p>
        </div>
        <div className="discovery-mode" role="tablist">
          <button
            className={mode === "ai" ? "active" : ""}
            type="button"
            onClick={() => setMode("ai")}
          >
            <Icon name="spark" size={15} /> AI Discovery
          </button>
          <button
            className={mode === "standard" ? "active" : ""}
            type="button"
            onClick={() => setMode("standard")}
          >
            Standard Search
          </button>
        </div>
      </div>

      <div className="ai-disclaimer">
        <Icon name="shield" size={15} />
        AI suggestions are not connection requests or binding commitments.
      </div>

      {mode === "standard" ? (
        <section className="standard-search">
          <div>
            <p className="eyebrow">Standard search</p>
            <h2>Filter public listings</h2>
          </div>
          <div className="standard-filters">
            <SelectField
              label="Product"
              value={filters.product_type}
              onChange={(v) => setFilters({ ...filters, product_type: v })}
            >
              {PRODUCTS.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </SelectField>
            <Field
              label="Quantity"
              value={filters.min_quantity}
              onChange={(v) => setFilters({ ...filters, min_quantity: v })}
            />
            <SelectField
              label="Unit"
              value={filters.unit}
              onChange={(v) => setFilters({ ...filters, unit: v })}
            >
              <option value="ton">Tons</option>
              <option value="kg">Kilograms</option>
            </SelectField>
            <Field
              label="Available until at least"
              type="date"
              value={filters.available_before}
              onChange={(v) => setFilters({ ...filters, available_before: v })}
            />
            <Button onClick={runStandard} disabled={searching}>
              {searching ? "Searching…" : "Search listings"}
            </Button>
          </div>
          <div className="standard-results">
            {standard?.results.map((listing) => (
              <DiscoveryCard
                result={listing}
                key={listing.id}
                onOpen={onOpenListing}
              />
            ))}
            {standard && standard.results.length === 0 && (
              <p>No public listing matches these filters.</p>
            )}
          </div>
        </section>
      ) : (
        <section className="ai-chat">
          <div className="ai-chat-top">
            <span className="ai-avatar">
              <Icon name="spark" size={19} />
            </span>
            <div>
              <h2>TrustGate Discovery AI</h2>
              <p>Matches transparent criteria against public seller data.</p>
            </div>
            <span className="ai-online">
              <span /> Public data only
            </span>
          </div>

          <div className="quick-prompts">
            <span>Try a prompt</span>
            {PROMPTS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => {
                  setQuery(p);
                  setCriteria(null);
                  runAi(p);
                }}
              >
                {p}
              </button>
            ))}
          </div>

          <form
            className="ai-query"
            onSubmit={(event) => {
              event.preventDefault();
              setCriteria(null);
              runAi(query);
            }}
          >
            <Icon name="spark" size={17} />
            <input
              aria-label="Ask Discovery AI"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit" disabled={searching}>
              {searching ? "Searching…" : "Search"}{" "}
              <Icon name="arrow" size={14} />
            </button>
          </form>

          <ErrorNote error={aiError} />

          {ai?.status === "needs_clarification" && (
            <div className="ai-response followup-response">
              <span className="ai-avatar">
                <Icon name="spark" size={18} />
              </span>
              <div>
                <strong>{ai.question}</strong>
                <p>
                  I need this to compare your request accurately against public
                  listings.
                </p>
                <div className="quick-replies">
                  {ai.quick_replies.map((reply) => (
                    <button
                      key={reply.label}
                      type="button"
                      onClick={() => runAi(query, reply.value)}
                    >
                      {reply.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {ai?.status === "ok" && (
            <div className="matched-results">
              <div className="results-heading">
                <div>
                  <span className="section-kicker">
                    {ai.results.length} public match
                    {ai.results.length === 1 ? "" : "es"}
                  </span>
                  <h2>Best matches for your criteria</h2>
                </div>
                <span>{ai.notice}</span>
              </div>
              <div className="discovery-grid">
                {ai.results.map((r) => (
                  <DiscoveryCard
                    result={r}
                    key={r.listing.id}
                    onOpen={onOpenListing}
                  />
                ))}
              </div>
            </div>
          )}

          {ai?.status === "no_results" && (
            <div className="zero-results">
              <span className="zero-icon">
                <Icon name="spark" size={23} />
              </span>
              <h2>No seller currently matches all criteria.</h2>
              <p>{ai.message} I won’t invent or infer unavailable sellers.</p>
              {ai.relaxation && (
                <button
                  type="button"
                  onClick={() => runAi(query, criteria, ai.relaxation.apply)}
                >
                  {ai.relaxation.description}
                </button>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}

export function ConnectionDrawer({ listing, open, onClose }) {
  const [acknowledged, setAcknowledged] = useState(false);
  const [message, setMessage] = useState(
    "Hello, we are interested in discussing availability and delivery to Phnom Penh before November 30.",
  );
  const [sent, setSent] = useState(null);
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);
  if (!open) return null;
  const send = async () => {
    setSending(true);
    setError(null);
    try {
      setSent(await api.connect(listing.id, message));
    } catch (e) {
      setError(e);
    } finally {
      setSending(false);
    }
  };
  return (
    <div className="drawer-layer" role="dialog" aria-modal="true">
      <button
        aria-label="Close connection request"
        className="drawer-backdrop"
        type="button"
        onClick={onClose}
      />
      <aside className="connection-drawer">
        <div className="drawer-head">
          <div>
            <p className="eyebrow">Connection request</p>
            <h2>{listing.seller.name}</h2>
          </div>
          <button type="button" onClick={onClose}>
            <Icon name="close" size={18} />
          </button>
        </div>
        {sent ? (
          <div className="request-sent">
            <span>
              <Icon name="check" size={21} />
            </span>
            <h2>Request {sent.id} sent</h2>
            <p>
              {listing.seller.name} will receive your message. No inventory has
              been reserved. The request expires in 7 days.
            </p>
            <Button kind="secondary" onClick={onClose}>
              Done
            </Button>
          </div>
        ) : (
          <>
            <div className="request-summary">
              <span>
                {listing.id} · {listing.version_label}
              </span>
              <strong>{title(listing)}</strong>
            </div>
            <label className="field">
              <span>Message</span>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={6}
              />
            </label>
            <label className="acknowledgement">
              <input
                checked={acknowledged}
                type="checkbox"
                onChange={(event) => setAcknowledged(event.target.checked)}
              />
              <span>
                I understand a connection is not a contract and does not reserve
                inventory
              </span>
            </label>
            <ErrorNote error={error} />
            <button
              className="button button-primary drawer-submit"
              disabled={!acknowledged || sending}
              type="button"
              onClick={send}
            >
              {sending ? "Sending…" : "Send Request"}{" "}
              <Icon name="arrow" size={16} />
            </button>
          </>
        )}
      </aside>
    </div>
  );
}

export function BuyerDetail({ role, listingId, onBack }) {
  const manager = role === "BM";
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [note, setNote] = useState(
    "Strong quantity and delivery match. Please review supplier verification.",
  );
  const [recommended, setRecommended] = useState(false);
  const [error, setError] = useState(null);
  const {
    data: listing,
    error: loadError,
    loading,
    reload,
  } = useApi(() => api.listing(listingId), [listingId]);

  const recommend = async () => {
    setError(null);
    try {
      await api.propose(listingId, note);
      setRecommended(true);
    } catch (e) {
      setError(e);
    }
  };

  if (!listing)
    return (
      <main className="page workspace-page buyer-detail-page">
        <button className="back-action" type="button" onClick={onBack}>
          <Icon name="arrow" size={14} /> Back to discovery
        </button>
        <ApiStatus loading={loading} error={loadError} onRetry={reload} />
      </main>
    );

  const verified = listing.seller.business_verified;
  return (
    <main className="page workspace-page buyer-detail-page">
      <button className="back-action" type="button" onClick={onBack}>
        <Icon name="arrow" size={14} /> Back to discovery
      </button>
      <section className="seller-profile">
        <div className="seller-monogram">{initials(listing.seller.name)}</div>
        <div>
          <p className="eyebrow">Seller organization</p>
          <h1>{listing.seller.name}</h1>
          <p>
            {listing.seller.country} ·{" "}
            {verified ? "Business Verified" : "Business Unverified"}
          </p>
        </div>
        <div className="seller-badges">
          <span className="tag verified">
            <Icon name="check" size={13} /> Email Verified
          </span>
          <span className={`tag ${verified ? "verified" : "unverified"}`}>
            {verified ? "Business Verified" : "Business Unverified"}
          </span>
        </div>
      </section>

      <div className="detail-layout">
        <section className="public-detail">
          <div className="detail-title">
            <div>
              <span className="section-kicker">
                {listing.id} · {listing.version_label}
              </span>
              <h2>{listing.public_fields.product?.value}</h2>
            </div>
            <span className="data-tag public">Public</span>
          </div>
          <p>
            All information below is explicitly public and available to buyers
            and Discovery AI.
          </p>
          <div className="public-field-grid">
            {Object.entries(listing.public_fields).map(([key, f]) => (
              <PreviewField key={key} label={f.label} value={fmtField(f)} />
            ))}
          </div>
        </section>

        <aside className="buyer-action-area">
          <p className="eyebrow">
            {manager ? "Manager action" : "Staff recommendation"}
          </p>
          <h2>
            {manager
              ? "Interested in this listing?"
              : "Share this match with your manager."}
          </h2>
          <p>
            {manager
              ? "Start a private conversation with the seller. This does not create a contract or reserve stock."
              : "Add context to help your manager evaluate and contact this seller."}
          </p>
          {manager ? (
            <Button onClick={() => setDrawerOpen(true)}>
              Send Connection Request <Icon name="arrow" size={16} />
            </Button>
          ) : recommended ? (
            <span className="approval-pill">
              <Icon name="clock" size={14} /> Awaiting Manager Approval
            </span>
          ) : (
            <>
              <label className="field">
                <span>Recommendation note</span>
                <textarea
                  rows={5}
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                />
              </label>
              <Button kind="secondary" onClick={recommend}>
                Recommend to Manager <Icon name="arrow" size={16} />
              </Button>
            </>
          )}
          <ErrorNote error={error} />
          <div className="action-assurance">
            <Icon name="shield" size={15} />
            <span>
              <strong>Public data only</strong>
              Confidential seller fields remain hidden
            </span>
          </div>
        </aside>
      </div>
      <ConnectionDrawer
        listing={listing}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </main>
  );
}

export function BuyerRecommendations() {
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(null);
  const {
    data,
    error: loadError,
    loading,
    reload,
  } = useApi(() => api.proposals(), [], 5000);
  const recommendations = (data ?? []).filter((p) => p.status === "pending");

  const act = async (item, action) => {
    setBusy(item.id);
    setError(null);
    try {
      if (action === "send") await api.sendProposal(item.id, item.note);
      else await api.dismissProposal(item.id);
      await reload(true);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="page workspace-page recommendations-page">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">Manager review</p>
          <h1>Staff recommendations</h1>
          <p>
            Review seller listings your team shortlisted from public discovery
            results.
          </p>
        </div>
      </div>
      <ErrorNote error={error} />
      <ApiStatus
        loading={loading && !data}
        error={loadError}
        onRetry={reload}
      />

      {data && recommendations.length === 0 ? (
        <section className="recommendations-empty">
          <span>
            <Icon name="check" size={22} />
          </span>
          <h2>You’re all caught up.</h2>
          <p>There are no staff recommendations waiting for manager review.</p>
        </section>
      ) : (
        <section className="recommendation-list">
          {recommendations.map((item) => (
            <article className="recommendation-item" key={item.id}>
              <div className="recommendation-meta">
                <span className="member-avatar">{initials(item.by_name)}</span>
                <span>
                  <strong>{item.by_name}</strong>
                  <small>
                    {fmtDate(item.created_at.slice(0, 10))} ·{" "}
                    {fmtTime(item.created_at)}
                  </small>
                </span>
              </div>
              <div className="recommendation-note">
                <span>Staff note</span>
                <p>“{item.note}”</p>
              </div>
              <div className="recommendation-listing">
                <span>{item.listing_id}</span>
                <strong>{item.listing?.public_fields.product?.value}</strong>
                <small>
                  {item.listing?.seller.name} ·{" "}
                  {fmtField(item.listing?.public_fields.quantity)}
                </small>
              </div>
              <div className="recommendation-actions">
                <Button
                  disabled={busy === item.id}
                  onClick={() => act(item, "send")}
                >
                  Send Connection Request
                </Button>
                <button
                  type="button"
                  disabled={busy === item.id}
                  onClick={() => act(item, "dismiss")}
                >
                  Dismiss
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}

export function BuyerConnectionInbox({ role, onEnterRoom }) {
  const manager = role === "BM";
  const [filter, setFilter] = useState("All");
  const [error, setError] = useState(null);
  const {
    data,
    error: loadError,
    loading,
    reload,
  } = useApi(() => api.connections("sent"), [], 5000);
  const all = data ?? [];
  const requests = all.filter(
    (r) => filter === "All" || REQUEST_STATUS[r.status] === filter,
  );
  const count = (s) => all.filter((r) => r.status === s).length;

  const withdraw = async (id) => {
    setError(null);
    try {
      await api.withdrawConnection(id);
      await reload(true);
    } catch (e) {
      setError(e);
    }
  };

  return (
    <main className="page workspace-page connection-page">
      <div className="workspace-heading connection-heading">
        <div>
          <p className="eyebrow">Buyer connections</p>
          <h1>Sent requests</h1>
          <p>
            Track seller responses and enter active Deal Rooms from one place.
          </p>
        </div>
        <span className="expiry-note">
          <Icon name="clock" size={14} /> Pending requests expire after 7 days
        </span>
      </div>

      <div className="buyer-inbox-summary">
        <div>
          <strong>{count("pending")}</strong>
          <span>Pending</span>
        </div>
        <div>
          <strong>{count("accepted")}</strong>
          <span>Active Deal Room</span>
        </div>
        <div>
          <strong>{all.length}</strong>
          <span>Total requests</span>
        </div>
        <div className="status-filters">
          <FilterSelect
            value={filter}
            options={["All", ...Object.values(REQUEST_STATUS)]}
            onChange={setFilter}
          />
        </div>
      </div>
      <ErrorNote error={error} />
      <ApiStatus
        loading={loading && !data}
        error={loadError}
        onRetry={reload}
      />

      {data && requests.length === 0 && (
        <section className="inbox-empty">
          <Icon name="mail" size={22} />
          <h2>No requests yet</h2>
          <p>Use Discovery to find a seller and send a connection request.</p>
        </section>
      )}

      <section className="buyer-request-list">
        {requests.map((request) => (
          <article className="buyer-request-item" key={request.id}>
            <div className="request-identity">
              <span className="member-avatar">
                {request.seller_org.slice(0, 2).toUpperCase()}
              </span>
              <span>
                <strong>{request.seller_org}</strong>
                <small>
                  {request.id} · Sent by {request.buyer_org}
                </small>
              </span>
            </div>
            <div className="buyer-request-listing">
              <span>Public listing</span>
              <strong>
                {request.listing_id} · {request.listing_snapshot.product?.value}{" "}
                {fmtField(request.listing_snapshot.quantity)}
              </strong>
            </div>
            <div>
              <ConnectionStatusBadge
                status={REQUEST_STATUS[request.status]}
                detail={
                  request.status === "pending"
                    ? timeLeft(request.expires_at)
                    : (request.room_id ?? undefined)
                }
              />
              {request.reason && (
                <p className="decline-reason">“{request.reason}”</p>
              )}
            </div>
            <div className="buyer-request-actions">
              {request.room_id && (
                <Button
                  kind="secondary"
                  onClick={() => onEnterRoom(request.room_id)}
                >
                  Enter Deal Room {request.room_id}
                </Button>
              )}
              {manager && request.can_withdraw && (
                <button type="button" onClick={() => withdraw(request.id)}>
                  Withdraw Request
                </button>
              )}
              {!manager && !request.room_id && <span>Read-only status</span>}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

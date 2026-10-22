import { useState } from "react";
import { PreviewField } from "./Seller";
import {
  Icon,
  Button,
  Field,
  SelectField,
  ConnectionStatusBadge,
  FilterSelect,
} from "../shared";
export const buyerMatches = [
  {
    id: "LST-VN-0161",
    seller: "Mekong Agro Export",
    status: "Business Unverified",
    product: "Robusta Coffee Grade 1",
    quantity: "20 Tons",
    validity: "Nov 30, 2026",
    port: "Cat Lai, HCMC",
    score: "94%",
    matched: ["Product", "Quantity", "Delivery window"],
    unmet: "Freight to Phnom Penh unverified",
  },
  {
    id: "LST-VN-0154",
    seller: "Dak Lak Cooperative",
    status: "Business Verified",
    product: "Robusta Coffee Screen 18",
    quantity: "35 Tons",
    validity: "Dec 10, 2026",
    port: "Cat Lai, HCMC",
    score: "89%",
    matched: ["Product", "Quantity"],
    unmet: "Delivery date requires confirmation",
  },
  {
    id: "LST-VN-0147",
    seller: "Highland Origin Co.",
    status: "Business Unverified",
    product: "Robusta Coffee Grade 1",
    quantity: "24 Tons",
    validity: "Dec 15, 2026",
    port: "Da Nang",
    score: "82%",
    matched: ["Product", "Minimum quantity"],
    unmet: "Port preference unmet",
  },
];
export function DiscoveryCard({ listing, onOpen }) {
  return (
    <article className="discovery-card">
      <div className="discovery-card-head">
        <span>{listing.id}</span>
        <span className="match-score">{listing.score} match</span>
      </div>
      <h3>{listing.product}</h3>
      <p>
        {listing.seller} · <strong>{listing.status}</strong>
      </p>
      <div className="discovery-facts">
        <div>
          <span>Quantity</span>
          <strong>{listing.quantity}</strong>
        </div>
        <div>
          <span>Available before</span>
          <strong>{listing.validity}</strong>
        </div>
        <div>
          <span>Loading port</span>
          <strong>{listing.port}</strong>
        </div>
      </div>
      <div className="criteria-list">
        {listing.matched.map((criterion) => (
          <span className="criteria matched" key={criterion}>
            <Icon name="check" size={12} /> {criterion}
          </span>
        ))}
        <span className="criteria unmet">
          <Icon name="alert" size={14} /> {listing.unmet}
        </span>
      </div>
      <div className="discovery-card-foot">
        <span>Updated 2h ago</span>
        <button type="button" onClick={onOpen}>
          View public listing <Icon name="arrow" size={14} />
        </button>
      </div>
    </article>
  );
}
export function BuyerWorkspace({ role, onOpenListing }) {
  const [mode, setMode] = useState("ai");
  const [query, setQuery] = useState(
    "Robusta Coffee 20 tons delivered to Phnom Penh before Nov 30",
  );
  const [aiState, setAiState] = useState("results");
  const submitQuery = (event) => {
    event.preventDefault();
    if (/cashew|500/i.test(query)) {
      setAiState("zero");
    } else if (!/\d+\s*(tons?|kg)/i.test(query)) {
      setAiState("followup");
    } else {
      setAiState("results");
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
            <SelectField label="Product" value="Robusta Coffee">
              <option>Robusta Coffee</option>
              <option>Black Pepper</option>
              <option>Cashew</option>
              <option>Rice</option>
            </SelectField>
            <Field label="Quantity" value="20" />
            <SelectField label="Unit" value="Tons">
              <option>Tons</option>
              <option>Kilograms</option>
            </SelectField>
            <Field label="Available before date" value="2026-11-30" />
            <Button>Search listings</Button>
          </div>
          <div className="standard-results">
            {buyerMatches.slice(0, 2).map((listing) => (
              <DiscoveryCard
                listing={listing}
                key={listing.id}
                onOpen={onOpenListing}
              />
            ))}
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
            <button
              type="button"
              onClick={() => {
                setQuery(
                  "Robusta Coffee 20 tons delivered to Phnom Penh before Nov 30",
                );
                setAiState("results");
              }}
            >
              Robusta Coffee 20 tons delivered to Phnom Penh before Nov 30
            </button>
            <button
              type="button"
              onClick={() => {
                setQuery("Robusta Coffee delivered to Phnom Penh");
                setAiState("followup");
              }}
            >
              Robusta Coffee delivered to Phnom Penh
            </button>
            <button
              type="button"
              onClick={() => {
                setQuery("Organic cashew 500 tons before Oct 1");
                setAiState("zero");
              }}
            >
              Organic cashew 500 tons before Oct 1
            </button>
          </div>

          <form className="ai-query" onSubmit={submitQuery}>
            <Icon name="spark" size={17} />
            <input
              aria-label="Ask Discovery AI"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit">
              Search <Icon name="arrow" size={14} />
            </button>
          </form>

          {aiState === "followup" && (
            <div className="ai-response followup-response">
              <span className="ai-avatar">
                <Icon name="spark" size={18} />
              </span>
              <div>
                <strong>What quantity do you need, and in which unit?</strong>
                <p>
                  I need both values to compare your request accurately against
                  public listings.
                </p>
                <div className="quick-replies">
                  {["10 Tons", "20 Tons", "50 Tons"].map((reply) => (
                    <button
                      key={reply}
                      type="button"
                      onClick={() => {
                        setQuery(`${query} · ${reply}`);
                        setAiState("results");
                      }}
                    >
                      {reply}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {aiState === "results" && (
            <div className="matched-results">
              <div className="results-heading">
                <div>
                  <span className="section-kicker">3 public matches</span>
                  <h2>Best matches for your criteria</h2>
                </div>
                <span>Ranked by verified public fields</span>
              </div>
              <div className="discovery-grid">
                {buyerMatches.map((listing) => (
                  <DiscoveryCard
                    listing={listing}
                    key={listing.id}
                    onOpen={onOpenListing}
                  />
                ))}
              </div>
            </div>
          )}

          {aiState === "zero" && (
            <div className="zero-results">
              <span className="zero-icon">
                <Icon name="spark" size={23} />
              </span>
              <h2>No seller currently matches all criteria.</h2>
              <p>
                I found no public listing that meets this product, quantity, and
                delivery window. I won’t invent or infer unavailable sellers.
              </p>
              <button
                type="button"
                onClick={() => {
                  setQuery("Organic cashew 500 tons before Dec 15");
                  setAiState("results");
                }}
              >
                Relax delivery date criteria to Dec 15?
              </button>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
export function ConnectionDrawer({ open, onClose }) {
  const [acknowledged, setAcknowledged] = useState(false);
  const [sent, setSent] = useState(false);
  if (!open) return null;
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
            <h2>Mekong Agro Export</h2>
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
            <h2>Request sent</h2>
            <p>
              Mekong Agro Export will receive your message. No inventory has
              been reserved.
            </p>
            <Button kind="secondary" onClick={onClose}>
              Done
            </Button>
          </div>
        ) : (
          <>
            <div className="request-summary">
              <span>LST-VN-0161 · v1</span>
              <strong>Robusta Coffee Grade 1 · 20 Tons</strong>
            </div>
            <label className="field">
              <span>Message</span>
              <textarea
                defaultValue="Hello, we are interested in discussing availability and delivery to Phnom Penh before November 30."
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
            <button
              className="button button-primary drawer-submit"
              disabled={!acknowledged}
              type="button"
              onClick={() => setSent(true)}
            >
              Send Request <Icon name="arrow" size={16} />
            </button>
          </>
        )}
      </aside>
    </div>
  );
}
export function BuyerDetail({ role, onBack }) {
  const manager = role === "BM";
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [note, setNote] = useState(
    "Strong quantity and delivery match. Please review supplier verification.",
  );
  const [recommended, setRecommended] = useState(false);
  return (
    <main className="page workspace-page buyer-detail-page">
      <button className="back-action" type="button" onClick={onBack}>
        <Icon name="arrow" size={14} /> Back to discovery
      </button>
      <section className="seller-profile">
        <div className="seller-monogram">MA</div>
        <div>
          <p className="eyebrow">Seller organization</p>
          <h1>Mekong Agro Export</h1>
          <p>Vietnam · Business Unverified</p>
        </div>
        <div className="seller-badges">
          <span className="tag verified">
            <Icon name="check" size={13} /> Email Verified
          </span>
          <span className="tag unverified">Business Unverified</span>
        </div>
      </section>

      <div className="detail-layout">
        <section className="public-detail">
          <div className="detail-title">
            <div>
              <span className="section-kicker">LST-VN-0161 · v1</span>
              <h2>Robusta Coffee Grade 1</h2>
            </div>
            <span className="data-tag public">Public</span>
          </div>
          <p>
            All information below is explicitly public and available to buyers
            and Discovery AI.
          </p>
          <div className="public-field-grid">
            <PreviewField label="Product" value="Robusta Coffee Grade 1" />
            <PreviewField label="Quantity" value="20 Tons" />
            <PreviewField label="Minimum order" value="10 Tons" />
            <PreviewField label="Validity date" value="Nov 30, 2026" />
            <PreviewField label="Grade" value="Screen 18" />
            <PreviewField label="Origin" value="Dak Lak, Vietnam" />
            <PreviewField label="Port of loading" value="Cat Lai, HCMC" />
            <PreviewField label="Packaging" value="60 kg jute bags" />
          </div>
          <div className="public-description">
            <span>Public description</span>
            <p>
              Sustainably sourced Robusta coffee from family farms in Dak Lak,
              prepared for export with full lot traceability.
            </p>
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
              <Button kind="secondary" onClick={() => setRecommended(true)}>
                Recommend to Manager <Icon name="arrow" size={16} />
              </Button>
            </>
          )}
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
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </main>
  );
}
export function BuyerRecommendations() {
  const [empty, setEmpty] = useState(false);
  const [handled, setHandled] = useState([]);
  const recommendations = [
    {
      id: "LST-VN-0161",
      product: "Robusta Coffee Grade 1",
      seller: "Mekong Agro Export",
      quantity: "20 Tons",
      staff: "Sokha Lim",
      time: "18 minutes ago",
      note: "Strong quantity and delivery match. Please review supplier verification before connecting.",
    },
    {
      id: "LST-VN-0154",
      product: "Robusta Coffee Screen 18",
      seller: "Dak Lak Cooperative",
      quantity: "35 Tons",
      staff: "Dara Chhim",
      time: "Yesterday, 16:42",
      note: "Alternative supplier with a larger lot. Delivery date needs confirmation.",
    },
  ].filter((item) => !handled.includes(item.id));
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
        <div className="state-switcher">
          <span>Preview</span>
          <button
            className={!empty ? "active" : ""}
            type="button"
            onClick={() => setEmpty(false)}
          >
            Queue
          </button>
          <button
            className={empty ? "active" : ""}
            type="button"
            onClick={() => setEmpty(true)}
          >
            Empty
          </button>
        </div>
      </div>

      {empty || recommendations.length === 0 ? (
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
                <span className="member-avatar">
                  {item.staff
                    .split(" ")
                    .map((word) => word[0])
                    .join("")}
                </span>
                <span>
                  <strong>{item.staff}</strong>
                  <small>{item.time}</small>
                </span>
              </div>
              <div className="recommendation-note">
                <span>Staff note</span>
                <p>“{item.note}”</p>
              </div>
              <div className="recommendation-listing">
                <span>{item.id}</span>
                <strong>{item.product}</strong>
                <small>
                  {item.seller} · {item.quantity}
                </small>
              </div>
              <div className="recommendation-actions">
                <Button onClick={() => setHandled([...handled, item.id])}>
                  Send Connection Request
                </Button>
                <button
                  type="button"
                  onClick={() => setHandled([...handled, item.id])}
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
export const buyerRequests = [
  {
    id: "REQ-0842",
    seller: "Mekong Agro Export",
    listing: "LST-VN-0161 · Robusta Coffee 20 Tons",
    status: "Pending",
    detail: "5d 18h left",
  },
  {
    id: "REQ-0834",
    seller: "Dak Lak Cooperative",
    listing: "LST-VN-0154 · Robusta Coffee 35 Tons",
    status: "Accepted",
    detail: "DR-0402",
  },
  {
    id: "REQ-0819",
    seller: "Highland Origin Co.",
    listing: "LST-VN-0147 · Arabica Coffee 12 Tons",
    status: "Declined",
    detail: "Jun 14",
    reason: "Requested inventory has already been allocated.",
  },
  {
    id: "REQ-0798",
    seller: "Saigon Pepper Co.",
    listing: "LST-VN-0131 · Black Pepper 10 Tons",
    status: "Expired",
    detail: "Expired Jun 10",
  },
  {
    id: "REQ-0761",
    seller: "Delta Rice Export",
    listing: "LST-VN-0108 · White Rice 50 Tons",
    status: "Withdrawn",
    detail: "Withdrawn Jun 6",
  },
];
export function BuyerConnectionInbox({ role, onEnterRoom }) {
  const manager = role === "BM";
  const [filter, setFilter] = useState("All");
  const [withdrawn, setWithdrawn] = useState([]);
  const requests = buyerRequests
    .map((request) =>
      withdrawn.includes(request.id)
        ? { ...request, status: "Withdrawn" }
        : request,
    )
    .filter((request) => filter === "All" || request.status === filter);
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
          <strong>1</strong>
          <span>Pending</span>
        </div>
        <div>
          <strong>1</strong>
          <span>Active Deal Room</span>
        </div>
        <div>
          <strong>5</strong>
          <span>Total requests</span>
        </div>
        <div className="status-filters">
          <FilterSelect
            value={filter}
            options={[
              "All",
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

      <section className="buyer-request-list">
        {requests.map((request) => (
          <article className="buyer-request-item" key={request.id}>
            <div className="request-identity">
              <span className="member-avatar">
                {request.seller.slice(0, 2).toUpperCase()}
              </span>
              <span>
                <strong>{request.seller}</strong>
                <small>{request.id} · Sent by Phnom Penh Imports</small>
              </span>
            </div>
            <div className="buyer-request-listing">
              <span>Public listing</span>
              <strong>{request.listing}</strong>
            </div>
            <div>
              <ConnectionStatusBadge
                status={request.status}
                detail={request.detail}
              />
              {request.reason && (
                <p className="decline-reason">“{request.reason}”</p>
              )}
            </div>
            <div className="buyer-request-actions">
              {request.status === "Accepted" && (
                <Button kind="secondary" onClick={onEnterRoom}>
                  Enter Deal Room DR-0402
                </Button>
              )}
              {manager && request.status === "Pending" && (
                <button
                  type="button"
                  onClick={() => setWithdrawn([...withdrawn, request.id])}
                >
                  Withdraw Request
                </button>
              )}
              {!manager && request.status !== "Accepted" && (
                <span>Read-only status</span>
              )}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

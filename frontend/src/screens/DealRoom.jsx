import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks";
import { fmtField, fmtNumber, fmtTime, fmtValue, initials } from "../format";
import { PreviewField } from "./Seller";
import {
  Icon,
  Button,
  Field,
  SelectField,
  Toggle,
  ApiStatus,
  ErrorNote,
} from "../shared";

export function AddSharedInfoModal({
  room,
  role,
  organization,
  onClose,
  onShared,
}) {
  const sellerManager = role === "Seller Manager";
  const types = room.structured_types;
  const [mode, setMode] = useState(sellerManager ? "snapshot" : "structured");
  const [snapshotFields, setSnapshotFields] = useState([]);
  const [typeKey, setTypeKey] = useState("delivery_schedule");
  const spec = types[typeKey];
  const [value, setValue] = useState("2026-11-28");
  const [unit, setUnit] = useState("");
  const [shared, setShared] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState(null);

  // Seller Manager: private fields of the listing snapshot not yet public
  const privateFields = useApi(async () => {
    if (!sellerManager) return [];
    const listing = await api.listing(room.listing.id);
    if (!listing.snapshot_id) return [];
    const snap = await api.snapshot(listing.snapshot_id);
    return snap.fields.filter((f) => !listing.public_keys.includes(f.key));
  }, [room.listing.id]);

  const pickType = (key) => {
    setTypeKey(key);
    const t = types[key];
    setValue(
      t.type === "enum" ? t.options[0] : t.type === "date" ? "2026-11-28" : "",
    );
    setUnit(t.units[0] ?? "");
  };
  const toggleSnapshot = (key) =>
    setSnapshotFields((fields) =>
      fields.includes(key) ? fields.filter((k) => k !== key) : [...fields, key],
    );

  const share = async () => {
    setSharing(true);
    setError(null);
    try {
      if (mode === "snapshot") {
        if (!snapshotFields.length) return;
        for (const key of snapshotFields) {
          // The modal itself is the extra confirmation for sensitive fields
          await api.share(room.id, {
            mode: "snapshot",
            field_key: key,
            confirm_sensitive: true,
          });
        }
      } else {
        await api.share(room.id, {
          mode: "structured",
          type_key: typeKey,
          value,
          unit: spec.units.length ? unit : null,
        });
      }
      setShared(true);
      onShared();
    } catch (e) {
      setError(e);
    } finally {
      setSharing(false);
    }
  };

  const labelOf = (key) =>
    privateFields.data?.find((f) => f.key === key)?.label ?? key;

  return (
    <div className="shared-modal-layer" role="dialog" aria-modal="true">
      <button
        aria-label="Close shared information modal"
        className="drawer-backdrop"
        type="button"
        onClick={onClose}
      />
      <section className="shared-modal">
        <div className="drawer-head">
          <div>
            <p className="eyebrow">Room {room.id}</p>
            <h2>Add Shared Information</h2>
          </div>
          <button type="button" onClick={onClose}>
            <Icon name="close" size={18} />
          </button>
        </div>

        {shared ? (
          <div className="share-success">
            <span>
              <Icon name="check" size={21} />
            </span>
            <h2>Shared in Room</h2>
            <p>
              Your partner and this room’s AI can now use this information.
              Public listing visibility is unchanged.
            </p>
            <Button kind="secondary" onClick={onClose}>
              Done
            </Button>
          </div>
        ) : (
          <>
            <div className="share-mode-tabs">
              {sellerManager && (
                <button
                  className={mode === "snapshot" ? "active" : ""}
                  type="button"
                  onClick={() => setMode("snapshot")}
                >
                  Share from Private Snapshot
                </button>
              )}
              <button
                className={mode === "structured" ? "active" : ""}
                type="button"
                onClick={() => setMode("structured")}
              >
                Add Structured Item
              </button>
            </div>

            {mode === "snapshot" ? (
              <div className="snapshot-share">
                <div className="modal-intro">
                  <h3>Reveal selected private fields in this room only.</h3>
                  <p>
                    This does not change {room.listing.id} or make these fields
                    public.
                  </p>
                </div>
                {(privateFields.data ?? []).map((f) => (
                  <div className="snapshot-share-row" key={f.key}>
                    <span>
                      <strong>{f.label}</strong>
                      <small>
                        {fmtValue(f.value, f.unit)} ·{" "}
                        {f.blocked
                          ? "Blocked by policy"
                          : "Confidential · Encrypted"}
                      </small>
                    </span>
                    <Toggle
                      checked={snapshotFields.includes(f.key)}
                      label={`Share ${f.label} in room`}
                      onChange={() => toggleSnapshot(f.key)}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="structured-share">
                <SelectField
                  label="Category"
                  value={typeKey}
                  onChange={pickType}
                >
                  {Object.entries(types).map(([key, t]) => (
                    <option key={key} value={key}>
                      {t.label}
                    </option>
                  ))}
                </SelectField>
                {spec.type === "enum" ? (
                  <SelectField label="Value" value={value} onChange={setValue}>
                    {spec.options.map((o) => (
                      <option key={o}>{o}</option>
                    ))}
                  </SelectField>
                ) : (
                  <Field
                    label="Value"
                    type={spec.type === "date" ? "date" : "text"}
                    value={value}
                    onChange={setValue}
                  />
                )}
                {spec.units.length > 0 && (
                  <SelectField
                    label="Unit · Required"
                    value={unit || spec.units[0]}
                    onChange={setUnit}
                  >
                    {spec.units.map((u) => (
                      <option key={u}>{u}</option>
                    ))}
                  </SelectField>
                )}
              </div>
            )}

            <div className="share-preview">
              <span className="preview-icon public">
                <Icon name="spark" size={18} />
              </span>
              <div>
                <span>What your partner and this room’s AI will see</span>
                <strong>
                  {mode === "snapshot"
                    ? snapshotFields.length
                      ? snapshotFields.map(labelOf).join(", ")
                      : "Select at least one private field"
                    : `${spec.label}: ${fmtValue(value, spec.units.length ? unit || spec.units[0] : null)}`}
                </strong>
                <small>Shared in Room · by {organization}</small>
              </div>
            </div>
            <ErrorNote error={error} />
            <Button disabled={sharing} onClick={share}>
              {sharing ? "Sharing…" : "Share in Room"}{" "}
              <Icon name="arrow" size={16} />
            </Button>
          </>
        )}
      </section>
    </div>
  );
}

const ROOM_STATUS = {
  active: "Active",
  finalized: "Deal Closed / Confirmed",
  closed: "Room Closed",
};
const CONTRACT_STATUS = {
  draft: "Draft",
  pending: "Awaiting Buyer Confirmation",
  confirmed: "Confirmed",
  revision_requested: "Revision Requested",
  declined: "Declined",
  cancelled: "Cancelled",
};

export function DealRoom({ role, roomId, onRoomResolved, onNavigate }) {
  // No room selected yet (e.g. top-nav "Deal Room"): open the most recent one
  const rooms = useApi(
    () => (roomId ? Promise.resolve(null) : api.rooms()),
    [roomId],
  );
  useEffect(() => {
    if (!roomId && rooms.data?.length) onRoomResolved(rooms.data[0].id);
  }, [roomId, rooms.data, onRoomResolved]);

  if (!roomId) {
    return (
      <main className="room-page">
        <ApiStatus
          loading={rooms.loading}
          error={rooms.error}
          onRetry={rooms.reload}
        />
        {rooms.data?.length === 0 && (
          <section className="inbox-empty">
            <Icon name="mail" size={22} />
            <h2>No Deal Room yet</h2>
            <p>
              A room is created when the Seller Manager accepts a connection
              request.
            </p>
          </section>
        )}
      </main>
    );
  }
  return (
    <Room key={roomId} role={role} roomId={roomId} onNavigate={onNavigate} />
  );
}

const AI_PROMPTS = {
  seller: [
    ["What is the MOQ?", "What is the MOQ?"],
    ["Summarize delivery schedule", "What is the delivery schedule?"],
    ["Ask for unshared data", "What is the buyer's budget?"],
  ],
  buyer: [
    ["What is the MOQ?", "What is the MOQ?"],
    ["Summarize delivery schedule", "What is the delivery schedule?"],
    ["Ask for unshared data", "What is the seller's floor price?"],
  ],
};

function Room({ role, roomId, onNavigate }) {
  const manager = role.endsWith("Manager");
  const [tab, setTab] = useState("listing");
  const [mobileTab, setMobileTab] = useState("chat");
  const [confirmClose, setConfirmClose] = useState(false);
  const [shareModal, setShareModal] = useState(false);
  const [directMessage, setDirectMessage] = useState("");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState(null);
  const streamRef = useRef(null);

  const room = useApi(() => api.room(roomId), [roomId], 5000);
  const messages = useApi(() => api.messages(roomId), [roomId], 3000);
  const assistant = useApi(() => api.assistantHistory(roomId), [roomId], 5000);

  useEffect(() => {
    const el = streamRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.data?.length]);

  if (!room.data) {
    return (
      <main className="room-page">
        <ApiStatus
          loading={room.loading}
          error={room.error}
          onRetry={room.reload}
        />
      </main>
    );
  }
  const r = room.data;
  const organization = r.my_side === "seller" ? r.seller_org : r.buyer_org;
  const roomStatus = ROOM_STATUS[r.status];
  const pf = r.listing.public_fields;

  const run = async (fn) => {
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e);
    }
  };
  const addMessage = (event) => {
    event.preventDefault();
    if (!directMessage.trim()) return;
    run(async () => {
      await api.sendMessage(roomId, directMessage);
      setDirectMessage("");
      messages.reload(true);
    });
  };
  const ask = (text) => {
    if (!text.trim()) return;
    setAsking(true);
    run(async () => {
      await api.ask(roomId, text);
      setQuestion("");
      await assistant.reload(true);
    }).finally(() => setAsking(false));
  };
  const turns = assistant.data ?? [];

  return (
    <main className="room-page">
      <header className="room-header">
        <div>
          <p className="eyebrow">Private Deal Room</p>
          <h1>{r.id}</h1>
        </div>
        <div className="room-link">
          <span>Linked listing</span>
          <strong>
            {r.listing.id} {r.listing.version_label}
          </strong>
        </div>
        <span
          className={`room-status ${roomStatus
            .toLowerCase()
            .replaceAll(" ", "-")
            .replace("/", "")}`}
        >
          {roomStatus}
        </span>
        {r.permissions.close && (
          <button
            className="close-room-action"
            type="button"
            onClick={() => setConfirmClose(true)}
          >
            Close Room
          </button>
        )}
      </header>

      {confirmClose && (
        <div className="room-close-confirm">
          <Icon name="shield" size={18} />
          <span>
            <strong>Close Deal Room {r.id}?</strong>
            Messaging and new sharing will stop. A pending contract is
            cancelled. Existing records remain versioned.
          </span>
          <button type="button" onClick={() => setConfirmClose(false)}>
            Cancel
          </button>
          <Button
            onClick={() =>
              run(async () => {
                await api.closeRoom(roomId);
                setConfirmClose(false);
                room.reload(true);
                messages.reload(true);
              })
            }
          >
            Confirm Close
          </Button>
        </div>
      )}

      {r.listing_changed && (
        <div className="room-update-banner">
          <span>
            <Icon name="file" size={17} />
          </span>
          <div>
            <strong>
              Underlying listing updated to {r.listing.version_label}
            </strong>
            <small>
              The assistant now answers from the current version. Review the
              listing tab for the latest public fields.
            </small>
          </div>
          <button
            type="button"
            onClick={() =>
              run(async () => {
                setTab("listing");
                await api.ackListingVersion(roomId);
                room.reload(true);
              })
            }
          >
            Mark as reviewed
          </button>
        </div>
      )}
      <ErrorNote error={error} />

      <div className="mobile-room-tabs">
        {[
          ["chat", "Direct Chat"],
          ["ai", "Private AI"],
          ["info", "Room Info"],
        ].map(([value, label]) => (
          <button
            className={mobileTab === value ? "active" : ""}
            key={value}
            type="button"
            onClick={() => setMobileTab(value)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="room-layout">
        <section
          className={`room-info-panel ${mobileTab === "info" ? "mobile-active" : ""}`}
        >
          <div className="room-tabs">
            {[
              ["listing", "Listing"],
              ["shared", "Shared Info"],
              ["contract", "Contract"],
              ["members", "Members"],
            ].map(([value, label]) => (
              <button
                className={tab === value ? "active" : ""}
                key={value}
                type="button"
                onClick={() => setTab(value)}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="room-panel-content">
            {tab === "listing" && (
              <div className="room-listing">
                <div className="room-panel-heading">
                  <div>
                    <p className="eyebrow">
                      Public listing · {r.listing.version_label}
                    </p>
                    <h2>{pf.product?.value}</h2>
                  </div>
                  <span className="data-tag public">Public</span>
                </div>
                <div className="room-fields">
                  {Object.entries(pf)
                    .filter(([key]) => key !== "product")
                    .map(([key, f]) => (
                      <PreviewField
                        key={key}
                        label={f.label}
                        value={fmtField(f)}
                      />
                    ))}
                </div>
              </div>
            )}

            {tab === "shared" && (
              <div className="room-shared">
                <div className="room-panel-heading">
                  <div>
                    <p className="eyebrow">Room-only data</p>
                    <h2>Shared information</h2>
                  </div>
                  {r.permissions.share && (
                    <Button onClick={() => setShareModal(true)}>
                      <Icon name="plus" size={14} /> Add Shared Info
                    </Button>
                  )}
                </div>
                <p className="panel-helper">
                  Available to both partners and this room’s grounded AI.
                </p>
                <div className="shared-item-list">
                  {r.shared_items.length === 0 && (
                    <p className="panel-helper">Nothing shared yet.</p>
                  )}
                  {r.shared_items.map((item) => (
                    <article
                      className="shared-item"
                      key={item.id}
                      style={item.revoked_at ? { opacity: 0.55 } : undefined}
                    >
                      <span className="shared-item-icon">
                        <Icon name="file" size={16} />
                      </span>
                      <div>
                        <span>{item.label}</span>
                        <strong>{fmtValue(item.value, item.unit)}</strong>
                        <small>{item.badge}</small>
                      </div>
                      {manager &&
                        item.side === r.my_side &&
                        !item.revoked_at &&
                        r.status === "active" && (
                          <button
                            title="Revoking stops the AI from using this data going forward"
                            type="button"
                            onClick={() =>
                              run(async () => {
                                await api.revoke(roomId, item.id);
                                room.reload(true);
                              })
                            }
                          >
                            Revoke
                          </button>
                        )}
                    </article>
                  ))}
                </div>
              </div>
            )}

            {tab === "contract" && (
              <div className="room-contract">
                <p className="eyebrow">Contract · Versioned</p>
                {r.contract ? (
                  <>
                    <h2>
                      Contract v{r.contract.version} ·{" "}
                      {CONTRACT_STATUS[r.contract.status]}
                    </h2>
                    <p>
                      Total {fmtNumber(r.contract.total)} {r.contract.currency} ·
                      calculated by the system.
                    </p>
                    <Button onClick={() => onNavigate("contract-review")}>
                      View Contract · R4 <Icon name="arrow" size={15} />
                    </Button>
                    {r.permissions.create_contract &&
                      ["revision_requested", "declined"].includes(
                        r.contract.status,
                      ) && (
                        <button
                          className="contract-link"
                          type="button"
                          onClick={() => onNavigate("contract-edit")}
                        >
                          Create v{r.contract.version + 1} · R3
                        </button>
                      )}
                  </>
                ) : (
                  <>
                    <h2>No contract created yet.</h2>
                    <p>
                      The Seller Manager creates a versioned contract from the
                      listing and room-shared information. The Buyer Manager
                      confirms it.
                    </p>
                    {r.permissions.create_contract && (
                      <Button onClick={() => onNavigate("contract-edit")}>
                        Create Contract · R3 <Icon name="arrow" size={15} />
                      </Button>
                    )}
                  </>
                )}
              </div>
            )}

            {tab === "members" && (
              <div className="room-members">
                <p className="eyebrow">{r.members.length} room members</p>
                <h2>Participating organizations</h2>
                {r.members.map((m) => (
                  <div className="room-member" key={`${m.name}-${m.org}`}>
                    <span className="member-avatar">{initials(m.name)}</span>
                    <span>
                      <strong>{m.name}</strong>
                      <small>{m.org}</small>
                    </span>
                    <span className={`role-badge ${m.side}`}>
                      {m.role_label}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section
          className={`partner-chat ${mobileTab === "chat" ? "mobile-active" : ""}`}
        >
          <div className="chat-panel-head">
            <div>
              <p className="eyebrow">Partner channel</p>
              <h2>Direct Chat</h2>
            </div>
            <span className="chat-members">{r.members.length} members</span>
          </div>
          <div className="direct-chat-notice">
            <Icon name="lock" size={13} />
            Direct messages are never read by the AI Assistant.
          </div>
          <div className="message-stream" ref={streamRef}>
            {(messages.data ?? []).map((message) =>
              message.system ? (
                <div className="direct-chat-notice" key={message.id}>
                  <Icon name="shield" size={13} />
                  {message.text}
                </div>
              ) : (
                <div
                  className={`partner-message ${message.sender_org === organization ? "own" : ""}`}
                  key={message.id}
                >
                  <div>
                    <strong>{message.sender_name}</strong>
                    <span>{fmtTime(message.created_at)}</span>
                  </div>
                  <div className="message-identity">
                    <small>{message.sender_org}</small>
                    <span className={`role-badge ${message.side}`}>
                      {message.sender_role}
                    </span>
                  </div>
                  <p>{message.text}</p>
                </div>
              ),
            )}
          </div>
          <form className="partner-composer" onSubmit={addMessage}>
            <input
              aria-label="Message your partner"
              disabled={!r.permissions.chat}
              placeholder={
                r.permissions.chat
                  ? "Message your partner organization…"
                  : `Room is ${roomStatus.toLowerCase()} · messaging stopped`
              }
              value={directMessage}
              onChange={(event) => setDirectMessage(event.target.value)}
            />
            <button
              type="submit"
              aria-label="Send direct message"
              disabled={!r.permissions.chat}
            >
              <Icon name="arrow" size={16} />
            </button>
          </form>
        </section>

        <aside
          className={`private-ai-panel ${mobileTab === "ai" ? "mobile-active" : ""}`}
        >
          <div className="private-ai-head">
            <span>
              <Icon name="spark" size={19} />
            </span>
            <div>
              <h2>Private AI Assistant</h2>
              <p>Visible only to {organization}</p>
            </div>
          </div>
          <div className="private-ai-grounding">
            <Icon name="shield" size={13} />
            Strictly grounded in listing, room-shared data and contract summary
          </div>
          <div className="private-ai-thread">
            {turns.length === 0 && (
              <p className="panel-helper">
                Ask about this room. Answers always cite their source.
              </p>
            )}
            {turns.map((t, i) => (
              <div key={`${t.created_at}-${i}`}>
                <div className="ai-user-message">{t.question}</div>
                <div className="ai-grounded-answer">
                  <span className="ai-avatar">
                    <Icon name="spark" size={16} />
                  </span>
                  <p style={{ whiteSpace: "pre-line" }}>{t.answer}</p>
                  <span className="citation-pill">
                    {t.sources.length
                      ? `Source: ${t.sources
                          .map((s) =>
                            s.type === "listing"
                              ? `Listing ${s.id} v${s.version} · ${s.field}`
                              : s.type === "shared_item"
                                ? `Shared in Room · ${s.label}`
                                : `Contract v${s.version}`,
                          )
                          .join(" · ")}`
                      : "Source: Room access policy · Not available in room"}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div className="ai-room-prompts">
            <span>Ask from room data</span>
            {AI_PROMPTS[r.my_side].map(([label, q]) => (
              <button
                key={label}
                type="button"
                disabled={asking}
                onClick={() => ask(q)}
              >
                {label}
              </button>
            ))}
          </div>
          <form
            className="private-ai-input"
            onSubmit={(e) => {
              e.preventDefault();
              ask(question);
            }}
          >
            <input
              aria-label="Ask private AI assistant"
              placeholder={asking ? "Thinking…" : "Ask about room data…"}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button type="submit" aria-label="Ask AI" disabled={asking}>
              <Icon name="arrow" size={15} />
            </button>
          </form>
        </aside>
      </div>

      {shareModal && r.permissions.share && (
        <AddSharedInfoModal
          room={r}
          role={role}
          organization={organization}
          onClose={() => setShareModal(false)}
          onShared={() => room.reload(true)}
        />
      )}
    </main>
  );
}

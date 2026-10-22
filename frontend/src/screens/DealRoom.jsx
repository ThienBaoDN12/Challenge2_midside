import { useState } from "react";
import { PreviewField } from "./Seller";
import { Icon, Button, Field, SelectField, Toggle } from "../shared";
export function AddSharedInfoModal({ role, organization, onClose }) {
  const sellerManager = role === "Seller Manager";
  const [mode, setMode] = useState(sellerManager ? "snapshot" : "structured");
  const [snapshotFields, setSnapshotFields] = useState([]);
  const [category, setCategory] = useState("Delivery Schedule");
  const [value, setValue] = useState("Delivery to Phnom Penh by Nov 28, 2026");
  const [unit, setUnit] = useState("Date");
  const [shared, setShared] = useState(false);
  const toggleSnapshot = (field) => {
    setSnapshotFields((fields) =>
      fields.includes(field)
        ? fields.filter((item) => item !== field)
        : [...fields, field],
    );
  };
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
            <p className="eyebrow">Room DR-0402</p>
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
                    This does not change LST-VN-0161 or make these fields
                    public.
                  </p>
                </div>
                {[
                  ["Floor Price", "$3,850 / ton"],
                  ["Cost Price", "$3,600 / ton"],
                  ["Supplier Households", "124 households"],
                ].map(([field, fieldValue]) => (
                  <div className="snapshot-share-row" key={field}>
                    <span>
                      <strong>{field}</strong>
                      <small>{fieldValue} · Confidential · Encrypted</small>
                    </span>
                    <Toggle
                      checked={snapshotFields.includes(field)}
                      label={`Share ${field} in room`}
                      onChange={() => toggleSnapshot(field)}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="structured-share">
                <SelectField
                  label="Category"
                  value={category}
                  onChange={setCategory}
                >
                  <option>Proposed Price</option>
                  <option>Delivery Schedule</option>
                  <option>Payment Terms</option>
                  <option>Certification</option>
                </SelectField>
                <Field label="Value" value={value} onChange={setValue} />
                <SelectField
                  label="Unit · Required"
                  value={unit}
                  onChange={setUnit}
                >
                  <option>Date</option>
                  <option>USD / ton</option>
                  <option>Days</option>
                  <option>Document</option>
                </SelectField>
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
                      ? snapshotFields.join(", ")
                      : "Select at least one private field"
                    : `${category}: ${value} · ${unit}`}
                </strong>
                <small>Shared in Room · by {organization}</small>
              </div>
            </div>
            <Button
              onClick={() => {
                if (mode === "structured" || snapshotFields.length) {
                  setShared(true);
                }
              }}
            >
              Share in Room <Icon name="arrow" size={16} />
            </Button>
          </>
        )}
      </section>
    </div>
  );
}
export function DealRoom({ role, dealConfirmed, onNavigate }) {
  const manager = role.endsWith("Manager");
  const sellerSide = role.startsWith("Seller");
  const organization = sellerSide ? "Mekong Agro" : "Phnom Penh Imports";
  const [tab, setTab] = useState("listing");
  const [mobileTab, setMobileTab] = useState("chat");
  const [roomStatus, setRoomStatus] = useState(
    dealConfirmed ? "Deal Closed / Confirmed" : "Active",
  );
  const [showUpdate, setShowUpdate] = useState(true);
  const [confirmClose, setConfirmClose] = useState(false);
  const [shareModal, setShareModal] = useState(false);
  const [revoked, setRevoked] = useState([]);
  const [directMessage, setDirectMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      name: "Sokha Lim",
      org: "Phnom Penh Imports",
      role: "Buyer Staff",
      text: "Could you confirm whether the 20-ton lot can reach Phnom Penh before November 30?",
      time: "10:42",
    },
    {
      name: "Nguyen Lan",
      org: "Mekong Agro",
      role: "Seller Manager",
      text: "Yes. We can support that schedule from Cat Lai. I’ll share the proposed delivery schedule in this room.",
      time: "10:48",
    },
    {
      name: "Dara Chhim",
      org: "Phnom Penh Imports",
      role: "Buyer Manager",
      text: "Thank you. We will review the schedule and prepare proposed payment terms.",
      time: "10:51",
    },
  ]);
  const [aiTopic, setAiTopic] = useState("moq");
  const addMessage = (event) => {
    event.preventDefault();
    if (!directMessage.trim()) return;
    setMessages([
      ...messages,
      {
        name: sellerSide ? "Nguyen Lan" : "Dara Chhim",
        org: organization,
        role: role,
        text: directMessage,
        time: "Now",
      },
    ]);
    setDirectMessage("");
  };
  const aiAnswers = {
    moq: {
      question: "What is the minimum order quantity?",
      answer:
        "The minimum order quantity for this listing is 10 Tons. The available quantity is 20 Tons.",
      source: "Source: Listing LST-VN-0161 v1 · MOQ",
    },
    schedule: {
      question: "What delivery schedule was proposed?",
      answer:
        "The seller proposed delivery to Phnom Penh by November 28, 2026, subject to final contract confirmation.",
      source: "Source: Shared in Room · Delivery Schedule",
    },
    missing: {
      question: sellerSide
        ? "What are the buyer’s unshared payment terms?"
        : "What is the seller’s floor price?",
      answer:
        "I do not have this information in the room yet. You may ask your partner in the direct chat.",
      source: "Source: Room access policy · Unshared information",
    },
  };
  const aiAnswer = aiAnswers[aiTopic];
  const sharedItems = [
    {
      id: "schedule",
      category: "Delivery Schedule",
      value: "Delivery to Phnom Penh by Nov 28, 2026",
      unit: "Date",
      org: "Mekong Agro",
      own: sellerSide,
    },
    {
      id: "terms",
      category: "Payment Terms",
      value: "30% deposit · 70% against shipping documents",
      unit: "Percent",
      org: "Phnom Penh Imports",
      own: !sellerSide,
    },
  ].filter((item) => !revoked.includes(item.id));
  return (
    <main className="room-page">
      <header className="room-header">
        <div>
          <p className="eyebrow">Private Deal Room</p>
          <h1>DR-0402</h1>
        </div>
        <div className="room-link">
          <span>Linked listing</span>
          <strong>LST-VN-0161 v1</strong>
        </div>
        <span
          className={`room-status ${roomStatus
            .toLowerCase()
            .replaceAll(" ", "-")
            .replace("/", "")}`}
        >
          {roomStatus}
        </span>
        <label className="update-toggle">
          <span>v2 update banner</span>
          <Toggle
            checked={showUpdate}
            label="Toggle listing update banner"
            onChange={() => setShowUpdate(!showUpdate)}
          />
        </label>
        {manager && roomStatus !== "Room Closed" && (
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
            <strong>Close Deal Room DR-0402?</strong>
            Messaging and new sharing will stop. Existing records remain
            versioned.
          </span>
          <button type="button" onClick={() => setConfirmClose(false)}>
            Cancel
          </button>
          <Button
            onClick={() => {
              setRoomStatus("Room Closed");
              setConfirmClose(false);
            }}
          >
            Confirm Close
          </Button>
        </div>
      )}

      {showUpdate && (
        <div className="room-update-banner">
          <span>
            <Icon name="file" size={17} />
          </span>
          <div>
            <strong>Underlying listing updated to v2</strong>
            <small>
              This room remains linked to requested snapshot v1. Review the
              field diff before using newer data.
            </small>
          </div>
          <button type="button" onClick={() => setTab("listing")}>
            View version history
          </button>
        </div>
      )}

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
                    <p className="eyebrow">Public snapshot · v1</p>
                    <h2>Robusta Coffee Grade 1</h2>
                  </div>
                  <span className="data-tag public">Public</span>
                </div>
                <div className="room-fields">
                  <PreviewField label="Quantity" value="20 Tons" />
                  <PreviewField label="MOQ" value="10 Tons" />
                  <PreviewField label="Validity" value="Nov 30, 2026" />
                  <PreviewField label="Grade" value="Screen 18" />
                  <PreviewField label="Origin" value="Dak Lak, Vietnam" />
                  <PreviewField label="Port" value="Cat Lai, HCMC" />
                </div>
                <div className="version-history">
                  <span>Version history</span>
                  <div>
                    <strong>v1 · Room snapshot</strong>
                    <small>Preserved Jun 18, 2026</small>
                  </div>
                  <div>
                    <strong>v2 · Current listing</strong>
                    <small>Validity and loading port updated</small>
                  </div>
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
                  {manager && (
                    <Button onClick={() => setShareModal(true)}>
                      <Icon name="plus" size={14} /> Add Shared Info
                    </Button>
                  )}
                </div>
                <p className="panel-helper">
                  Available to both partners and this room’s grounded AI.
                </p>
                <div className="shared-item-list">
                  {sharedItems.map((item) => (
                    <article className="shared-item" key={item.id}>
                      <span className="shared-item-icon">
                        <Icon name="file" size={16} />
                      </span>
                      <div>
                        <span>{item.category}</span>
                        <strong>{item.value}</strong>
                        <small>
                          Shared in Room · by {item.org} · {item.unit}
                        </small>
                      </div>
                      {manager && item.own && (
                        <button
                          title="Revoking stops the AI from using this data going forward"
                          type="button"
                          onClick={() => setRevoked([...revoked, item.id])}
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
                <h2>No contract created yet.</h2>
                <p>
                  Create a versioned draft from agreed room information. Both
                  organization managers must confirm the final version.
                </p>
                {role === "Seller Manager" ? (
                  <Button onClick={() => onNavigate("contract-edit")}>
                    Create Contract · R3 <Icon name="arrow" size={15} />
                  </Button>
                ) : (
                  <Button
                    kind={manager ? "primary" : "secondary"}
                    onClick={() => onNavigate("contract-review")}
                  >
                    View Contract · R4 <Icon name="arrow" size={15} />
                  </Button>
                )}
                <button
                  className="contract-link"
                  type="button"
                  onClick={() => onNavigate("contract-review")}
                >
                  View confirmed contract · R4
                </button>
              </div>
            )}

            {tab === "members" && (
              <div className="room-members">
                <p className="eyebrow">4 room members</p>
                <h2>Participating organizations</h2>
                {[
                  ["Nguyen Lan", "Mekong Agro", "Seller Manager"],
                  ["Tran Minh", "Mekong Agro", "Seller Staff"],
                  ["Dara Chhim", "Phnom Penh Imports", "Buyer Manager"],
                  ["Sokha Lim", "Phnom Penh Imports", "Buyer Staff"],
                ].map(([name, org, memberRole]) => (
                  <div className="room-member" key={name}>
                    <span className="member-avatar">
                      {name
                        .split(" ")
                        .map((word) => word[0])
                        .join("")}
                    </span>
                    <span>
                      <strong>{name}</strong>
                      <small>{org}</small>
                    </span>
                    <span
                      className={`role-badge ${memberRole.startsWith("Seller") ? "seller" : "buyer"}`}
                    >
                      {memberRole}
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
            <span className="chat-members">4 members</span>
          </div>
          <div className="direct-chat-notice">
            <Icon name="lock" size={13} />
            Direct messages are never read by the AI Assistant.
          </div>
          <div className="message-stream">
            {messages.map((message, index) => {
              const own = message.org === organization;
              return (
                <div
                  className={`partner-message ${own ? "own" : ""}`}
                  key={`${message.time}-${index}`}
                >
                  <div>
                    <strong>{message.name}</strong>
                    <span>{message.time}</span>
                  </div>
                  <div className="message-identity">
                    <small>{message.org}</small>
                    <span
                      className={`role-badge ${message.role.startsWith("Seller") ? "seller" : "buyer"}`}
                    >
                      {message.role}
                    </span>
                  </div>
                  <p>{message.text}</p>
                </div>
              );
            })}
          </div>
          <form className="partner-composer" onSubmit={addMessage}>
            <input
              aria-label="Message your partner"
              placeholder="Message your partner organization…"
              value={directMessage}
              onChange={(event) => setDirectMessage(event.target.value)}
            />
            <button type="submit" aria-label="Send direct message">
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
            Strictly grounded in listing and room-shared data
          </div>
          <div className="private-ai-thread">
            <div className="ai-user-message">{aiAnswer.question}</div>
            <div className="ai-grounded-answer">
              <span className="ai-avatar">
                <Icon name="spark" size={16} />
              </span>
              <p>{aiAnswer.answer}</p>
              <span className="citation-pill">{aiAnswer.source}</span>
            </div>
          </div>
          <div className="ai-room-prompts">
            <span>Ask from room data</span>
            <button type="button" onClick={() => setAiTopic("moq")}>
              What is the MOQ?
            </button>
            <button type="button" onClick={() => setAiTopic("schedule")}>
              Summarize delivery schedule
            </button>
            <button type="button" onClick={() => setAiTopic("missing")}>
              Ask for unshared data
            </button>
          </div>
          <div className="private-ai-input">
            <input
              aria-label="Ask private AI assistant"
              placeholder="Ask about room data…"
            />
            <button type="button" aria-label="Ask AI">
              <Icon name="arrow" size={15} />
            </button>
          </div>
        </aside>
      </div>

      {shareModal && manager && (
        <AddSharedInfoModal
          role={role}
          organization={organization}
          onClose={() => setShareModal(false)}
        />
      )}
    </main>
  );
}

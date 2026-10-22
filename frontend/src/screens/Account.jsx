import { useState } from "react";
import { team, Icon, Button, Field, SelectField } from "../shared";
export function Invitation() {
  const [expired, setExpired] = useState(false);
  const [accepted, setAccepted] = useState(false);
  return (
    <main className="page invitation-page">
      <div className="state-switcher" aria-label="Invitation state preview">
        <span>Preview state</span>
        <button
          className={!expired ? "active" : ""}
          type="button"
          onClick={() => setExpired(false)}
        >
          Active
        </button>
        <button
          className={expired ? "active" : ""}
          type="button"
          onClick={() => setExpired(true)}
        >
          Expired
        </button>
      </div>

      <section className={`invitation-card ${expired ? "is-expired" : ""}`}>
        <div className="invitation-symbol">
          <Icon name={expired ? "clock" : "mail"} size={26} />
        </div>
        <p className="eyebrow">
          {expired ? "Invitation expired" : "Private invitation"}
        </p>
        <h1>
          {expired ? (
            "This invitation has expired."
          ) : (
            <>
              You are invited to join <span>Mekong Agro</span> as{" "}
              <span>Seller Staff</span>.
            </>
          )}
        </h1>
        <p className="invitation-copy">
          {expired
            ? "For your security, invitations are only valid for 7 days. Ask your organization manager to send a new one."
            : "Collaborate with your team and help prepare trusted product information for buyers."}
        </p>
        {!expired && !accepted && (
          <Button onClick={() => setAccepted(true)}>
            Accept Invitation <Icon name="arrow" size={17} />
          </Button>
        )}
        {!expired && accepted && (
          <div className="accepted-state">
            <Icon name="check" size={18} />
            Invitation accepted
          </div>
        )}
        {expired && (
          <div className="expired-state">
            <Icon name="clock" size={17} />
            Invitation Expired
          </div>
        )}
        <div className="invitation-meta">
          <div>
            <span>Invited email</span>
            <strong>linh.nguyen@example.com</strong>
          </div>
          <div>
            <span>Organization</span>
            <strong>Mekong Agro · Vietnam</strong>
          </div>
        </div>
      </section>
      <p className="invitation-footer">
        <Icon name="lock" size={13} />
        Identity protected by TideCloak
      </p>
    </main>
  );
}
export function Members() {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Staff");
  const [sent, setSent] = useState(false);
  const sendInvite = (event) => {
    event.preventDefault();
    if (!email) return;
    setSent(true);
    setEmail("");
  };
  return (
    <main className="page members-page">
      <div className="members-heading">
        <div>
          <p className="eyebrow">Organization access</p>
          <h1>Team members</h1>
          <p>
            Manage who can prepare, review, and share your organization’s trade
            information.
          </p>
        </div>
        <div className="member-count">
          <span>4</span>
          <small>members</small>
        </div>
      </div>

      <section className="invite-panel">
        <div className="invite-prompt">
          <span className="prompt-icon">
            <Icon name="team" size={21} />
          </span>
          <div>
            <h2>Invite staff to your organization</h2>
            <p>They’ll receive a secure link to join your workspace.</p>
          </div>
        </div>
        <form className="invite-form" onSubmit={sendInvite}>
          <Field
            label="Work email"
            type="email"
            value={email}
            placeholder="name@company.com"
            onChange={(value) => {
              setEmail(value);
              setSent(false);
            }}
          />
          <SelectField label="Role" value={role} onChange={setRole}>
            <option>Staff</option>
            <option>Manager</option>
          </SelectField>
          <Button type="submit">
            <Icon name="plus" size={16} /> Send Invite
          </Button>
        </form>
        {sent && <span className="invite-sent">Invitation sent</span>}
      </section>

      <section className="team-section">
        <div className="table-heading">
          <h2>Organization members</h2>
          <span>2 active · 2 invited</span>
        </div>
        <div
          className="team-table"
          role="table"
          aria-label="Organization members"
        >
          <div className="table-row table-header" role="row">
            <span role="columnheader">Member</span>
            <span role="columnheader">Role</span>
            <span role="columnheader">Status</span>
            <span role="columnheader">Access</span>
            <span role="columnheader" aria-label="Actions" />
          </div>
          {team.map((member) => (
            <div className="table-row" role="row" key={member.email}>
              <div className="member-cell" role="cell">
                <span className="member-avatar">{member.initials}</span>
                <span>
                  <strong>{member.name}</strong>
                  <small>{member.email}</small>
                </span>
              </div>
              <span className="role-cell" role="cell">
                {member.role}
              </span>
              <span role="cell">
                <span
                  className={`member-status ${member.status.toLowerCase().replace(" ", "-")}`}
                >
                  <span />
                  {member.status}
                </span>
              </span>
              <span className="access-cell" role="cell">
                {member.role === "Manager"
                  ? "Full organization"
                  : "Assigned rooms"}
              </span>
              <span className="row-action" role="cell">
                {member.status === "Pending Acceptance" ? (
                  <button type="button">Resend</button>
                ) : member.status === "Expired" ? (
                  <button type="button">Renew</button>
                ) : member.role === "Manager" ? (
                  <span className="you-label">You</span>
                ) : (
                  <button
                    type="button"
                    aria-label={`Open actions for ${member.name}`}
                  >
                    ···
                  </button>
                )}
              </span>
            </div>
          ))}
        </div>
        <div className="table-note">
          <Icon name="shield" size={16} />
          <span>
            <strong>Manager safeguard</strong>
            The last remaining Manager cannot be removed.
          </span>
        </div>
      </section>
    </main>
  );
}

import { useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks";
import { initials } from "../format";
import {
  Icon,
  Button,
  Field,
  SelectField,
  ApiStatus,
  ErrorNote,
} from "../shared";
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
const INVITE_STATUS = {
  pending: "Pending Acceptance",
  expired: "Expired",
  revoked: "Revoked",
};

export function Members({ me }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Staff");
  const [sent, setSent] = useState(null);
  const [error, setError] = useState(null);
  const {
    data,
    error: loadError,
    loading,
    reload,
  } = useApi(() => api.members());

  const run = async (fn) => {
    setError(null);
    try {
      await fn();
      await reload(true);
    } catch (e) {
      setError(e);
    }
  };
  const sendInvite = (event) => {
    event.preventDefault();
    if (!email) return;
    run(async () => {
      const inv = await api.invite(email, role.toLowerCase());
      setSent(inv);
      setEmail("");
    });
  };

  const rows = [
    ...(data?.members ?? []).map((m) => ({
      key: m.user_id,
      userId: m.user_id,
      name: m.name,
      email: m.email,
      role: m.role === "manager" ? "Manager" : "Staff",
      status: "Active",
    })),
    ...(data?.invites ?? [])
      .filter((i) => i.status !== "revoked")
      .map((i) => ({
        key: i.id,
        name: i.email.split("@")[0],
        email: i.email,
        role: i.role === "manager" ? "Manager" : "Staff",
        status: INVITE_STATUS[i.status],
        invite: i,
      })),
  ];
  const active = data?.members.length ?? 0;
  const invited = rows.length - active;

  return (
    <main className="page members-page">
      <div className="members-heading">
        <div>
          <p className="eyebrow">
            Organization access · {me.organization.name}
          </p>
          <h1>Team members</h1>
          <p>
            Manage who can prepare, review, and share your organization’s trade
            information.
          </p>
        </div>
        <div className="member-count">
          <span>{active}</span>
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
            <p>
              They’ll receive a secure link to join your workspace (valid 7
              days).
            </p>
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
              setSent(null);
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
        {sent && (
          <span className="invite-sent">Invitation sent to {sent.email}</span>
        )}
      </section>
      <ErrorNote error={error} />

      <section className="team-section">
        <div className="table-heading">
          <h2>Organization members</h2>
          <span>
            {active} active · {invited} invited
          </span>
        </div>
        <ApiStatus
          loading={loading && !data}
          error={loadError}
          onRetry={reload}
        />
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
          {rows.map((member) => (
            <div className="table-row" role="row" key={member.key}>
              <div className="member-cell" role="cell">
                <span className="member-avatar">{initials(member.name)}</span>
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
                  : "Public data & rooms"}
              </span>
              <span className="row-action" role="cell">
                {member.invite ? (
                  <button
                    type="button"
                    onClick={() =>
                      run(() => api.invite(member.email, member.invite.role))
                    }
                  >
                    {member.status === "Expired" ? "Renew" : "Resend"}
                  </button>
                ) : member.userId === me.user.id ? (
                  <span className="you-label">You</span>
                ) : (
                  <button
                    type="button"
                    aria-label={`Remove ${member.name}`}
                    onClick={() => run(() => api.removeMember(member.userId))}
                  >
                    Remove
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

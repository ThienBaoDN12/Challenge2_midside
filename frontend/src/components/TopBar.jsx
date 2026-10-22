import { Logo } from "../shared";
import { initials } from "../format";
export function TopBar({ active, me, onNavigate, onSignOut }) {
  // Organization and role always come from the signed-in session (server-side)
  const authenticatedRole = me?.role_label ?? null;
  const contextualOrg = me?.organization?.name ?? "";
  const displaySide = me?.organization?.side ?? "seller";
  return (
    <header className="topbar">
      <Logo />
      <div className="account">
        {authenticatedRole && (
          <div className="account-nav">
            {authenticatedRole.startsWith("Seller") && (
              <button
                className={active === "seller-workspace" ? "active" : ""}
                type="button"
                onClick={() => onNavigate("seller-workspace")}
              >
                Listings
              </button>
            )}
            {authenticatedRole.startsWith("Seller") && (
              <button
                className={active === "seller-inbox" ? "active" : ""}
                type="button"
                onClick={() => onNavigate("seller-inbox")}
              >
                Inbox
              </button>
            )}
            {authenticatedRole === "Seller Manager" && (
              <button
                className={active === "members" ? "active" : ""}
                type="button"
                onClick={() => onNavigate("members")}
              >
                Team
              </button>
            )}
            {authenticatedRole === "Buyer Manager" && (
              <button
                className={active === "members" ? "active" : ""}
                type="button"
                onClick={() => onNavigate("members")}
              >
                Team
              </button>
            )}
            {authenticatedRole.startsWith("Buyer") && (
              <button
                className={
                  active === "buyer-workspace" || active === "buyer-detail"
                    ? "active"
                    : ""
                }
                type="button"
                onClick={() => onNavigate("buyer-workspace")}
              >
                Discovery
              </button>
            )}
            {authenticatedRole.startsWith("Buyer") && (
              <button
                className={active === "buyer-inbox" ? "active" : ""}
                type="button"
                onClick={() => onNavigate("buyer-inbox")}
              >
                Inbox
              </button>
            )}
            {authenticatedRole === "Buyer Manager" && (
              <button
                className={active === "buyer-recommendations" ? "active" : ""}
                type="button"
                onClick={() => onNavigate("buyer-recommendations")}
              >
                Recommendations
              </button>
            )}
            <button
              className={
                active === "deal-room" ||
                active === "contract-edit" ||
                active === "contract-review"
                  ? "active"
                  : ""
              }
              type="button"
              onClick={() => onNavigate("deal-room")}
            >
              Deal Room
            </button>
          </div>
        )}
        {authenticatedRole && (
          <>
            <span className="account-org">{contextualOrg}</span>
            <span aria-hidden="true" className="account-divider" />
            <span className={`role-badge ${displaySide}`}>
              {authenticatedRole}
            </span>
            <span className="avatar" title={me.user.name}>
              {initials(me.user.name)}
            </span>
          </>
        )}
        {authenticatedRole && (
          <button className="switch-account" type="button" onClick={onSignOut}>
            Sign out
          </button>
        )}
      </div>
    </header>
  );
}

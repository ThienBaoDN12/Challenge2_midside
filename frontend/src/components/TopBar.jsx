import { screenMeta, Logo } from "../shared";
export function TopBar({
  active,
  roleOverride,
  authenticatedRole,
  onNavigate,
  onSignOut,
}) {
  const meta = screenMeta[active];
  const roomContext =
    active === "deal-room" ||
    active === "contract-edit" ||
    active === "contract-review";
  const roomForBuyer = roomContext && authenticatedRole?.startsWith("Buyer");
  const roomForSeller = roomContext && authenticatedRole?.startsWith("Seller");
  const displayOrg = roomForBuyer ? "Phnom Penh Imports" : meta.org;
  const contextualOrg = roomForSeller ? "Mekong Agro" : displayOrg;
  const displaySide = roomForBuyer
    ? "buyer"
    : roomForSeller
      ? "seller"
      : meta.side;
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
        <span className="account-org">{contextualOrg}</span>
        <span aria-hidden="true" className="account-divider" />
        <span className={`role-badge ${displaySide}`}>
          {roleOverride ?? meta.role}
        </span>
        <span className="avatar">
          {contextualOrg.slice(0, 2).toUpperCase()}
        </span>
        {authenticatedRole && (
          <button className="switch-account" type="button" onClick={onSignOut}>
            Sign out
          </button>
        )}
      </div>
    </header>
  );
}

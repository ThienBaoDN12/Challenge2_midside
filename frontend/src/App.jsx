import { useState } from "react";
import { TopBar } from "./components/TopBar";
import Login from "./pages/Login.jsx";
import { Invitation, Members } from "./screens/Account";
import {
  SellerWorkspace,
  ListingUpload,
  ListingFields,
  ListingPublish,
  SellerConnectionInbox,
} from "./screens/Seller";
import {
  BuyerWorkspace,
  BuyerDetail,
  BuyerRecommendations,
  BuyerConnectionInbox,
} from "./screens/Buyer";
import { DealRoom } from "./screens/DealRoom";
import { ContractEditor, ContractReview } from "./screens/Contract";
export default function App() {
  const [active, setActive] = useState("onboarding");
  const [authenticatedRole, setAuthenticatedRole] = useState(null);
  const [workspaceRole, setWorkspaceRole] = useState("SM");
  const [buyerRole, setBuyerRole] = useState("BM");
  const [dealConfirmed, setDealConfirmed] = useState(false);
  const roleOverride =
    active === "deal-room" ||
    active === "contract-edit" ||
    active === "contract-review"
      ? (authenticatedRole ?? undefined)
      : active === "seller-workspace" || active === "seller-inbox"
        ? workspaceRole === "SM"
          ? "Seller Manager"
          : "Seller Staff"
        : active === "buyer-workspace" ||
            active === "buyer-detail" ||
            active === "buyer-recommendations" ||
            active === "buyer-inbox"
          ? buyerRole === "BM"
            ? "Buyer Manager"
            : "Buyer Staff"
          : undefined;
  const handleLogin = (role) => {
    setAuthenticatedRole(role);
    if (role === "Seller Manager" || role === "Seller Staff") {
      setWorkspaceRole(role === "Seller Manager" ? "SM" : "SS");
      setActive("seller-workspace");
      return;
    }
    setBuyerRole(role === "Buyer Manager" ? "BM" : "BS");
    setActive("buyer-workspace");
  };
  const handleSignOut = () => {
    setAuthenticatedRole(null);
    setActive("onboarding");
  };
  return (
    <div className="app-shell">
      <TopBar
        active={active}
        roleOverride={roleOverride}
        authenticatedRole={authenticatedRole}
        onNavigate={setActive}
        onSignOut={handleSignOut}
      />
      {active === "onboarding" && (
        <Login
          onLogin={handleLogin}
          onOpenInvite={() => setActive("invitation")}
        />
      )}
      {active === "invitation" && <Invitation />}
      {active === "members" && <Members />}
      {active === "seller-workspace" && (
        <SellerWorkspace
          role={workspaceRole}
          onCreate={() => setActive("listing-upload")}
        />
      )}
      {active === "listing-upload" && (
        <ListingUpload
          onContinue={() => setActive("listing-fields")}
          onNavigate={setActive}
        />
      )}
      {active === "listing-fields" && (
        <ListingFields
          onContinue={() => setActive("listing-publish")}
          onNavigate={setActive}
        />
      )}
      {active === "listing-publish" && (
        <ListingPublish onNavigate={setActive} />
      )}
      {active === "seller-inbox" && (
        <SellerConnectionInbox
          role={workspaceRole}
          onEnterRoom={() => setActive("deal-room")}
        />
      )}
      {active === "buyer-workspace" && (
        <BuyerWorkspace
          role={buyerRole}
          onOpenListing={() => setActive("buyer-detail")}
        />
      )}
      {active === "buyer-detail" && (
        <BuyerDetail
          role={buyerRole}
          onBack={() => setActive("buyer-workspace")}
        />
      )}
      {active === "buyer-recommendations" && <BuyerRecommendations />}
      {active === "buyer-inbox" && (
        <BuyerConnectionInbox
          role={buyerRole}
          onEnterRoom={() => setActive("deal-room")}
        />
      )}
      {active === "deal-room" && authenticatedRole && (
        <DealRoom
          role={authenticatedRole}
          dealConfirmed={dealConfirmed}
          onNavigate={setActive}
        />
      )}
      {active === "contract-edit" && authenticatedRole === "Seller Manager" && (
        <ContractEditor
          onBack={() => setActive("deal-room")}
          onSent={() => setActive("contract-review")}
        />
      )}
      {active === "contract-review" && authenticatedRole && (
        <ContractReview
          role={authenticatedRole}
          dealConfirmed={dealConfirmed}
          onConfirm={() => setDealConfirmed(true)}
          onBack={() => setActive("deal-room")}
        />
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "./api";
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

const HOME = { seller: "seller-workspace", buyer: "buyer-workspace" };

export default function App() {
  const [active, setActive] = useState("onboarding");
  // Session from the backend: { user, organization, role, role_label }
  const [me, setMe] = useState(null);
  // Objects the current flow is working on
  const [listingId, setListingId] = useState(null);
  const [roomId, setRoomId] = useState(null);
  // Listing creation draft: snapshot + chosen public fields
  const [draft, setDraft] = useState(null);

  // Restore a session after a page refresh
  useEffect(() => {
    api
      .me()
      .then((data) => {
        if (data.organization) {
          setMe(data);
          setActive(HOME[data.organization.side]);
        }
      })
      .catch(() => {});
  }, []);

  const role = me?.role_label ?? null; // "Seller Manager" | "Seller Staff" | ...
  const sellerCode = role === "Seller Manager" ? "SM" : "SS";
  const buyerCode = role === "Buyer Manager" ? "BM" : "BS";

  const handleLogin = (session) => {
    setMe(session);
    setActive(HOME[session.organization.side]);
  };
  const handleSignOut = () => {
    api.logout();
    setMe(null);
    setRoomId(null);
    setListingId(null);
    setDraft(null);
    setActive("onboarding");
  };
  const enterRoom = (id) => {
    setRoomId(id);
    setActive("deal-room");
  };

  return (
    <div className="app-shell">
      <TopBar
        active={active}
        me={me}
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
      {active === "members" && me && <Members me={me} />}
      {active === "seller-workspace" && (
        <SellerWorkspace
          role={sellerCode}
          onCreate={() => {
            setDraft(null);
            setActive("listing-upload");
          }}
        />
      )}
      {active === "listing-upload" && (
        <ListingUpload
          draft={draft}
          onUploaded={(snapshot) =>
            setDraft({
              snapshot,
              publicKeys: snapshot.fields
                .filter((f) => f.default_public)
                .map((f) => f.key),
              confirmed: [],
            })
          }
          onContinue={() => setActive("listing-fields")}
          onNavigate={setActive}
        />
      )}
      {active === "listing-fields" && (
        <ListingFields
          draft={draft}
          onChange={setDraft}
          onContinue={() => setActive("listing-publish")}
          onNavigate={setActive}
        />
      )}
      {active === "listing-publish" && (
        <ListingPublish
          draft={draft}
          onNavigate={setActive}
          onDone={() => {
            setDraft(null);
            setActive("seller-workspace");
          }}
        />
      )}
      {active === "seller-inbox" && (
        <SellerConnectionInbox role={sellerCode} onEnterRoom={enterRoom} />
      )}
      {active === "buyer-workspace" && (
        <BuyerWorkspace
          role={buyerCode}
          onOpenListing={(id) => {
            setListingId(id);
            setActive("buyer-detail");
          }}
        />
      )}
      {active === "buyer-detail" && (
        <BuyerDetail
          role={buyerCode}
          listingId={listingId}
          onBack={() => setActive("buyer-workspace")}
        />
      )}
      {active === "buyer-recommendations" && <BuyerRecommendations />}
      {active === "buyer-inbox" && (
        <BuyerConnectionInbox role={buyerCode} onEnterRoom={enterRoom} />
      )}
      {active === "deal-room" && role && (
        <DealRoom
          role={role}
          roomId={roomId}
          onRoomResolved={setRoomId}
          onNavigate={setActive}
        />
      )}
      {active === "contract-edit" && role === "Seller Manager" && roomId && (
        <ContractEditor
          roomId={roomId}
          onBack={() => setActive("deal-room")}
          onSent={() => setActive("contract-review")}
        />
      )}
      {active === "contract-review" && role && roomId && (
        <ContractReview
          role={role}
          roomId={roomId}
          onBack={() => setActive("deal-room")}
          onNewVersion={() => setActive("contract-edit")}
        />
      )}
    </div>
  );
}

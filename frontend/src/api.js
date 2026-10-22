// Thin client for the FastAPI backend. Screens can switch from mock data to these calls one by one.
let token = null;
try {
  token = sessionStorage.getItem("tg_token");
} catch {
  token = null;
}

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.error?.message ?? `HTTP ${status}`);
    this.status = status;
    this.code = body?.error?.code;
    this.details = body?.error?.details;
  }
}

async function request(method, path, body, headers = {}) {
  const isForm = body instanceof FormData;
  const res = await fetch(`/api${path}`, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body && !isForm ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });
  const data = res.headers.get("content-type")?.includes("json")
    ? await res.json()
    : await res.blob();
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

const get = (p) => request("GET", p);
const post = (p, b, h) => request("POST", p, b, h);

export const api = {
  // F0
  demoAccounts: () => get("/auth/demo-accounts"),
  async login(email) {
    const data = await post("/auth/demo-login", { email });
    token = data.token;
    try {
      sessionStorage.setItem("tg_token", token);
    } catch {
      /* storage unavailable: keep token in memory */
    }
    return data.me;
  },
  logout() {
    token = null;
    try {
      sessionStorage.removeItem("tg_token");
    } catch {
      /* ignore */
    }
  },
  me: () => get("/me"),
  createOrg: (org) => post("/orgs", org),
  members: () => get("/orgs/me/members"),
  invite: (email, role) => post("/orgs/me/invites", { email, role }),
  acceptInvite: (t) => post(`/invites/${t}/accept`),

  resetDemo: () => post("/demo/reset"),
  notifications: () => get("/notifications"),
  removeMember: (userId) => request("DELETE", `/orgs/me/members/${userId}`),

  // F1
  templates: () => get("/templates"),
  templateFile: (id, format = "json") =>
    get(`/templates/${id}/download?format=${format}`),
  sampleFile: (id, variant) =>
    get(`/templates/${id}/sample?variant=${variant}`),
  publishListing: (id) => post(`/listings/${id}/publish`),
  pauseListing: (id) => post(`/listings/${id}/pause`),
  resumeListing: (id) => post(`/listings/${id}/resume`),
  uploadFile(templateId, file) {
    const fd = new FormData();
    fd.append("template_id", templateId);
    fd.append("file", file);
    return post("/files", fd);
  },
  snapshot: (id) => get(`/snapshots/${id}`),
  previewListing: (b) => post("/listings/preview", b),
  createListing: (b) => post("/listings", b),
  myListings: () => get("/listings/mine"),
  listing: (id) => get(`/listings/${id}`),

  // F2–F3
  discover: (query, criteria, acceptRelaxation) =>
    post("/discovery/ai", {
      query,
      criteria,
      accept_relaxation: acceptRelaxation,
    }),
  search: (params) => get(`/discovery/search?${new URLSearchParams(params)}`),
  propose: (listingId, note) =>
    post("/proposals", { listing_id: listingId, note }),
  proposals: () => get("/proposals"),
  sendProposal: (id, message) =>
    post(
      `/proposals/${id}/send`,
      { message, acknowledge_not_contract: true },
      { "Idempotency-Key": crypto.randomUUID() },
    ),
  dismissProposal: (id) => post(`/proposals/${id}/dismiss`),
  connection: (id) => get(`/connections/${id}`),
  connect: (listingId, message) =>
    post(
      "/connections",
      { listing_id: listingId, message, acknowledge_not_contract: true },
      { "Idempotency-Key": crypto.randomUUID() },
    ),
  connections: (box, status) =>
    get(`/connections?box=${box}${status ? `&status=${status}` : ""}`),
  acceptConnection: (id, confirmVersion) =>
    post(`/connections/${id}/accept`, { confirm_version: confirmVersion }),
  declineConnection: (id, reason) =>
    post(`/connections/${id}/decline`, { reason }),
  withdrawConnection: (id) => post(`/connections/${id}/withdraw`),

  // F4
  rooms: () => get("/rooms"),
  room: (id) => get(`/rooms/${id}`),
  ackListingVersion: (id) => post(`/rooms/${id}/ack-listing-version`),
  assistantHistory: (id) => get(`/rooms/${id}/assistant`),
  messages: (id) => get(`/rooms/${id}/messages`),
  sendMessage: (id, text) => post(`/rooms/${id}/messages`, { text }),
  ask: (id, question) => post(`/rooms/${id}/assistant`, { question }),
  share: (id, item) => post(`/rooms/${id}/shared`, item),
  revoke: (id, itemId) => post(`/rooms/${id}/shared/${itemId}/revoke`),
  closeRoom: (id) => post(`/rooms/${id}/close`),

  // F5
  contracts: (roomId) => get(`/rooms/${roomId}/contracts`),
  prefillContract: (roomId) => get(`/rooms/${roomId}/contracts/prefill`),
  sendContract: (roomId, terms) =>
    post(`/rooms/${roomId}/contracts`, { terms, send: true }),
  draftContract: (roomId, terms) =>
    post(`/rooms/${roomId}/contracts`, { terms, send: false }),
  sendDraft: (roomId, cid) => post(`/rooms/${roomId}/contracts/${cid}/send`),
  attachPdf(roomId, cid, file) {
    const fd = new FormData();
    fd.append("file", file);
    return post(`/rooms/${roomId}/contracts/${cid}/pdf`, fd);
  },
  confirmContract: (roomId, cid) =>
    post(`/rooms/${roomId}/contracts/${cid}/confirm`, {
      acknowledge_in_system: true,
    }),
  requestRevision: (roomId, cid, termNotes, note) =>
    post(`/rooms/${roomId}/contracts/${cid}/request-revision`, {
      term_notes: termNotes,
      note,
    }),
  declineContract: (roomId, cid, reason) =>
    post(`/rooms/${roomId}/contracts/${cid}/decline`, { reason }),
};

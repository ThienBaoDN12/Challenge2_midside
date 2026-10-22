# TrustGate AI — Backend (SRS v2 · T/H1)

Python API cho luồng: Seller Manager upload file mật → chọn trường công khai → Buyer tìm bằng Discovery AI → kết nối → phòng giao dịch (chat + trợ lý AI riêng mỗi bên + bổ sung thông tin) → hợp đồng.

Stack: **FastAPI + SQLite**. Không cần dịch vụ ngoài để chạy demo.

## Chạy

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

Frontend (`npm run dev` trong `frontend/`) gọi `/api/...`; Vite đã proxy sang `http://localhost:8000`.

Chạy test (mỗi test là một acceptance test trong SRS §13):

```bash
pytest -q
```

## Tài khoản demo (seed, khớp dữ liệu mẫu của frontend)

| Vai trò | Email | Tổ chức |
| --- | --- | --- |
| Seller Manager | lan@mekongagro.vn | Mekong Agro |
| Seller Staff | minh@mekongagro.vn | Mekong Agro |
| Buyer Manager | dara@ppimports.com.kh | Phnom Penh Imports |
| Buyer Staff | sokha@ppimports.com.kh | Phnom Penh Imports |
| Platform Admin | admin@trustgate.ai | — |

`POST /api/auth/demo-login {"email": ...}` trả về `token`; gửi kèm header `Authorization: Bearer <token>`.
Seed gồm listing `LST-VN-0161` (đã công bố), `0158` (nháp), `0142` (tạm dừng), `0119` (hết hạn) và 2 seller khác để Discovery có kết quả.
Xóa thư mục `.data/` để seed lại từ đầu.

## Cấu trúc

```
app/
  main.py            khởi tạo FastAPI, CORS, seed
  auth.py            xác định user / tổ chức / vai trò ở server (FR-02, FR-06)
  db.py              schema SQLite theo SRS §9
  errors.py          mã lỗi logic §10, thông báo cho người dùng (FR-46)
  seed.py            dữ liệu demo tái lập (NFR-12)
  routers/
    accounts.py      F0  đăng nhập, tổ chức, thành viên, lời mời, nhật ký, admin
    listings.py      F1  mẫu file, upload file mật, snapshot, listing, phiên bản
    connections.py   F2–F3  Discovery AI, tìm thường, đề xuất của staff, kết nối
    rooms.py         F4  phòng, chat, trợ lý AI, bổ sung / thu hồi, đóng phòng
    contracts.py     F5  hợp đồng có phiên bản, xác nhận / yêu cầu sửa / từ chối
  services/
    templates.py     mẫu cố định theo loại sản phẩm (cà phê v3: 14 trường)
    extractor.py     tách trường bằng code, không LLM (FR-10)
    vault.py         mã hóa file mật (Fernet)
    listings.py      projection công khai, phiên bản, diff, thông báo phòng
    discovery.py     Discovery AI theo luật, chỉ đọc projection công khai
    assistant.py     trợ lý AI trong phòng, chỉ 3 nguồn được phép
    contracts.py     điền sẵn điều khoản, kiểm tra chính sách, đánh dấu khác biệt
    units.py         tính tổng giá trị bằng Decimal, quy đổi kg/tấn
    audit.py         nhật ký không chứa dữ liệu mật
    ratelimit.py     giới hạn 10 kết nối/giờ, 30 câu hỏi AI/giờ (NFR-10)
tests/test_acceptance.py
```

## API chính

| Nhóm | Endpoint |
| --- | --- |
| Auth | `POST /api/auth/demo-login`, `POST /api/auth/signup`, `GET /api/me`, `GET /api/auth/demo-accounts` |
| Tổ chức (C1–C3) | `POST /api/orgs`, `GET /api/orgs/me/members`, `POST /api/orgs/me/invites`, `GET/POST /api/invites/{token}[/accept]`, `PATCH/DELETE /api/orgs/me/members/{id}` |
| Listing (S1–S4) | `GET /api/templates`, `GET /api/templates/{id}/download?format=xlsx`, `POST /api/files`, `GET /api/snapshots/{id}`, `POST /api/listings/preview`, `POST /api/listings`, `GET /api/listings/mine`, `PUT /api/listings/{id}`, `POST /api/listings/{id}/publish\|pause\|resume` |
| Tìm kiếm (B1–B3) | `POST /api/discovery/ai`, `GET /api/discovery/search`, `POST/GET /api/proposals`, `POST /api/proposals/{id}/send\|dismiss` |
| Kết nối (S5, B4) | `POST /api/connections` (header `Idempotency-Key`), `GET /api/connections?box=received\|sent&status=`, `POST /api/connections/{id}/accept\|decline\|withdraw` |
| Phòng (R1–R2) | `GET /api/rooms/{id}`, `GET/POST /api/rooms/{id}/messages`, `GET/POST /api/rooms/{id}/assistant`, `POST /api/rooms/{id}/shared`, `POST /api/rooms/{id}/shared/{item}/revoke`, `POST /api/rooms/{id}/close` |
| Hợp đồng (R3–R4) | `GET /api/rooms/{id}/contracts/prefill`, `POST /api/rooms/{id}/contracts`, `POST .../{cid}/send\|confirm\|request-revision\|decline`, `POST/GET .../{cid}/pdf` |
| Khác | `GET /api/notifications`, `GET /api/audit` (manager) |

Lỗi luôn có dạng `{"error": {"code", "message", "details?"}}` với `code` ∈ `unauthenticated, forbidden, not_found, conflict, expired, validation_failed, policy_denied, rate_limited, unavailable`.

## Phần thật / phần mô phỏng

| Hạng mục | Trạng thái |
| --- | --- |
| Phân quyền 4 vai trò, kiểm tra ở server | Thật, có test `forbidden` |
| Tách trường bằng code, lỗi theo dòng | Thật (`.json`, `.xlsx`) |
| Mã hóa file mật | Fernet với khóa cục bộ `.data/dev_file.key`; **chưa** dùng khóa do TideCloak quản lý (§15.2 còn mở) |
| Đăng nhập TideCloak | Mô phỏng bằng `demo-login`; production thay bằng OIDC của TideCloak |
| Discovery AI, trợ lý AI | Theo luật + từ khóa (đúng mặc định §15.2). Nếu đặt `GEMINI_API_KEY`, Gemini chỉ diễn đạt lại các dữ kiện đã lọc từ 3 nguồn |
| Tổng giá trị hợp đồng | Thật, `Decimal`, quy đổi kg/tấn |
| Rate limit | Bộ nhớ trong một process |

Biến môi trường: `TRUSTGATE_DB`, `TRUSTGATE_DATA_DIR`, `TRUSTGATE_FILE_KEY`, `TRUSTGATE_CORS`, `GEMINI_API_KEY`, `GEMINI_MODEL`.

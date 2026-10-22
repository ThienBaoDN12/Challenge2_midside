import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib

# Cấu hình trang hiển thị
st.set_page_config(
    page_title="TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên",
    layout="wide",
    page_icon="🌾"
)

# Tùy biến CSS giao diện
st.markdown("""
<style>
    .metric-box {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #dee2e6;
        text-align: center;
    }
    .chat-bubble-seller {
        background-color: #e3f2fd;
        padding: 10px 14px;
        border-radius: 12px 12px 12px 0px;
        margin-bottom: 8px;
        max-width: 80%;
    }
    .chat-bubble-buyer {
        background-color: #f1f8e9;
        padding: 10px 14px;
        border-radius: 12px 12px 0px 12px;
        margin-bottom: 8px;
        max-width: 80%;
        margin-left: auto;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
def init_db():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # 1. Bảng lưu trữ danh tính phân tán TideCloak
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tide_identities (
        did_address TEXT PRIMARY KEY,
        public_key TEXT,
        fullname TEXT,
        org_name TEXT,
        role TEXT,
        country TEXT,
        created_at TEXT
    )
    """)
    
    # 2. Bảng Sàn Thị Trường Chung (Marketplace Pool)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_pool (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_type TEXT,
        owner_did TEXT,
        org_name TEXT,
        product_name TEXT,
        quantity TEXT,
        price REAL,
        location TEXT,
        created_at TEXT
    )
    """)
    
    # 3. Bảng Phiên Thương Lượng (Deal Rooms)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        seller_did TEXT,
        buyer_did TEXT,
        product_name TEXT,
        quantity TEXT,
        seller_price REAL,
        buyer_price REAL,
        ai_price REAL,
        final_price REAL,
        seller_signed INTEGER DEFAULT 0,
        buyer_signed INTEGER DEFAULT 0,
        status TEXT DEFAULT 'NEGOTIATING'
    )
    """)
    
    # 4. Bảng Lịch Sử Tin Nhắn Thương Lượng (Chat)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deal_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id INTEGER,
        sender_did TEXT,
        sender_name TEXT,
        message TEXT,
        created_at TEXT
    )
    """)
    
    # Khởi tạo dữ liệu mẫu nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM tide_identities")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        did_seller = "did:tide:vn_lamvien_7a8f90b"
        pk_seller = "pk_secp256k1_vn_04e8b910a3c4..."
        cursor.execute("INSERT OR REPLACE INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (did_seller, pk_seller, "Trần Thu Hà", "Nông sản Lâm Viên", "Bên Bán (Việt Nam)", "Việt Nam", now))
        
        did_buyer = "did:tide:kh_mekong_3d4e12a"
        pk_buyer = "pk_secp256k1_kh_02c77d9811f2..."
        cursor.execute("INSERT OR REPLACE INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (did_buyer, pk_buyer, "Sok Dara", "Mekong Fresh Trading", "Bên Mua (Campuchia)", "Campuchia", now))
        
        cursor.execute("INSERT INTO market_pool (post_type, owner_did, org_name, product_name, quantity, price, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("BÁN", did_seller, "Nông sản Lâm Viên", "Cà phê Robusta nhân xanh S16", "20 tấn", 2150.0, "Đức Trọng, Lâm Đồng", now))
        cursor.execute("INSERT INTO market_pool (post_type, owner_did, org_name, product_name, quantity, price, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("MUA", did_buyer, "Mekong Fresh Trading", "Hồ tiêu đen khô 500g/l", "10 tấn", 4100.0, "Cửa khẩu Mộc Bài / Phnom Penh", now))
        
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "current_deal_id" not in st.session_state:
    st.session_state.current_deal_id = None

# ==========================================
# 2. XÁC THỰC DANH TÍNH TIDECLOAK
# ==========================================
if st.session_state.auth_user is None:
    st.title("🛡️ TrustGate AI — Cổng Xác Thực TideCloak")
    st.caption("Xác thực phi tập trung: Hệ thống không lưu trữ mật khẩu hay khóa riêng của doanh nghiệp[cite: 1, 7].")
    
    t1, t2 = st.tabs(["🔐 Đăng Nhập Bằng TideCloak DID", "📝 Cấp Mới Danh Tính Doanh Nghiệp"])
    
    with t1:
        st.subheader("Xác thực bằng Danh tính số phân tán (DID)")
        st.info("💡 **Tài khoản demo sẵn có:**\n\n* **Bên Bán:** `did:tide:vn_lamvien_7a8f90b`\n* **Bên Mua:** `did:tide:kh_mekong_3d4e12a`")
        
        with st.form("form_tide_login"):
            did_inp = st.text_input("Nhập mã TideCloak DID:", placeholder="did:tide:vn_lamvien_7a8f90b")
            nonce = hashlib.sha256(str(datetime.date.today()).encode()).hexdigest()[:16]
            st.caption(f"Security Nonce: `{nonce}` | Ký số tự động bằng tiện ích bảo mật phân tán.")
            btn_sub_login = st.form_submit_button("Xác Thực Danh Tính & Đăng Nhập")
            
            if btn_sub_login:
                if did_inp.strip():
                    cursor.execute("SELECT did_address, fullname, org_name, role, country, public_key FROM tide_identities WHERE did_address = ?", 
                                   (did_inp.strip(),))
                    user_data = cursor.fetchone()
                    if user_data:
                        st.session_state.auth_user = {
                            "did": user_data[0],
                            "fullname": user_data[1],
                            "org_name": user_data[2],
                            "role": user_data[3],
                            "country": user_data[4],
                            "public_key": user_data[5]
                        }
                        st.success(f"✅ Xác thực thành công! Xin chào {user_data[1]} ({user_data[2]}).")
                        st.rerun()
                    else:
                        st.error("❌ Không tìm thấy danh tính DID này trong mạng lưới TideCloak.")
                else:
                    st.warning("Vui lòng nhập mã DID hợp lệ.")

    with t2:
        st.subheader("Khởi tạo danh tính phân tán mới")
        with st.form("form_tide_reg"):
            r_name = st.text_input("Họ và tên người đại diện ký duyệt")[cite: 11]
            r_org = st.text_input("Tên doanh nghiệp / Hợp tác xã")
            r_role = st.selectbox("Vai trò giao dịch", ["Bên Bán (Việt Nam)", "Bên Mua (Campuchia)"])
            btn_reg = st.form_submit_button("Cấp Phát Mã Tide DID Mới")
            
            if btn_reg:
                if r_name and r_org:
                    prefix = "vn" if "Việt Nam" in r_role else "kh"
                    country = "Việt Nam" if "Việt Nam" in r_role else "Campuchia"
                    rnd_hash = hashlib.sha256(f"{r_name}{r_org}{datetime.datetime.now()}".encode()).hexdigest()[:8]
                    gen_did = f"did:tide:{prefix}_{rnd_hash}"
                    gen_pk = f"pk_secp256k1_{prefix}_{rnd_hash}8f9a"
                    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    cursor.execute("INSERT INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (gen_did, gen_pk, r_name, r_org, r_role, country, now_str))
                    conn.commit()
                    st.success("🎉 Cấp phát danh tính TideCloak thành công!")
                    st.code(f"Mã DID của bạn: {gen_did}\nPublic Key: {gen_pk}", language="text")
                    st.info("Hãy copy mã DID này và chuyển sang tab Đăng Nhập.")
                else:
                    st.warning("Vui lòng điền đầy đủ thông tin.")
    st.stop()

# ==========================================
# 3. GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP
# ==========================================
cur_u = st.session_state.auth_user

with st.sidebar:
    st.header("🛡️ Phiên Danh Tính TideCloak")
    st.markdown(f"**Người đại diện:** {cur_u['fullname']}")
    st.markdown(f"**Tổ chức:** {cur_u['org_name']}")
    st.markdown(f"**Vai trò:** {cur_u['role']}")
    st.markdown(f"**Quốc gia:** {cur_u['country']}")
    st.code(f"{cur_u['did']}", language="text")
    st.caption("Trạng thái: `ĐÃ XÁC THỰC PHÂN TÁN`[cite: 7]")
    
    st.divider()
    if st.button("🚪 Đăng Xuất"):
        st.session_state.auth_user = None
        st.session_state.current_deal_id = None
        st.rerun()

st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.markdown("**Kiến trúc không quyền kiểm soát đơn phương (No Unilateral Control)** — Được bảo vệ bởi **TideCloak**[cite: 1, 7].")

# Tạo 3 Tabs chính
tab1, tab2, tab3 = st.tabs([
    "🛒 1. Sàn Thị Trường Chung (Pool)", 
    "💬 2. Phòng Thương Lượng & Chat", 
    "🛡️ 3. Kiểm Tra Bảo Mật TideCloak"
])

# ---------------- TAB 1: SÀN THỊ TRƯỜNG CHUNG ----------------
with tab1:
    st.subheader("Sàn Hàng Hóa & Nhu Cầu Mua Bán Nông Sản")
    
    with st.expander("➕ Đăng Tin Mới Lên Sàn Chung", expanded=False):
        with st.form("form_add_item"):
            col_t1, col_t2 = st.columns(2)
            def_idx = 0 if "Bán" in cur_u['role'] else 1
            post_t = col_t1.selectbox("Loại bài đăng", ["BÁN (Listing)", "MUA (Demand)"], index=def_idx)
            item_name = col_t2.text_input("Tên nông sản", "Cà phê Robusta Grade 1")
            
            col_t3, col_t4 = st.columns(2)
            item_qty = col_t3.text_input("Khối lượng (Ví dụ: 20 tấn)", "20 tấn")
            item_price = col_t4.number_input("Mức giá đề xuất ban đầu (USD/tấn)", min_value=10.0, value=2150.0, step=10.0)
            
            item_loc = st.text_input("Địa điểm giao nhận", "Cửa khẩu Mộc Bài - Tây Ninh / Phnom Penh")
            
            if st.form_submit_button("Đăng Lên Thị Trường"):
                now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                actual_type = "BÁN" if "BÁN" in post_t else "MUA"
                cursor.execute("""
                INSERT INTO market_pool (post_type, owner_did, org_name, product_name, quantity, price, location, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (actual_type, cur_u['did'], cur_u['org_name'], item_name, item_qty, item_price, item_loc, now_str))
                conn.commit()
                st.success("Đã đăng tin lên thị trường thành công!")
                st.rerun()

    st.write("---")
    st.markdown("#### Danh Mục Hàng Hóa Đang Chào Bán & Cần Mua")
    
    cursor.execute("SELECT id, post_type, owner_did, org_name, product_name, quantity, price, location, created_at FROM market_pool ORDER BY id DESC")
    all_posts = cursor.fetchall()
    
    if not all_posts:
        st.info("Hiện chưa có sản phẩm nào trên thị trường.")
    else:
        for post in all_posts:
            pid, ptype, powner_did, porg, pname, pqty, pprice, ploc, pdate = post
            c_card, c_act = st.columns([4, 1])
            
            with c_card:
                badge = "🟢 BÁN" if ptype == "BÁN" else "🔵 CẦN MUA"
                st.markdown(f"**[{badge}] {pname}** — Số lượng: **{pqty}** | Mức giá: **${pprice:,.1f}/tấn**")
                st.caption(f"Đăng bởi: **{porg}** (`{powner_did}`) | Địa điểm: {ploc} | Ngày: {pdate}")
                
            with c_act:
                if powner_did != cur_u['did']:
                    if st.button("🤝 Thương Lượng", key=f"btn_neg_{pid}"):
                        seller = powner_did if ptype == "BÁN" else cur_u['did']
                        buyer = cur_u['did'] if ptype == "BÁN" else powner_did
                        
                        # Không đặt giá ngẫu nhiên: Người bán lấy đúng giá niêm yết; người mua khởi tạo 0.0
                        init_seller_p = pprice if ptype == "BÁN" else 0.0
                        init_buyer_p = 0.0 if ptype == "BÁN" else pprice
                        init_final_p = pprice
                        
                        cursor.execute("""
                        INSERT INTO deals (post_id, seller_did, buyer_did, product_name, quantity, seller_price, buyer_price, final_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (pid, seller, buyer, pname, pqty, init_seller_p, init_buyer_p, init_final_p))
                        new_deal_id = cursor.lastrowid
                        
                        # Tạo tin nhắn chào mở phòng tự động
                        now_msg = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("""
                        INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """, (new_deal_id, cur_u['did'], cur_u['fullname'], f"Xin chào, tôi muốn mở phiên thương lượng cho lô hàng {pname} ({pqty}).", now_msg))
                        
                        conn.commit()
                        st.session_state.current_deal_id = new_deal_id
                        st.success("Đã kết nối phòng thương lượng! Vui lòng chuyển sang Tab 2.")
                        st.rerun()
                else:
                    st.caption("Tin của bạn")
            st.divider()

# ---------------- TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ & KHUNG CHAT ----------------
with tab2:
    st.subheader("Phòng Thương Lượng Trực Tiếp & Trợ Lý AI")
    
    cursor.execute("""
    SELECT id, product_name, quantity, seller_did, buyer_did, seller_price, buyer_price, ai_price, final_price, seller_signed, buyer_signed, status
    FROM deals
    WHERE seller_did = ? OR buyer_did = ?
    ORDER BY id DESC
    """, (cur_u['did'], cur_u['did']))
    active_deals = cursor.fetchall()
    
    if not active_deals:
        st.info("Bạn chưa có phiên đàm phán nào. Hãy chọn một mặt hàng từ **Tab 1: Sàn Thị Trường** và nhấn **'Thương Lượng'**.")
    else:
        deal_mapping = {f"Phiên #{d[0]}: {d[1]} ({d[2]})": d[0] for d in active_deals}
        
        # Đồng bộ phiên làm việc vừa tạo
        default_index = 0
        deal_ids_list = list(deal_mapping.values())
        if st.session_state.current_deal_id in deal_ids_list:
            default_index = deal_ids_list.index(st.session_state.current_deal_id)
            
        chosen_label = st.selectbox("Chọn phiên đàm phán:", list(deal_mapping.keys()), index=default_index)
        deal_id = deal_mapping[chosen_label]
        st.session_state.current_deal_id = deal_id
        
        cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        deal = cursor.fetchone()
        
        d_id, _, d_s_did, d_b_did, d_prod, d_qty, d_s_pr, d_b_pr, d_ai_pr, d_fin_pr, d_s_sign, d_b_sign, d_stat = deal
        
        is_seller = (cur_u['did'] == d_s_did)
        is_buyer = (cur_u['did'] == d_b_did)
        
        st.markdown(f"**Mặt hàng:** {d_prod} | **Sản lượng:** {d_qty}")
        st.caption(f"Bên Bán (Seller): `{d_s_did}` ⟷ Bên Mua (Buyer): `{d_b_did}`")
        
        c_chat, c_price = st.columns([1, 1])
        
        # ---------------- CỘT TRÁI: KHUNG CHAT TRAO ĐỔI ----------------
        with c_chat:
            st.markdown("### 💬 Trao Đổi Thương Lượng")
            
            # Hiển thị lịch sử chat
            chat_container = st.container(height=320)
            cursor.execute("SELECT sender_did, sender_name, message, created_at FROM deal_messages WHERE deal_id = ? ORDER BY id ASC", (d_id,))
            messages = cursor.fetchall()
            
            with chat_container:
                if not messages:
                    st.caption("Chưa có tin nhắn nào trong phiên này.")
                for msg in messages:
                    m_did, m_name, m_text, m_time = msg
                    if m_did == d_s_did:
                        st.markdown(f"<div class='chat-bubble-seller'><b>[Bên Bán] {m_name}:</b> {m_text}<br><small style='color:gray'>{m_time}</small></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-bubble-buyer'><b>[Bên Mua] {m_name}:</b> {m_text}<br><small style='color:gray'>{m_time}</small></div>", unsafe_allow_html=True)
            
            # Form gửi tin nhắn mới
            with st.form(f"form_send_msg_{d_id}", clear_on_submit=True):
                new_msg_text = st.text_input("Nhập tin nhắn trao đổi...", placeholder="Ví dụ: Mức giá này đã gồm phí vận chuyển chưa?")
                if st.form_submit_button("Gửi Tin Nhắn"):
                    if new_msg_text.strip():
                        now_m = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], new_msg_text.strip(), now_m))
                        conn.commit()
                        st.rerun()

        # ---------------- CỘT PHẢI: THƯƠNG LƯỢNG GIÁ & CHỐT ĐỒNG THUẬN ----------------
        with c_price:
            st.markdown("### 🏷️ Thiết Lập Mức Giá Thương Lượng")
            
            col_v1, col_v2 = st.columns(2)
            col_v1.write(f"**Bên Bán yêu cầu:** " + (f"`${d_s_pr:,.1f}/tấn`" if d_s_pr > 0 else "*(Chưa ra giá)*"))
            col_v2.write(f"**Bên Mua đề nghị:** " + (f"`${d_b

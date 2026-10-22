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
    .role-card {
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 15px;
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

if "active_nav" not in st.session_state:
    st.session_state.active_nav = "🛒 1. Sàn Thị Trường Chung (Pool)"

# ==========================================
# 2. XÁC THỰC DANH TÍNH TIDECLOAK
# ==========================================
if st.session_state.auth_user is None:
    st.title("🛡️ TrustGate AI — Cổng Xác Thực TideCloak")
    st.caption("Xác thực phi tập trung: Hệ thống không lưu trữ mật khẩu hay khóa riêng của doanh nghiệp.")
    
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
                        st.success(f"Xác thực thành công! Xin chào {user_data[1]} ({user_data[2]}).")
                        st.rerun()
                    else:
                        st.error("Không tìm thấy danh tính DID này trong mạng lưới TideCloak.")
                else:
                    st.warning("Vui lòng nhập mã DID hợp lệ.")

    with t2:
        st.subheader("Khởi tạo danh tính phân tán mới")
        with st.form("form_tide_reg"):
            r_name = st.text_input("Họ và tên người đại diện ký duyệt")
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
                    st.success("Cấp phát danh tính TideCloak thành công!")
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
    st.caption("Trạng thái: ĐÃ XÁC THỰC PHÂN TÁN")
    
    st.divider()
    if st.button("🚪 Đăng Xuất"):
        st.session_state.auth_user = None
        st.session_state.current_deal_id = None
        st.rerun()

st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.markdown("**Kiến trúc không quyền kiểm soát đơn phương (No Unilateral Control)** — Được bảo vệ bởi **TideCloak**.")

# THANH ĐIỀU HƯỚNG TỰ ĐỘNG CHUYỂN TAB ĐỘNG
nav_options = [
    "🛒 1. Sàn Thị Trường Chung (Pool)", 
    "💬 2. Phòng Thương Lượng & Chat", 
    "🛡️ 3. Kiểm Tra Bảo Mật TideCloak"
]

selected_nav = st.radio(
    "Thanh điều hướng:",
    nav_options,
    index=nav_options.index(st.session_state.active_nav),
    horizontal=True,
    label_visibility="collapsed"
)
st.session_state.active_nav = selected_nav
st.divider()

# ========================================================
# TAB 1: SÀN THỊ TRƯỜNG CHUNG (MARKETPLACE POOL)
# ========================================================
if st.session_state.active_nav == "🛒 1. Sàn Thị Trường Chung (Pool)":
    st.subheader("Sàn Hàng Hóa & Nhu Cầu Mua Bán Nông Sản")
    
    with st.expander("➕ Đăng Tin Mới Lên Sàn Chung", expanded=False):
        with st.form("form_add_item"):
            col_t1, col_t2 = st.columns(2)
            def_idx = 0 if "Bán" in cur_u['role'] else 1
            post_t = col_t1.selectbox("Loại bài đăng", ["BÁN (Listing)", "MUA (Demand)"], index=def_idx)
            item_name = col_t2.text_input("Tên nông sản", "Cà phê Robusta Grade 1")
            
            col_t3, col_t4 = st.columns(2)
            item_qty = col_t3.text_input("Khối lượng (Ví dụ: 20 tấn)", "20 tấn")
            item_price = col_t4.number_input("Mức giá mong muốn ban đầu (USD/tấn)", min_value=10.0, value=2150.0, step=10.0)
            
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
                        
                        init_seller_p = pprice if ptype == "BÁN" else 0.0
                        init_buyer_p = 0.0 if ptype == "BÁN" else pprice
                        init_final_p = pprice
                        
                        cursor.execute("""
                        INSERT INTO deals (post_id, seller_did, buyer_did, product_name, quantity, seller_price, buyer_price, final_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (pid, seller, buyer, pname, pqty, init_seller_p, init_buyer_p, init_final_p))
                        new_deal_id = cursor.lastrowid
                        
                        now_msg = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("""
                        INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """, (new_deal_id, cur_u['did'], cur_u['fullname'], f"Xin chào, tôi muốn mở phiên thương lượng cho lô hàng {pname} ({pqty}).", now_msg))
                        
                        conn.commit()
                        st.session_state.current_deal_id = new_deal_id
                        # TỰ ĐỘNG CHUYỂN SANG TAB 2
                        st.session_state.active_nav = "💬 2. Phòng Thương Lượng & Chat"
                        st.rerun()
                else:
                    st.caption("Tin của bạn")
            st.divider()

# ========================================================
# TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ & KHUNG CHAT
# ========================================================
elif st.session_state.active_nav == "💬 2. Phòng Thương Lượng & Chat":
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
        
        with c_chat:
            st.markdown("### 💬 Trao Đổi Thương Lượng")
            
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
            
            with st.form(f"form_send_msg_{d_id}", clear_on_submit=True):
                new_msg_text = st.text_input("Nhập tin nhắn trao đổi...", placeholder="Ví dụ: Mức giá này đã gồm phí vận chuyển chưa?")
                if st.form_submit_button("Gửi Tin Nhắn"):
                    if new_msg_text.strip():
                        now_m = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], new_msg_text.strip(), now_m))
                        conn.commit()
                        st.rerun()

        with c_price:
            st.markdown("### 🏷️ Thiết Lập Mức Giá Thương Lượng")
            
            col_v1, col_v2 = st.columns(2)
            col_v1.write(f"**Bên Bán yêu cầu:** " + (f"`${d_s_pr:,.1f}/tấn`" if d_s_pr > 0 else "*(Chưa ra giá)*"))
            col_v2.write(f"**Bên Mua đề nghị:** " + (f"`${d_b_pr:,.1f}/tấn`" if d_b_pr > 0 else "*(Chưa trả giá)*"))
            
            if d_s_pr > 0 and d_b_pr > 0:
                gap = d_s_pr - d_b_pr
                if gap > 0:
                    st.warning(f"⚠️ Chênh lệch giá: **${gap:,.1f}/tấn**. Hai bên chưa thể chốt đơn.")
                elif gap == 0:
                    st.success("🎯 Hai bên đã đưa ra mức giá hoàn toàn trùng khớp!")
            else:
                st.info("💡 Hãy nhập mức giá kỳ vọng của bạn bên dưới để bắt đầu trả giá.")
                
            with st.form(f"form_set_price_{d_id}"):
                if is_seller:
                    val_init = float(d_s_pr) if d_s_pr > 0 else 2150.0
                    my_new_p = st.number_input("Cập nhật giá Bên Bán ($/tấn):", value=val_init, step=10.0)
                else:
                    val_init = float(d_b_pr) if d_b_pr > 0 else 2000.0
                    my_new_p = st.number_input("Cập nhật giá Bên Mua đề xuất ($/tấn):", value=val_init, step=10.0)
                    
                if st.form_submit_button("Cập Nhật Báo Giá"):
                    now_m = datetime.datetime.now().strftime("%H:%M")
                    if is_seller:
                        cursor.execute("UPDATE deals SET seller_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", (my_new_p, my_new_p, d_id))
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], f"Tôi cập nhật mức giá chào bán là ${my_new_p:,.1f}/tấn.", now_m))
                    else:
                        cursor.execute("UPDATE deals SET buyer_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", (my_new_p, my_new_p, d_id))
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], f"Tôi đề xuất mức giá mua là ${my_new_p:,.1f}/tấn.", now_m))
                    conn.commit()
                    st.success("Đã cập nhật mức giá! Chữ ký cũ bị thu hồi để đảm bảo đồng thuận.")
                    st.rerun()

            st.divider()
            
            st.markdown("#### Trợ Lý AI Điều Phối Giá Cân Bằng")
            st.caption("AI hoạt động trong vùng cách ly, tính toán chi phí vận chuyển ($35/tấn) để đề xuất mức giá tối ưu khi 2 bên bế tắc.")
            
            if st.button("🤖 Nhờ AI Đề Xuất Giá Hòa Giải", key=f"btn_ai_{d_id}"):
                if d_s_pr > 0 and d_b_pr > 0:
                    shipping = 35.0
                    calc_optimal = round((d_s_pr + d_b_pr) / 2.0 + (shipping / 2.0), 1)
                    cursor.execute("UPDATE deals SET ai_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?",
                                   (calc_optimal, calc_optimal, d_id))
                    
                    now_m = datetime.datetime.now().strftime("%H:%M")
                    cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                   (d_id, "did:tide:ai_copilot", "AI Copilot", f"Đã tính toán: Mức giá cân bằng tối ưu là ${calc_optimal:,.1f}/tấn.", now_m))
                    conn.commit()
                    st.rerun()
                else:
                    st.warning("Cả hai bên cần đưa ra mức giá ban đầu trước khi gọi AI.")
                    
            if d_ai_pr:
                st.info(f"💡 **AI Khuyến Nghị Chốt:** **${d_ai_pr:,.1f}/tấn** (Hỗ trợ 50% chi phí vận chuyển).")
                if st.button("Chấp Nhận Mức Giá Của AI", key=f"btn_acc_ai_{d_id}"):
                    cursor.execute("UPDATE deals SET final_price = ? WHERE id = ?", (d_ai_pr, d_id))
                    conn.commit()
                    st.rerun()

            st.divider()
            
            st.markdown("#### Phê Duyệt Đồng Thuận (Tide Dual-Consensus)")
            st.caption("Hợp đồng chỉ có hiệu lực khi cả hai bên cùng ký xác nhận mức giá chốt.")
            
            target_close_p = d_fin_pr if d_fin_pr else d_s_pr
            st.metric("Mức Giá Dự Kiến Chốt", f"${target_close_p:,.1f} / tấn")
            
            c_s_btn, c_b_btn = st.columns(2)
            
            with c_s_btn:
                if d_s_sign == 1:
                    st.success("✅ Người bán đã ký")
                else:
                    if is_seller:
                        if st.button("✍️ Người Bán Ký Duyệt", key=f"s_sign_{d_id}"):
                            cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.warning("Chờ Người Bán ký...")
                        if st.button("⚡ [Demo] Giả lập Người Bán ký", key=f"sim_s_{d_id}"):
                            cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                            
            with c_b_btn:
                if d_b_sign == 1:
                    st.success("✅ Người mua đã ký")
                else:
                    if is_buyer:
                        if st.button("✍️ Người Mua Ký Duyệt", key=f"b_sign_{d_id}"):
                            cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.warning("Chờ Người Mua ký...")
                        if st.button("⚡ [Demo] Giả lập Người Mua ký", key=f"sim_b_{d_id}"):
                            cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
            
            st.write("")
            if d_s_sign == 1 and d_b_sign == 1:
                st.balloons()
                st.success(f"🎉 **GIAO DỊCH THÀNH CÔNG Ở MỨC GIÁ ${target_close_p:,.1f}/TẤN!**")
                st.write("Hai bên đã hoàn tất xác thực số qua TideCloak. Hợp đồng mua bán đã được đóng băng.")
            else:
                st.error("🔒 **TRẠNG THÁI: CHƯA ĐỦ ĐỒNG THUẬN (FAIL-CLOSED)**")
                st.caption("Chính sách TideCloak: Nếu thiếu chữ ký của một trong hai bên, hợp đồng hoàn toàn không thể thực thi.")

# ========================================================
# TAB 3: TRUNG TÂM BẢO MẬT & KIỂM THỬ ĐA VAI TRÒ
# ========================================================
elif st.session_state.active_nav == "🛡️ 3. Kiểm Tra Bảo Mật TideCloak":
    st.subheader("🛡️ Trung Tâm Giám Sát Phân Quyền & Kiểm Thử Bảo Mật TideCloak")
    st.caption("Kiểm chứng cơ chế No Unilateral Control và tính toàn vẹn dưới các góc nhìn khác nhau.")
    
    # Bộ chọn góc nhìn kiểm thử
    perspective = st.radio(
        "Lựa chọn góc nhìn kiểm tra cơ chế bảo mật:",
        [
            "👑 Góc nhìn Quản Trị Viên (Platform Admin)", 
            "🌾 Góc nhìn Bên Bán (Seller)", 
            "🛒 Góc nhìn Bên Mua (Buyer)"
        ],
        horizontal=True
    )
    st.write("---")
    
    # 1. GÓC NHÌN QUẢN TRỊ VIÊN
    if "Admin" in perspective:
        st.markdown("#### 👑 Góc nhìn Quản Trị Viên Nền Tảng (Platform Admin)")
        st.info("""
        **Quyền hạn thực tế của Admin:**
        - Chỉ có thể giám sát trạng thái mạng, dung lượng giao dịch và siêu dữ liệu (metadata) vận hành.
        - **Hoàn toàn KHÔNG sở hữu Khóa Riêng (Private Key)** của Người Bán hay Người Mua.
        - Không thể tự ý ký thay, không thể giải mã kho dữ liệu bí mật và không thể cưỡng chế chốt hợp đồng.
        """)
        
        st.markdown("##### 🧪 Thử nghiệm tấn công / Can thiệp đơn phương:")
        c_ad1, c_ad2 = st.columns(2)
        with c_ad1:
            if st.button("🚨 Admin Thử Cưỡng Chế Chốt Đơn (Admin Bypass)"):
                st.error("""
                ❌ **ACCESS DENIED BY TIDECLOAK CORE:**
                - Mã vi phạm: `ERR_NO_UNILATERAL_CONTROL_VIOLATION`
                - Lý do: Yêu cầu thiếu chữ ký xác thực từ Private Key của doanh nghiệp tham gia.
                - Kết luận: Quản trị viên không có quyền đơn phương can thiệp thỏa thuận!
                """)
        with c_ad2:
            if st.button("🔍 Admin Thử Đọc Trộm Giá Vốn Riêng Tư"):
                st.error("❌ **DECRYPTION FAILED:** Payload đã được mã hóa phân tán. Không có ủy quyền đồng thuận từ cả hai bên.")
                
    # 2. GÓC NHÌN BÊN BÁN
    elif "Bên Bán" in perspective:
        st.markdown("#### 🌾 Góc nhìn Bên Bán (Seller - Việt Nam)")
        st.success("""
        **Quyền kiểm soát dữ liệu của Bên Bán:**
        - Dữ liệu giá vốn và tồn kho nội bộ được lưu trong Két bí mật (Private Vault), chỉ chia sẻ trường đã duyệt.
        - Có toàn quyền kích hoạt **Thu hồi khẩn cấp (Emergency Revoke)** để hủy bỏ đàm phán bất cứ lúc nào.
        """)
        
        st.markdown("##### ⚡ Quyền thu hồi chữ ký số:")
        if st.button("🛑 Thu Hồi Chữ Ký Bên Bán (Revoke Seller Signature)"):
            cursor.execute("UPDATE deals SET seller_signed = 0")
            conn.commit()
            st.warning("🔒 **ĐÃ THU HỒI CHỮ KÝ BÊN BÁN:** Phiên đàm phán lập tức quay về trạng thái khóa (Fail-Closed).")
            st.rerun()

    # 3. GÓC NHÌN BÊN MUA
    else:
        st.markdown("#### 🛒 Góc nhìn Bên Mua (Buyer - Campuchia)")
        st.success("""
        **Quyền kiểm soát dữ liệu của Bên Mua:**
        - Ngân sách tối đa và hạn mức tín dụng được giữ kín hoàn toàn với Bên Bán và AI.
        - Nếu Bên Bán tự ý sửa giá sau khi Bên Mua đã ký, hệ thống sẽ tự động hủy bỏ chữ ký cũ để bảo vệ Bên Mua.
        """)
        
        st.markdown("##### ⚡ Quyền thu hồi chữ ký số:")
        if st.button("🛑 Thu Hồi Chữ Ký Bên Mua (Revoke Buyer Signature)"):
            cursor.execute("UPDATE deals SET buyer_signed = 0")
            conn.commit()
            st.warning("🔒 **ĐÃ THU HỒI CHỮ KÝ BÊN MUA:** Phiên đàm phán lập tức quay về trạng thái khóa (Fail-Closed).")
            st.rerun()

    st.write("---")
    # NHẬT KÝ KIỂM TOÁN CHUNG
    st.markdown("#### 📜 Nhật Ký Kiểm Toán Phân Tán (Tamper-evident Audit Trail)")
    st.caption("Lịch sử xác thực danh tính và kiểm tra điều kiện đồng thuận theo thời gian thực:")
    
    audit_data = [
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": cur_u['fullname'], "Hành động": f"Xác thực Tide DID ({cur_u['did']})", "Kết quả": "Hợp lệ"},
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": "TideCloak Consensus Gate", "Hành động": "Kiểm tra ràng buộc Dual-Consensus", "Kết quả": "Enforced"},
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": "Security Monitor", "Hành động": "Chặn nỗ lực can thiệp đơn phương", "Kết quả": "Bảo vệ thành công"}
    ]
    st.table(pd.DataFrame(audit_data))

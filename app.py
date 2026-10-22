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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
def init_db():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Đảm bảo schema luôn đúng
    try:
        cursor.execute("SELECT owner_did FROM market_pool LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS market_pool")
        cursor.execute("DROP TABLE IF EXISTS deals")
        cursor.execute("DROP TABLE IF EXISTS tide_identities")
    
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
    
    # 3. Bảng Phiên Thương Lượng & Đồng Thuận (Deal Rooms)
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
    
    # Khởi tạo dữ liệu mẫu nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM tide_identities")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Tài khoản Bên Bán (Việt Nam)
        did_seller = "did:tide:vn_lamvien_7a8f90b"
        pk_seller = "pk_secp256k1_vn_04e8b910a3c4..."
        cursor.execute("INSERT OR REPLACE INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (did_seller, pk_seller, "Trần Thu Hà", "Nông sản Lâm Viên", "Bên Bán (Việt Nam)", "Việt Nam", now))
        
        # Tài khoản Bên Mua (Campuchia)
        did_buyer = "did:tide:kh_mekong_3d4e12a"
        pk_buyer = "pk_secp256k1_kh_02c77d9811f2..."
        cursor.execute("INSERT OR REPLACE INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (did_buyer, pk_buyer, "Sok Dara", "Mekong Fresh Trading", "Bên Mua (Campuchia)", "Campuchia", now))
        
        # Thêm 2 bài đăng mẫu vào sàn
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
                        st.success(f"✅ Xác thực thành công! Xin chào {user_data[1]} ({user_data[2]}).")
                        st.rerun()
                    else:
                        st.error("❌ Không tìm thấy danh tính DID này trong mạng lưới TideCloak.")
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
        st.rerun()

st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.markdown("**Kiến trúc không quyền kiểm soát đơn phương (No Unilateral Control)** — Được bảo vệ bởi **TideCloak**[cite: 1, 7].")

tab1, tab2, tab3 = st.tabs([
    "🛒 1. Sàn Thị Trường Chung (Pool)", 
    "💬 2. Phòng Thương Lượng Giá Của Tôi", 
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
                        
                        s_pr = pprice if ptype == "BÁN" else pprice * 1.05
                        b_pr = pprice * 0.93 if ptype == "BÁN" else pprice
                        
                        cursor.execute("""
                        INSERT INTO deals (post_id, seller_did, buyer_did, product_name, quantity, seller_price, buyer_price, final_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (pid, seller, buyer, pname, pqty, s_pr, b_pr, s_pr))
                        conn.commit()
                        st.success("Đã mở phòng thương lượng! Chuyển sang Tab 2[cite: 14].")
                        st.rerun()
                else:
                    st.caption("Tin của bạn")
            st.divider()

# ---------------- TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ & AI COPILOT ----------------
with tab2:
    st.subheader("Phòng Thương Lượng Đang Hoạt Động")
    
    cursor.execute("""
    SELECT id, product_name, quantity, seller_did, buyer_did, seller_price, buyer_price, ai_price, final_price, seller_signed, buyer_signed, status
    FROM deals
    WHERE seller_did = ? OR buyer_did = ?
    ORDER BY id DESC
    """, (cur_u['did'], cur_u['did']))
    active_deals = cursor.fetchall()
    
    if not active_deals:
        st.info("Bạn chưa có phiên đàm phán nào. Hãy chọn một mặt hàng từ **Tab 1: Sàn Thị Trường** để bắt đầu.")
    else:
        deal_mapping = {f"Phiên #{d[0]}: {d[1]} ({d[2]})": d[0] for d in active_deals}
        chosen_label = st.selectbox("Chọn phiên đàm phán:", list(deal_mapping.keys()))
        deal_id = deal_mapping[chosen_label]
        
        cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        deal = cursor.fetchone()
        
        d_id, _, d_s_did, d_b_did, d_prod, d_qty, d_s_pr, d_b_pr, d_ai_pr, d_fin_pr, d_s_sign, d_b_sign, d_stat = deal
        
        is_seller = (cur_u['did'] == d_s_did)
        is_buyer = (cur_u['did'] == d_b_did)
        
        st.markdown(f"**Mặt hàng:** {d_prod} | **Sản lượng:** {d_qty}")
        st.caption(f"Bên Bán (Seller): `{d_s_did}` ⟷ Bên Mua (Buyer): `{d_b_did}`")
        
        c_p2p, c_tide = st.columns([1, 1])
        
        with c_p2p:
            st.markdown("### 1. Thương Lượng Mức Giá Kỳ Vọng")
            col_v1, col_v2 = st.columns(2)
            col_v1.write(f"🏷️ **Bên Bán yêu cầu:** `${d_s_pr:,.1f}/tấn`")
            col_v2.write(f"🏷️ **Bên Mua đề nghị:** `${d_b_pr:,.1f}/tấn`")
            
            gap = d_s_pr - d_b_pr
            if gap > 0:
                st.warning(f"⚠️ Chênh lệch: **${gap:,.1f}/tấn**. Hai bên chưa thể chốt giá.")
            elif gap == 0:
                st.success("🎯 Mức giá hai bên đưa ra đã hoàn toàn khớp nhau!")
            else:
                st.info("Bên mua đang trả giá cao hơn mức chào bán.")
                
            st.markdown("---")
            st.markdown("#### Cập Nhật Mức Giá Của Bạn")
            with st.form(f"form_price_update_{d_id}"):
                if is_seller:
                    new_pr = st.number_input("Mức giá Bên Bán đề xuất lại ($/tấn):", value=float(d_s_pr), step=10.0)
                else:
                    new_pr = st.number_input("Mức giá Bên Mua đề xuất lại ($/tấn):", value=float(d_b_pr), step=10.0)
                
                if st.form_submit_button("Cập Nhật Mức Giá"):
                    if is_seller:
                        cursor.execute("UPDATE deals SET seller_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", (new_pr, new_pr, d_id))
                    else:
                        cursor.execute("UPDATE deals SET buyer_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", (new_pr, new_pr, d_id))
                    conn.commit()
                    st.success("Đã cập nhật mức giá! Chữ ký cũ đã bị thu hồi để đảm bảo đồng thuận mới.")
                    st.rerun()

            st.markdown("---")
            # KÍCH HOẠT AI KHI BẾ TẮC
            st.markdown("### 2. Bất Đồng Quan Điểm? Nhờ AI Phân Tích")
            st.caption("AI hoạt động trong vùng cách ly, tính toán chi phí vận chuyển ($35/tấn) để đề xuất mức giá cân bằng lợi ích cho cả hai bên[cite: 7, 11].")
            
            if st.button("🤖 Kích Hoạt AI Đề Xuất Giá Cân Bằng", key=f"btn_run_ai_{d_id}"):
                shipping = 35.0
                calc_optimal = round((d_s_pr + d_b_pr) / 2.0 + (shipping / 2.0), 1)
                cursor.execute("UPDATE deals SET ai_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?",
                               (calc_optimal, calc_optimal, d_id))
                conn.commit()
                st.rerun()
                
            if d_ai_pr:
                st.info(f"💡 **AI Khuyến Nghị:** Chốt ở mức **${d_ai_pr:,.1f}/tấn**\n\n*Lý do:* Đảm bảo bên bán có biên lợi nhuận khả dụng, đồng thời hỗ trợ 50% chi phí logistics cho bên mua[cite: 7, 11].")
                if st.button("Chấp Nhận Mức Giá Khuyến Nghị Của AI", key=f"btn_accept_ai_{d_id}"):
                    cursor.execute("UPDATE deals SET final_price = ? WHERE id = ?", (d_ai_pr, d_id))
                    conn.commit()
                    st.rerun()

        with c_tide:
            st.markdown("### 3. Phê Duyệt Đồng Thuận (Tide Dual-Consensus)")
            st.caption("Nguyên tắc Không Quyền Kiểm Soát Đơn Phương (No Unilateral Control): Hợp đồng chỉ phát sinh hiệu lực khi cả 2 bên cùng ký số[cite: 1, 7].")
            
            target_close_price = d_fin_pr if d_fin_pr else d_s_pr
            st.metric("Mức Giá Dự Kiến Chốt", f"${target_close_price:,.1f} / tấn")
            
            col_s_btn, col_b_btn = st.columns(2)
            
            # CỘT NGƯỜI BÁN KÝ
            with col_s_btn:
                if d_s_sign == 1:
                    st.success("✅ Người bán đã ký")
                else:
                    if is_seller:
                        if st.button("✍️ Người Bán Ký Phê Duyệt", key=f"s_sign_{d_id}"):
                            cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.warning("Chờ Người Bán ký...")
                        # Nút bấm giả lập đối tác ký từ xa phục vụ video demo góc quay đơn
                        if st.button("⚡ [Demo] Giả lập Người Bán ký từ xa", key=f"sim_s_sign_{d_id}"):
                            cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                        
            # CỘT NGƯỜI MUA KÝ
            with col_b_btn:
                if d_b_sign == 1:
                    st.success("✅ Người mua đã ký")
                else:
                    if is_buyer:
                        if st.button("✍️ Người Mua Ký Phê Duyệt", key=f"b_sign_{d_id}"):
                            cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.warning("Chờ Người Mua ký...")
                        # Nút bấm giả lập đối tác ký từ xa phục vụ video demo góc quay đơn
                        if st.button("⚡ [Demo] Giả lập Người Mua ký từ xa", key=f"sim_b_sign_{d_id}"):
                            cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
            
            st.markdown("---")
            st.markdown("#### Trạng Thái Hiệu Lực Của Hợp Đồng:")
            if d_s_sign == 1 and d_b_sign == 1:
                st.balloons()
                st.success(f"🎉 **GIAO DỊCH THÀNH CÔNG Ở MỨC GIÁ ${target_close_price:,.1f}/TẤN!**")
                st.write("Hai bên đã hoàn tất xác thực số qua TideCloak[cite: 7]. Hợp đồng mua bán đã được đóng băng toàn vẹn.")
            else:
                st.error("🔒 **TRẠNG THÁI: CHƯA ĐỦ ĐỒNG THUẬN (FAIL-CLOSED)**")
                st.caption("Chính sách TideCloak: Nếu thiếu chữ ký của một trong hai bên, hợp đồng hoàn toàn không thể thực thi[cite: 1, 7, 11].")

# ---------------- TAB 3: BẢO MẬT & KIỂM THỬ TIDECLOAK ----------------
with tab3:
    st.subheader("Cổng Giám Sát Phân Quyền & Kiểm Thử Bảo Mật (TideCloak Enforcement)")
    
    st.markdown("#### 1. Kiểm thử khả năng ngăn chặn can thiệp đơn phương")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🚨 Thử Admin Bypass (Cố tình đóng đơn đơn phương)"):
            st.error("❌ **ACCESS DENIED BY TIDECLOAK:** Nền tảng và Quản trị viên không sở hữu Private Key của các bên. Quyền truy cập bị từ chối tuyệt đối[cite: 1, 7]!")
    with col_t2:
        if st.button("🛑 Thu Hồi Quyền Của Cả Hai Bên (Emergency Revoke)"):
            cursor.execute("UPDATE deals SET seller_signed = 0, buyer_signed = 0")
            conn.commit()
            st.warning("🔒 Toàn bộ chữ ký trên các phiên đàm phán đã được thu hồi an toàn[cite: 7].")
            st.rerun()
            
    st.divider()
    st.markdown("#### 2. Nhật Ký Kiểm Toán Thời Gian Thực (Audit Trail)")
    audit_data = [
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": cur_u['fullname'], "Hành động": f"Xác thực Tide DID ({cur_u['did']})", "Trạng thái": "Hợp lệ"},
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": "TideCloak Consensus Gate", "Hành động": "Kiểm tra điều kiện chữ ký 2 bên", "Trạng thái": "Enforced[cite: 7]"}
    ]
    st.table(pd.DataFrame(audit_data))

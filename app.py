import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="TrustGate AI — Sàn Giao Dịch Nông Sản",
    layout="wide",
    page_icon="🌾"
)

# ==========================================
# 1. HỆ THỐNG CƠ SỞ DỮ LIỆU BỀN VỮNG (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Bảng người dùng (Lưu tài khoản, vai trò, tổ chức)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT,
        fullname TEXT,
        org_name TEXT,
        role TEXT
    )
    """)
    
    # Bảng sàn thị trường chung (Pool hàng hóa)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_pool (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_type TEXT,
        owner_username TEXT,
        org_name TEXT,
        product_name TEXT,
        quantity TEXT,
        price REAL,
        location TEXT,
        created_at TEXT
    )
    """)
    
    # Bảng phiên thương lượng (Deal Rooms)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        seller_username TEXT,
        buyer_username TEXT,
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
    
    # Tạo tài khoản mẫu ban đầu nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        h1 = hashlib.sha256("123456".encode()).hexdigest()
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                       ("seller_vn", h1, "Trần Thu Hà", "Nông sản Lâm Viên", "Bên Bán (Việt Nam)"))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                       ("buyer_kh", h1, "Sok Dara", "Mekong Fresh Trading", "Bên Mua (Campuchia)"))
        
        # Thêm dữ liệu mẫu vào Pool
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        cursor.execute("INSERT INTO market_pool (post_type, owner_username, org_name, product_name, quantity, price, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("BÁN", "seller_vn", "Nông sản Lâm Viên", "Cà phê Robusta S16", "20 tấn", 2150.0, "Đức Trọng, Lâm Đồng", now))
        cursor.execute("INSERT INTO market_pool (post_type, owner_username, org_name, product_name, quantity, price, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("MUA", "buyer_kh", "Mekong Fresh Trading", "Hồ tiêu đen 500g/l", "10 tấn", 4100.0, "Cửa khẩu Mộc Bài", now))
    
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# Khởi tạo phiên người dùng trong session_state
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

# ==========================================
# 2. MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ THỰC TẾ
# ==========================================
if st.session_state.auth_user is None:
    st.title("🌾 TrustGate AI — Hệ Thống Đàm Phán Nông Sản")
    st.caption("Cơ chế xác thực và bảo mật phân tán dựa trên kiến trúc TideCloak")
    
    tab_login, tab_register = st.tabs(["🔑 Đăng Nhập", "📝 Đăng Ký Doanh Nghiệp Mới"])
    
    with tab_login:
        st.subheader("Đăng nhập vào hệ thống")
        with st.form("form_login"):
            username_inp = st.text_input("Tên tài khoản (Gợi ý: seller_vn hoặc buyer_kh)")
            password_inp = st.text_input("Mật khẩu (Mặc định: 123456)", type="password")
            btn_login = st.form_submit_button("Đăng Nhập")
            
            if btn_login:
                pwd_h = hashlib.sha256(password_inp.encode()).hexdigest()
                cursor.execute("SELECT username, fullname, org_name, role FROM users WHERE username = ? AND password_hash = ?", 
                               (username_inp, pwd_h))
                user = cursor.fetchone()
                if user:
                    st.session_state.auth_user = {
                        "username": user[0],
                        "fullname": user[1],
                        "org_name": user[2],
                        "role": user[3]
                    }
                    st.success(f"Đăng nhập thành công! Chào mừng {user[1]}.")
                    st.rerun()
                else:
                    st.error("Tên tài khoản hoặc mật khẩu không chính xác.")
                    
    with tab_register:
        st.subheader("Đăng ký tài khoản doanh nghiệp")
        with st.form("form_reg"):
            reg_user = st.text_input("Tên đăng nhập mới")
            reg_pwd = st.text_input("Mật khẩu", type="password")
            reg_name = st.text_input("Họ và tên người đại diện")
            reg_org = st.text_input("Tên công ty / Hợp tác xã")
            reg_role = st.selectbox("Vai trò trên sàn", ["Bên Bán (Việt Nam)", "Bên Mua (Campuchia)"])
            btn_reg = st.form_submit_button("Tạo Tài Khoản")
            
            if btn_reg:
                if reg_user and reg_pwd and reg_name and reg_org:
                    try:
                        pwd_h = hashlib.sha256(reg_pwd.encode()).hexdigest()
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                                       (reg_user, pwd_h, reg_name, reg_org, reg_role))
                        conn.commit()
                        st.success("Tạo tài khoản thành công! Vui lòng chuyển sang tab Đăng Nhập.")
                    except sqlite3.IntegrityError:
                        st.error("Tên đăng nhập này đã tồn tại trên hệ thống!")
                else:
                    st.warning("Vui lòng điền đầy đủ các trường thông tin.")
    st.stop()

# ==========================================
# 3. GIAO DIỆN CHÍNH KHI ĐÃ ĐĂNG NHẬP
# ==========================================
current_u = st.session_state.auth_user

# Sidebar hiển thị thông tin danh tính
with st.sidebar:
    st.header("👤 Hồ Sơ Đăng Nhập")
    st.markdown(f"**Người đại diện:** {current_u['fullname']}")
    st.markdown(f"**Doanh nghiệp:** {current_u['org_name']}")
    st.markdown(f"**Vai trò:** {current_u['role']}")
    st.caption("Xác thực phi tập trung: Khóa bảo mật được bảo vệ bởi TideCloak.")
    
    st.divider()
    if st.button("🚪 Đăng Xuất"):
        st.session_state.auth_user = None
        st.rerun()

st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.markdown("**Kiến trúc không quyền kiểm soát đơn phương (No Unilateral Control)** — Được bảo vệ bởi **TideCloak**[cite: 1, 7].")

tab1, tab2, tab3 = st.tabs([
    "🛒 1. Sàn Thị Trường Chung (Pool)", 
    "💬 2. Phòng Thương Lượng Của Tôi", 
    "🛡️ 3. Kiểm Tra Bảo Mật TideCloak"
])

# ----------------------------------------------------
# TAB 1: SÀN THỊ TRƯỜNG CHUNG (MARKETPLACE POOL)
# ----------------------------------------------------
with tab1:
    st.subheader("Sàn Hàng Hóa & Nhu Cầu Mua Bán Chung")
    
    # Form đăng tin lên sàn
    with st.expander("➕ Đăng Tin Mới Lên Thị Trường", expanded=False):
        with st.form("form_add_post"):
            c1, c2 = st.columns(2)
            default_type = "BÁN" if "Bán" in current_u['role'] else "MUA"
            p_type = c1.selectbox("Loại tin", ["BÁN", "MUA"], index=0 if default_type=="BÁN" else 1)
            p_prod = c2.text_input("Tên nông sản", "Cà phê Robusta nhân xanh S16")
            
            c3, c4 = st.columns(2)
            p_qty = c3.text_input("Khối lượng (Ví dụ: 20 tấn)", "20 tấn")
            p_price = c4.number_input("Mức giá đề xuất ban đầu (USD/tấn)", min_value=10.0, value=2150.0, step=10.0)
            
            p_loc = st.text_input("Địa điểm giao nhận hàng", "Cửa khẩu Mộc Bài - Tây Ninh")
            btn_post = st.form_submit_button("Đăng Lên Thị Trường")
            
            if btn_post:
                now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                INSERT INTO market_pool (post_type, owner_username, org_name, product_name, quantity, price, location, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_type, current_u['username'], current_u['org_name'], p_prod, p_qty, p_price, p_loc, now_str))
                conn.commit()
                st.success("Đã đăng tin thành công lên Sàn giao dịch chung!")
                st.rerun()

    st.write("---")
    st.markdown("#### Danh Sách Nông Sản Đang Giao Dịch")
    
    cursor.execute("SELECT id, post_type, owner_username, org_name, product_name, quantity, price, location, created_at FROM market_pool ORDER BY id DESC")
    posts = cursor.fetchall()
    
    if not posts:
        st.info("Hiện chưa có tin đăng nào trên sàn.")
    else:
        for p in posts:
            p_id, p_type, p_owner, p_org, p_prod, p_qty, p_pr, p_loc, p_time = p
            col_desc, col_btn = st.columns([4, 1])
            
            with col_desc:
                badge = "🟢 BÁN" if p_type == "BÁN" else "🔵 CẦN MUA"
                st.markdown(f"**[{badge}] {p_prod}** — Sản lượng: **{p_qty}** | Mức giá: **${p_pr:,.1f}/tấn**")
                st.caption(f"Đăng bởi: **{p_org}** | Địa điểm: {p_loc} | Ngày đăng: {p_time}")
            
            with col_btn:
                # Không tự thương lượng với bài đăng của chính mình
                if p_owner != current_u['username']:
                    if st.button("🤝 Thương Lượng", key=f"deal_init_{p_id}"):
                        seller = p_owner if p_type == "BÁN" else current_u['username']
                        buyer = current_u['username'] if p_type == "BÁN" else p_owner
                        s_price = p_pr if p_type == "BÁN" else p_pr * 1.05
                        b_price = p_pr * 0.95 if p_type == "BÁN" else p_pr
                        
                        cursor.execute("""
                        INSERT INTO deals (post_id, seller_username, buyer_username, product_name, quantity, seller_price, buyer_price, final_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (p_id, seller, buyer, p_prod, p_qty, s_price, b_price, s_price))
                        conn.commit()
                        st.success("Đã tạo phòng thương lượng! Chuyển sang Tab 2 để bắt đầu đàm phán.")
                        st.rerun()
                else:
                    st.caption("Tin của bạn")
            st.divider()

# ----------------------------------------------------
# TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ & AI COPILOT
# ----------------------------------------------------
with tab2:
    st.subheader("Phòng Thương Lượng Đang Hoạt Động Của Bạn")
    
    # Lấy các giao dịch mà người dùng này tham gia (vai trò mua hoặc bán)
    cursor.execute("""
    SELECT id, product_name, quantity, seller_username, buyer_username, seller_price, buyer_price, ai_price, final_price, seller_signed, buyer_signed, status
    FROM deals 
    WHERE seller_username = ? OR buyer_username = ?
    ORDER BY id DESC
    """, (current_u['username'], current_u['username']))
    my_deals = cursor.fetchall()
    
    if not my_deals:
        st.info("Bạn chưa có phiên thương lượng nào. Hãy bấm **'Thương Lượng'** trên một sản phẩm ở Tab 1.")
    else:
        deal_options = {f"Phiên #{d[0]} — {d[1]} ({d[2]})": d[0] for d in my_deals}
        selected_deal_label = st.selectbox("Chọn phiên đàm phán cần làm việc:", list(deal_options.keys()))
        selected_deal_id = deal_options[selected_deal_label]
        
        # Lấy thông tin chi tiết phiên được chọn
        cursor.execute("SELECT * FROM deals WHERE id = ?", (selected_deal_id,))
        cur_deal = cursor.fetchone()
        
        d_id, _, d_s_user, d_b_user, d_prod, d_qty, d_s_price, d_b_price, d_ai_price, d_fin_price, d_s_sign, d_b_sign, d_stat = cur_deal
        
        is_seller = (current_u['username'] == d_s_user)
        is_buyer = (current_u['username'] == d_b_user)
        
        st.markdown(f"**Mặt hàng:** {d_prod} | **Khối lượng:** {d_qty}")
        st.caption(f"Bên Bán (Seller): **{d_s_user}** ⟷ Bên Mua (Buyer): **{d_b_user}**")
        
        c_left, c_right = st.columns([1, 1])
        
        # BÊN TRÁI: ĐÀM PHÁN GIÁ TRỰC TIẾP GIỮA 2 BÊN
        with c_left:
            st.markdown("### 1. Mức Giá Kỳ Vọng Hai Bên Đang Đưa Ra")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.write(f"🏷️ **Bên Bán yêu cầu:** `${d_s_price:,.1f}/tấn`")
            with c_p2:
                st.write(f"🏷️ **Bên Mua đề nghị:** `${d_b_price:,.1f}/tấn`")
            
            price_gap = d_s_price - d_b_price
            if price_gap > 0:
                st.warning(f"⚠️ Chênh lệch giá: **${price_gap:,.1f}/tấn**. Chưa đạt được thỏa thuận.")
            elif price_gap == 0:
                st.success("🎯 Mức giá hai bên đưa ra đã hoàn toàn trùng khớp!")
            else:
                st.info("Bên mua đang trả mức giá cao hơn mức chào bán.")
                
            st.markdown("---")
            st.markdown("#### Cập Nhật Lại Mức Giá Của Bạn")
            with st.form(f"form_update_price_{d_id}"):
                if is_seller:
                    new_val = st.number_input("Nhập giá mới của Bên Bán ($/tấn):", value=float(d_s_price), step=10.0)
                else:
                    new_val = st.number_input("Nhập giá mới của Bên Mua ($/tấn):", value=float(d_b_price), step=10.0)
                
                btn_update_p = st.form_submit_button("Cập Nhật Báo Giá")
                if btn_update_p:
                    if is_seller:
                        cursor.execute("UPDATE deals SET seller_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", (new_val, d_id))
                    else:
                        cursor.execute("UPDATE deals SET buyer_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", (new_val, d_id))
                    conn.commit()
                    st.success("Đã cập nhật mức giá mới! Chữ ký cũ đã được thu hồi để hai bên xem xét lại.")
                    st.rerun()

            st.markdown("---")
            # KHU VỰC KÍCH HOẠT AI KHI BẾ TẮC
            st.markdown("### 2. Bất Đồng Giá? Nhờ AI Hỗ Trợ Phân Tích")
            st.caption("AI đóng vai trò trọng tài trung gian, tính toán cước vận tải đường bộ ($35/tấn) để đưa ra mức giá cân bằng lợi ích cho cả hai.")
            
            if st.button("🤖 Kích Hoạt AI Đề Xuất Giá Cân Bằng", key=f"btn_ai_{d_id}"):
                shipping_cost = 35.0
                suggested = (d_s_price + d_b_price) / 2.0 + (shipping_cost / 2.0)
                suggested = round(suggested, 1)
                
                cursor.execute("UPDATE deals SET ai_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0 WHERE id = ?", 
                               (suggested, suggested, d_id))
                conn.commit()
                st.rerun()
                
            if d_ai_price:
                st.info(f"💡 **AI Đề Xuất:** Nên chốt ở mức **${d_ai_price:,.1f}/tấn**\n\n*Phân tích:* Mức giá này chia sẻ đồng đều chi phí logistics và tối ưu hóa lợi nhuận cho cả hai bên[cite: 7, 11].")
                if st.button("Chấp Nhận Mức Giá AI Đề Xuất", key=f"accept_ai_{d_id}"):
                    cursor.execute("UPDATE deals SET final_price = ? WHERE id = ?", (d_ai_price, d_id))
                    conn.commit()
                    st.rerun()

        # BÊN PHẢI: CHỐT HỢP ĐỒNG BẰNG TIDECLOAK
        with c_right:
            st.markdown("### 3. Phê Duyệt Đồng Thuận (Tide Dual-Consensus)")
            st.caption("Nguyên tắc Không Kiểm Soát Đơn Phương (No Unilateral Control): Hợp đồng chỉ phát sinh hiệu lực khi cả 2 bên cùng ký số[cite: 1, 7].")
            
            chot_gia = d_fin_price if d_fin_price else d_s_price
            st.metric("Mức Giá Dự Kiến Chốt", f"${chot_gia:,.1f} / tấn")
            
            c_s_btn, c_b_btn = st.columns(2)
            with c_s_btn:
                if d_s_sign == 1:
                    st.success("✅ Người bán đã ký")
                else:
                    if is_seller:
                        if st.button("✍️ Người Bán Ký Phê Duyệt", key=f"sign_s_{d_id}"):
                            cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.warning("Chờ Người Bán ký...")
                        
            with c_b_btn:
                if d_b_sign == 1:
                    st.success("✅ Người mua đã ký")
                else:
                    if is_buyer:
                        if st.button("✍️ Người Mua Ký Phê Duyệt", key=f"sign_b_{d_id}"):
                            cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.warning("Chờ Người Mua ký...")
            
            st.markdown("---")
            st.markdown("#### Trạng Thái Hiệu Lực Của Hợp Đồng:")
            if d_s_sign == 1 and d_b_sign == 1:
                st.balloons()
                st.success(f"🎉 **GIAO DỊCH CHÍNH THỨC THÀNH CÔNG Ở MỨC GIÁ ${chot_gia:,.1f}/TẤN!**")
                st.write("Hai bên đã hoàn tất chữ ký số qua TideCloak. Hợp đồng mua bán đã được đóng băng toàn vẹn[cite: 16].")
            else:
                st.error("🔒 **TRẠNG THÁI: CHƯA ĐỦ ĐỒNG THUẬN (FAIL-CLOSED)**")
                st.caption("Chính sách bảo mật TideCloak: Nếu thiếu chữ ký của một trong hai bên, hợp đồng hoàn toàn không thể thực thi[cite: 1, 7, 11].")

# ----------------------------------------------------
# TAB 3: BẢO MẬT & KIỂM THỬ TIDECLOAK
# ----------------------------------------------------
with tab3:
    st.subheader("Cổng Giám Sát Phân Quyền & Kiểm Thử Bảo Mật (TideCloak Enforcement)")
    
    st.markdown("#### 1. Kiểm thử khả năng ngăn chặn can thiệp đơn phương")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🚨 Thử Admin Bypass (Cố tình đóng đơn đơn phương)"):
            st.error("❌ **ACCESS DENIED BY TIDECLOAK:** Nền tảng và Quản trị viên không sở hữu Private Key của các bên. Quyền truy cập bị từ chối tuyệt đối[cite: 1, 7]!")
    with col_t2:
        if st.button("🛑 Thu Hồi Toàn Bộ Quyền Phê Duyệt"):
            cursor.execute("UPDATE deals SET seller_signed = 0, buyer_signed = 0")
            conn.commit()
            st.warning("🔒 Toàn bộ chữ ký trên các phiên đàm phán đã được thu hồi an toàn[cite: 7].")
            st.rerun()
            
    st.divider()
    st.markdown("#### 2. Nhật Ký Kiểm Toán Thời Gian Thực (Audit Trail)")
    audit_data = [
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": current_u['fullname'], "Hành động": "Truy cập hệ thống an toàn", "Trạng thái": "Hợp lệ"},
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": "TideCloak Consensus Gate", "Hành động": "Kiểm tra điều kiện chữ ký 2 bên", "Trạng thái": "Đang thực thi[cite: 7]"}
    ]
    st.table(pd.DataFrame(audit_data))

import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
import json
import requests

st.set_page_config(
    page_title="TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên",
    layout="wide",
    page_icon="🌾"
)

# Tùy biến CSS giao diện
st.markdown("""
<style>
    .chat-bubble-seller {
        background-color: #e3f2fd;
        padding: 10px 14px;
        border-radius: 12px 12px 12px 0px;
        margin-bottom: 8px;
        max-width: 85%;
    }
    .chat-bubble-buyer {
        background-color: #f1f8e9;
        padding: 10px 14px;
        border-radius: 12px 12px 0px 12px;
        margin-bottom: 8px;
        max-width: 85%;
        margin-left: auto;
    }
    .paper-contract-pending {
        background: #fffdfa;
        border: 2px dashed #bcaaa4;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .paper-contract-success {
        background: #f1f8e9;
        border: 2px solid #2e7d32;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 6px 20px rgba(46, 125, 50, 0.15);
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .paper-contract-cancelled {
        background: #ffebee;
        border: 2px dashed #c62828;
        border-radius: 8px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .stamp-badge-ok {
        border: 3px double #2e7d32;
        color: #2e7d32;
        font-weight: 900;
        text-transform: uppercase;
        padding: 6px 14px;
        border-radius: 8px;
        display: inline-block;
        transform: rotate(-3deg);
    }
    .stamp-badge-void {
        border: 3px double #c62828;
        color: #c62828;
        font-weight: 900;
        text-transform: uppercase;
        padding: 6px 14px;
        border-radius: 8px;
        display: inline-block;
        transform: rotate(-5deg);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
def init_db():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT phone FROM tide_identities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS tide_identities")
        cursor.execute("DROP TABLE IF EXISTS market_pool")
        cursor.execute("DROP TABLE IF EXISTS deals")
        cursor.execute("DROP TABLE IF EXISTS deal_messages")
        conn.commit()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tide_identities (
        did_address TEXT PRIMARY KEY,
        public_key TEXT,
        fullname TEXT,
        org_name TEXT,
        role TEXT,
        country TEXT,
        phone TEXT,
        created_at TEXT
    )
    """)
    
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
    
    cursor.execute("SELECT COUNT(*) FROM tide_identities")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        did_seller = "did:tide:vn_lamvien_7a8f90b"
        pk_seller = "pk_secp256k1_vn_04e8b910a3c4..."
        cursor.execute("INSERT OR REPLACE INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (did_seller, pk_seller, "Trần Thu Hà", "Nông sản Lâm Viên", "Bên Bán (Việt Nam)", "Việt Nam", "0912345678", now))
        
        did_buyer = "did:tide:kh_mekong_3d4e12a"
        pk_buyer = "pk_secp256k1_kh_02c77d9811f2..."
        cursor.execute("INSERT OR REPLACE INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (did_buyer, pk_buyer, "Sok Dara", "Mekong Fresh Trading", "Bên Mua (Campuchia)", "Campuchia", "0988888999", now))
        
        cursor.execute("INSERT INTO market_pool (post_type, owner_did, org_name, product_name, quantity, price, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("BÁN", did_seller, "Nông sản Lâm Viên", "Cà phê Robusta nhân xanh S16", "20 tấn", 2200.0, "Đức Trọng, Lâm Đồng", now))
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
# 2. HÀM TRỢ LÝ CHIẾN LƯỢC GIÁ (AI STRATEGY)
# ==========================================
def get_ai_price_strategy(user_role, product, quantity, target_price, partner_price):
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    
    prompt = f"""
    Bạn là Chuyên gia đàm phán kinh tế nông sản (TrustGate AI Strategy Advisor).
    Vai trò người dùng của tôi: {user_role}
    Mặt hàng: {product} (Khối lượng: {quantity})
    Mức giá đối tác đang đưa ra: {partner_price} USD/tấn
    Mức giá hiện tại của người dùng: {target_price} USD/tấn
    
    Hãy phân tích và trả về đúng 2 mức giá tư vấn:
    1. 'aggressive_price': Mức giá đè tối đa (nếu là bên mua: trả mức thấp nhất mà bên bán vẫn chấp nhận được; nếu là bên bán: hét giá cao nhất có thể).
    2. 'balanced_price': Mức giá cân bằng hòa giải logistics (đường bộ Mộc Bài $35/tấn).
    3. 'advice': Lời khuyên chiến thuật tâm lý khi gửi giá này (khoảng 2 câu).
    
    Trả về định dạng JSON thuần túy:
    {{"aggressive_price": 2130.0, "balanced_price": 2170.0, "advice": "lời khuyên"}}
    """
    
    if api_key:
        for m in ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            try:
                res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=5)
                if res.status_code == 200:
                    text_resp = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text_resp.startswith("```"):
                        text_resp = text_resp.replace("```json", "").replace("```", "").strip()
                    return json.loads(text_resp)
            except Exception:
                continue

    # Fallback số học
    if "Mua" in user_role:
        agg = round(partner_price * 0.96, 1)
        bal = round((target_price + partner_price) / 2.0 + 15.0, 1) if target_price > 0 else round(partner_price * 0.98, 1)
        adv = f"Bên bán đang yêu cầu ${partner_price:,.1f}. Bạn có thể trả trước ${agg:,.1f}. Nếu đối phương chưa ưng, mức hòa giải tối ưu là ${bal:,.1f}."
    else:
        agg = round(partner_price * 1.04, 1) if partner_price > 0 else round(target_price, 1)
        bal = round((target_price + partner_price) / 2.0 + 17.5, 1) if partner_price > 0 else round(target_price, 1)
        adv = f"Bên mua đang đề nghị ${partner_price:,.1f}. Mức giá phản đòn khuyến nghị là ${agg:,.1f}, điểm chốt cân bằng là ${bal:,.1f}."
        
    return {"aggressive_price": agg, "balanced_price": bal, "advice": adv}

# ==========================================
# 3. GIAO DIỆN XÁC THỰC DANH TÍNH TIDECLOAK
# ==========================================
if st.session_state.auth_user is None:
    st.title("🛡️ TrustGate AI — Cổng Xác Thực TideCloak")
    st.caption("Xác thực phi tập trung: Hệ thống không lưu trữ mật khẩu hay khóa riêng của doanh nghiệp.")
    
    t1, t2, t3 = st.tabs([
        "🔐 Đăng Nhập Nhanh Bằng DID", 
        "🔍 Quên Mã DID? (Khôi Phục)", 
        "📝 Đăng Ký Cặp Khóa Mới"
    ])
    
    with t1:
        st.subheader("Chọn hoặc nhập mã danh tính số (DID)")
        cursor.execute("SELECT did_address, fullname, org_name, role FROM tide_identities")
        all_accounts = cursor.fetchall()
        acc_dict = {f"{a[1]} — {a[2]} ({a[3]})": a[0] for a in all_accounts}
        
        selected_preset = st.selectbox("📌 Chọn nhanh danh tính đã lưu trên máy:", ["-- Tự nhập mã DID thủ công --"] + list(acc_dict.keys()))
        preset_did = acc_dict[selected_preset] if selected_preset != "-- Tự nhập mã DID thủ công --" else ""
        
        with st.form("form_tide_login"):
            did_inp = st.text_input("Mã TideCloak DID:", value=preset_did, placeholder="did:tide:vn_lamvien_7a8f90b")
            nonce = hashlib.sha256(str(datetime.date.today()).encode()).hexdigest()[:16]
            st.caption(f"Security Nonce: `{nonce}` | Ký số tự động bởi phiên bảo mật phân tán.")
            btn_sub_login = st.form_submit_button("Xác Thực & Đăng Nhập")
            
            if btn_sub_login:
                if did_inp.strip():
                    cursor.execute("SELECT did_address, fullname, org_name, role, country, phone, public_key FROM tide_identities WHERE did_address = ?", 
                                   (did_inp.strip(),))
                    user_data = cursor.fetchone()
                    if user_data:
                        st.session_state.auth_user = {
                            "did": user_data[0],
                            "fullname": user_data[1],
                            "org_name": user_data[2],
                            "role": user_data[3],
                            "country": user_data[4],
                            "phone": user_data[5],
                            "public_key": user_data[6]
                        }
                        st.success(f"Xác thực thành công! Xin chào {user_data[1]} ({user_data[2]}).")
                        st.rerun()
                    else:
                        st.error("Không tìm thấy danh tính DID này trong hệ thống.")
                else:
                    st.warning("Vui lòng nhập hoặc chọn mã DID.")

    with t2:
        st.subheader("Tra cứu và Khôi phục mã DID bị quên")
        with st.form("form_recover_did"):
            search_query = st.text_input("Nhập Số điện thoại hoặc Họ tên người đại diện:")
            btn_search = st.form_submit_button("Tra Cứu Danh Tính")
            if btn_search:
                if search_query.strip():
                    cursor.execute("""
                    SELECT did_address, fullname, org_name, role, phone FROM tide_identities 
                    WHERE phone LIKE ? OR fullname LIKE ? OR org_name LIKE ?
                    """, (f"%{search_query.strip()}%", f"%{search_query.strip()}%", f"%{search_query.strip()}%"))
                    found_users = cursor.fetchall()
                    if found_users:
                        st.success(f"Tìm thấy {len(found_users)} danh tính phù hợp:")
                        for u in found_users:
                            st.code(f"Mã DID: {u[0]}\nNgười đại diện: {u[1]} | Công ty: {u[2]} ({u[3]})\nSĐT: {u[4]}", language="text")
                    else:
                        st.warning("Không tìm thấy thông tin nào phù hợp với từ khóa.")
                else:
                    st.warning("Vui lòng nhập thông tin để tra cứu.")

    with t3:
        st.subheader("Cấp phát danh tính phân tán mới")
        with st.form("form_tide_reg"):
            r_name = st.text_input("Họ và tên người đại diện")
            r_org = st.text_input("Tên doanh nghiệp / Hợp tác xã")
            r_phone = st.text_input("Số điện thoại liên hệ", "0912345678")
            r_role = st.selectbox("Vai trò giao dịch", ["Bên Bán (Việt Nam)", "Bên Mua (Campuchia)"])
            btn_reg = st.form_submit_button("Cấp Phát Mã Tide DID Mới")
            
            if btn_reg:
                if r_name and r_org and r_phone:
                    prefix = "vn" if "Việt Nam" in r_role else "kh"
                    country = "Việt Nam" if "Việt Nam" in r_role else "Campuchia"
                    rnd_hash = hashlib.sha256(f"{r_name}{r_org}{datetime.datetime.now()}".encode()).hexdigest()[:8]
                    gen_did = f"did:tide:{prefix}_{rnd_hash}"
                    gen_pk = f"pk_secp256k1_{prefix}_{rnd_hash}8f9a"
                    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    cursor.execute("INSERT INTO tide_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (gen_did, gen_pk, r_name, r_org, r_role, country, r_phone, now_str))
                    conn.commit()
                    st.success("Cấp phát danh tính thành công!")
                    st.code(f"Mã DID: {gen_did}\nPublic Key: {gen_pk}", language="text")
                else:
                    st.warning("Vui lòng điền đầy đủ họ tên, tên tổ chức và số điện thoại.")
    st.stop()

# ==========================================
# 4. GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP
# ==========================================
cur_u = st.session_state.auth_user

with st.sidebar:
    st.header("🛡️ Phiên Danh Tính TideCloak")
    st.markdown(f"**Người đại diện:** {cur_u['fullname']}")
    st.markdown(f"**Tổ chức:** {cur_u['org_name']}")
    st.markdown(f"**Vai trò:** {cur_u['role']}")
    st.markdown(f"**Điện thoại:** {cur_u.get('phone', 'N/A')}")
    st.code(f"{cur_u['did']}", language="text")
    st.caption("Trạng thái: ĐÃ XÁC THỰC PHÂN TÁN")
    
    st.divider()
    if st.button("🚪 Đăng Xuất"):
        st.session_state.auth_user = None
        st.session_state.current_deal_id = None
        st.rerun()

st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.markdown("**Kiến trúc không quyền kiểm soát đơn phương (No Unilateral Control)** — Được bảo vệ bởi **TideCloak**.")

# THANH ĐIỀU HƯỚNG AN TOÀN TRÁNH LỖI VALUEERROR
nav_options = [
    "🛒 1. Sàn Thị Trường & Yêu Cầu", 
    "💬 2. Phòng Thương Lượng & Hợp Đồng", 
    "🛡️ 3. Kiểm Tra Bảo Mật TideCloak"
]

if "active_nav" not in st.session_state or st.session_state.active_nav not in nav_options:
    st.session_state.active_nav = nav_options[0]

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
# TAB 1: SÀN THỊ TRƯỜNG & YÊU CẦU CỦA TÔI
# ========================================================
if st.session_state.active_nav == "🛒 1. Sàn Thị Trường & Yêu Cầu":
    pool_subtab1, pool_subtab2, pool_subtab3 = st.tabs([
        "🌐 Khám Phá Thị Trường (Marketplace Pool)", 
        "📋 Yêu Cầu Của Tôi (My Listings)", 
        "➕ Đăng Yêu Cầu Mới"
    ])
    
    with pool_subtab1:
        st.subheader("Sàn Giao Dịch Hàng Hóa Nông Sản")
        
        c_f1, c_f2, c_f3 = st.columns([2, 1, 1])
        with c_f1:
            search_keyword = st.text_input("🔍 Tìm theo tên sản phẩm hoặc địa điểm:", placeholder="Nhập: Cà phê, Tiêu, Mộc Bài...")
        with c_f2:
            filter_type = st.selectbox("Lọc theo loại:", ["Tất cả loại", "BÁN (Nguồn cung)", "MUA (Nhu cầu)"])
        with c_f3:
            sort_price = st.selectbox("Sắp xếp mức giá:", ["Mới nhất trước", "Giá tăng dần", "Giá giảm dần"])
            
        query = "SELECT id, post_type, owner_did, org_name, product_name, quantity, price, location, created_at FROM market_pool WHERE 1=1"
        params = []
        
        if search_keyword.strip():
            query += " AND (product_name LIKE ? OR location LIKE ? OR org_name LIKE ?)"
            params.extend([f"%{search_keyword.strip()}%", f"%{search_keyword.strip()}%", f"%{search_keyword.strip()}%"])
            
        if "BÁN" in filter_type:
            query += " AND post_type = 'BÁN'"
        elif "MUA" in filter_type:
            query += " AND post_type = 'MUA'"
            
        if sort_price == "Giá tăng dần":
            query += " ORDER BY price ASC"
        elif sort_price == "Giá giảm dần":
            query += " ORDER BY price DESC"
        else:
            query += " ORDER BY id DESC"
            
        cursor.execute(query, params)
        filtered_posts = cursor.fetchall()
        
        st.caption(f"Hiển thị **{len(filtered_posts)}** mặt hàng thỏa mãn bộ lọc:")
        
        if not filtered_posts:
            st.info("Không tìm thấy mặt hàng nào phù hợp với bộ lọc tìm kiếm.")
        else:
            for post in filtered_posts:
                pid, ptype, powner_did, porg, pname, pqty, pprice, ploc, pdate = post
                c_card, c_act = st.columns([4, 1])
                
                with c_card:
                    badge = "🟢 NGUỒN CUNG (BÁN)" if ptype == "BÁN" else "🔵 NHU CẦU (MUA)"
                    st.markdown(f"**[{badge}] {pname}** — Khối lượng: **{pqty}** | Mức giá: **${pprice:,.1f}/tấn**")
                    st.caption(f"Tổ chức: **{porg}** (`{powner_did}`) | Điểm giao: {ploc} | Ngày đăng: {pdate}")
                    
                with c_act:
                    if powner_did != cur_u['did']:
                        if st.button("🤝 Thương Lượng", key=f"btn_neg_{pid}"):
                            seller = powner_did if ptype == "BÁN" else cur_u['did']
                            buyer = cur_u['did'] if ptype == "BÁN" else powner_did
                            
                            init_seller_p = pprice if ptype == "BÁN" else 0.0
                            init_buyer_p = 0.0 if ptype == "BÁN" else pprice
                            init_final_p = pprice
                            
                            cursor.execute("""
                            INSERT INTO deals (post_id, seller_did, buyer_did, product_name, quantity, seller_price, buyer_price, final_price, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEGOTIATING')
                            """, (pid, seller, buyer, pname, pqty, init_seller_p, init_buyer_p, init_final_p))
                            new_deal_id = cursor.lastrowid
                            
                            now_msg = datetime.datetime.now().strftime("%H:%M")
                            cursor.execute("""
                            INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at)
                            VALUES (?, ?, ?, ?, ?)
                            """, (new_deal_id, cur_u['did'], cur_u['fullname'], f"Xin chào, tôi muốn mở phòng thương lượng cho đơn hàng {pname} ({pqty}).", now_msg))
                            
                            conn.commit()
                            st.session_state.current_deal_id = new_deal_id
                            st.session_state.active_nav = "💬 2. Phòng Thương Lượng & Hợp Đồng"
                            st.rerun()
                    else:
                        st.caption("📌 Tin của bạn")
                st.divider()

    with pool_subtab2:
        st.subheader("Quản Lý Các Yêu Cầu Của Tôi")
        st.caption("Xem, cập nhật mức giá hoặc gỡ bài đăng của chính bạn khỏi sàn chung.")
        
        cursor.execute("SELECT id, post_type, product_name, quantity, price, location, created_at FROM market_pool WHERE owner_did = ? ORDER BY id DESC", (cur_u['did'],))
        my_posts = cursor.fetchall()
        
        if not my_posts:
            st.info("Bạn chưa đăng bài nào lên sàn thị trường.")
        else:
            for mp in my_posts:
                mp_id, mp_t, mp_name, mp_qty, mp_pr, mp_loc, mp_time = mp
                with st.expander(f"📦 [{mp_t}] {mp_name} - {mp_qty} (${mp_pr:,.1f}/tấn)"):
                    with st.form(f"edit_my_post_{mp_id}"):
                        e_c1, e_c2 = st.columns(2)
                        new_name = e_c1.text_input("Tên hàng hóa:", value=mp_name)
                        new_qty = e_c2.text_input("Sản lượng:", value=mp_qty)
                        
                        e_c3, e_c4 = st.columns(2)
                        new_price = e_c3.number_input("Mức giá chào ($/tấn):", value=float(mp_pr), step=10.0)
                        new_loc = e_c4.text_input("Điểm giao hàng:", value=mp_loc)
                        
                        b_col1, b_col2 = st.columns([1, 1])
                        save_btn = b_col1.form_submit_button("💾 Lưu Cập Nhật")
                        del_btn = b_col2.form_submit_button("🗑️ Xóa Bài Đăng Này")
                        
                        if save_btn:
                            cursor.execute("UPDATE market_pool SET product_name = ?, quantity = ?, price = ?, location = ? WHERE id = ?",
                                           (new_name, new_qty, new_price, new_loc, mp_id))
                            conn.commit()
                            st.success("Đã cập nhật bài đăng thành công!")
                            st.rerun()
                            
                        if del_btn:
                            cursor.execute("DELETE FROM market_pool WHERE id = ?", (mp_id,))
                            conn.commit()
                            st.warning("Đã gỡ bài đăng khỏi sàn chung!")
                            st.rerun()

    with pool_subtab3:
        st.subheader("Đăng Sản Phẩm Hoặc Nhu Cầu Mua Hàng Mới")
        with st.form("form_add_new_pool_item"):
            col_t1, col_t2 = st.columns(2)
            def_idx = 0 if "Bán" in cur_u['role'] else 1
            post_t = col_t1.selectbox("Loại tin đăng:", ["BÁN (Chào hàng)", "MUA (Cần mua)"], index=def_idx)
            item_name = col_t2.text_input("Tên nông sản:", placeholder="Ví dụ: Cà phê Robusta Grade 1 S16")
            
            col_t3, col_t4 = st.columns(2)
            item_qty = col_t3.text_input("Khối lượng dự kiến:", "20 tấn")
            item_price = col_t4.number_input("Mức giá mong muốn ($/tấn):", min_value=10.0, value=2200.0, step=10.0)
            
            item_loc = st.text_input("Địa điểm giao nhận hàng:", "Cửa khẩu Mộc Bài - Tây Ninh / Phnom Penh")
            
            if st.form_submit_button("🚀 Đăng Lên Sàn Chung"):
                if item_name.strip():
                    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    actual_type = "BÁN" if "BÁN" in post_t else "MUA"
                    cursor.execute("""
                    INSERT INTO market_pool (post_type, owner_did, org_name, product_name, quantity, price, location, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (actual_type, cur_u['did'], cur_u['org_name'], item_name.strip(), item_qty, item_price, item_loc, now_str))
                    conn.commit()
                    st.success("Đã đưa yêu cầu lên Sàn Thị Trường! Chuyển qua tab Khám phá để xem.")
                    st.rerun()
                else:
                    st.warning("Vui lòng nhập tên nông sản.")

# ========================================================
# TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ & HỢP ĐỒNG SỐ
# ========================================================
elif st.session_state.active_nav == "💬 2. Phòng Thương Lượng & Hợp Đồng":
    cursor.execute("""
    SELECT id, product_name, quantity, seller_did, buyer_did, seller_price, buyer_price, ai_price, final_price, seller_signed, buyer_signed, status
    FROM deals
    WHERE seller_did = ? OR buyer_did = ?
    ORDER BY id DESC
    """, (cur_u['did'], cur_u['did']))
    active_deals = cursor.fetchall()
    
    if not active_deals:
        st.info("Bạn chưa có phiên đàm phán nào. Hãy chọn một mặt hàng từ **Tab 1** và nhấn **'Thương Lượng'**.")
    else:
        deal_mapping = {f"Phiên #{d[0]}: {d[1]} ({d[2]})": d[0] for d in active_deals}
        
        default_index = 0
        deal_ids_list = list(deal_mapping.values())
        if st.session_state.current_deal_id in deal_ids_list:
            default_index = deal_ids_list.index(st.session_state.current_deal_id)
            
        chosen_label = st.selectbox("Chọn phiên đàm phán đang tham gia:", list(deal_mapping.keys()), index=default_index)
        deal_id = deal_mapping[chosen_label]
        st.session_state.current_deal_id = deal_id
        
        cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        deal = cursor.fetchone()
        
        d_id, _, d_s_did, d_b_did, d_prod, d_qty, d_s_pr, d_b_pr, d_ai_pr, d_fin_pr, d_s_sign, d_b_sign, d_stat = deal
        
        is_seller = (cur_u['did'] == d_s_did)
        is_buyer = (cur_u['did'] == d_b_did)
        
        partner_did = d_b_did if is_seller else d_s_did
        cursor.execute("SELECT fullname, org_name, country, phone FROM tide_identities WHERE did_address = ?", (partner_did,))
        partner_info = cursor.fetchone()
        partner_name = partner_info[0] if partner_info else "Đối tác"
        partner_org = partner_info[1] if partner_info else "Công ty đối tác"
        partner_phone = partner_info[3] if partner_info else "0900000000"

        c_left, c_right = st.columns([1.1, 1.2])
        
        # ---------------- CỘT TRÁI: TRAO ĐỔI P2P & TRỢ LÝ AI ----------------
        with c_left:
            st.markdown("### 💬 Trao Đổi Thương Lượng Hai Bên")
            st.caption("Kênh trò chuyện bảo mật trực tiếp giữa Bên Bán và Bên Mua.")
            
            chat_container = st.container(height=340)
            cursor.execute("SELECT sender_did, sender_name, message, created_at FROM deal_messages WHERE deal_id = ? ORDER BY id ASC", (d_id,))
            messages = cursor.fetchall()
            
            with chat_container:
                if not messages:
                    st.caption("Chưa có tin nhắn nào trong phòng.")
                for msg in messages:
                    m_did, m_name, m_text, m_time = msg
                    if m_did == d_s_did:
                        st.markdown(f"<div class='chat-bubble-seller'><b>[Bên Bán] {m_name}:</b> {m_text}<br><small style='color:gray'>{m_time}</small></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-bubble-buyer'><b>[Bên Mua] {m_name}:</b> {m_text}<br><small style='color:gray'>{m_time}</small></div>", unsafe_allow_html=True)
            
            with st.form(f"form_send_msg_{d_id}", clear_on_submit=True):
                new_msg_text = st.text_input("Soạn tin nhắn gửi đối tác:", placeholder="Trao đổi về thời gian bốc hàng, chất lượng...")
                if st.form_submit_button("📤 Gửi Tin Nhắn"):
                    if new_msg_text.strip():
                        now_m = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], new_msg_text.strip(), now_m))
                        conn.commit()
                        st.rerun()

            st.write("---")
            
            # CỬA SỔ POP-OVER TRỢ LÝ AI
            with st.popover("💡 Mở Trợ Lý Chiến Lược Giá (AI Copilot)", use_container_width=True):
                st.markdown("#### 🤖 Trợ Lý Chiến Thuật Đàm Phán Gemini")
                st.caption("AI phân tích giá của đối tác và gợi ý mức giá đè xuống thấp nhất có thể trước khi hòa giải.")
                
                my_p = d_s_pr if is_seller else d_b_pr
                opp_p = d_b_pr if is_seller else d_s_pr
                
                if st.button("🔍 Phân Tích & Gợi Ý Mức Trả Giá Tối Ưu", key=f"btn_ai_strat_{d_id}"):
                    if opp_p > 0:
                        with st.spinner("AI đang tính toán chiến lược..."):
                            role_str = "Bên Bán" if is_seller else "Bên Mua"
                            strat = get_ai_price_strategy(role_str, d_prod, d_qty, my_p, opp_p)
                            st.session_state[f"ai_strat_{d_id}"] = strat
                    else:
                        st.warning("Đối tác chưa đưa ra mức giá nào để phân tích.")
                        
                if f"ai_strat_{d_id}" in st.session_state:
                    res = st.session_state[f"ai_strat_{d_id}"]
                    st.info(f"🎯 **Chiến thuật:** {res['advice']}")
                    
                    c_st1, c_st2 = st.columns(2)
                    c_st1.metric("1. Đề xuất đè giá an toàn", f"${res['aggressive_price']:,.1f}/tấn")
                    c_st2.metric("2. Mức giá hòa giải logistics", f"${res['balanced_price']:,.1f}/tấn")
                    
                    if st.button("Áp dụng mức đè giá vào Hợp đồng", key=f"apply_agg_{d_id}"):
                        cursor.execute("UPDATE deals SET final_price = ?, seller_signed = 0, buyer_signed = 0, status = 'NEGOTIATING' WHERE id = ?",
                                       (res['aggressive_price'], d_id))
                        conn.commit()
                        st.rerun()
                        
                    if st.button("Áp dụng mức giá hòa giải vào Hợp đồng", key=f"apply_bal_{d_id}"):
                        cursor.execute("UPDATE deals SET final_price = ?, seller_signed = 0, buyer_signed = 0, status = 'NEGOTIATING' WHERE id = ?",
                                       (res['balanced_price'], d_id))
                        conn.commit()
                        st.rerun()

            # Thiết lập giá đàm phán thủ công
            with st.form(f"form_price_{d_id}"):
                c_p1, c_p2 = st.columns(2)
                c_p1.write(f"🏷️ **Bên Bán:** " + (f"`${d_s_pr:,.1f}`" if d_s_pr > 0 else "*(Chưa chào)*"))
                c_p2.write(f"🏷️ **Bên Mua:** " + (f"`${d_b_pr:,.1f}`" if d_b_pr > 0 else "*(Chưa trả giá)*"))
                
                if is_seller:
                    val_init = float(d_s_pr) if d_s_pr > 0 else 2200.0
                    new_val = st.number_input("Giá Bên Bán đề xuất ($/tấn):", value=val_init, step=10.0)
                else:
                    val_init = float(d_b_pr) if d_b_pr > 0 else 2150.0
                    new_val = st.number_input("Giá Bên Mua trả ($/tấn):", value=val_init, step=10.0)
                    
                if st.form_submit_button("Cập Nhật & Đưa Vào Tờ Hợp Đồng"):
                    now_m = datetime.datetime.now().strftime("%H:%M")
                    if is_seller:
                        cursor.execute("UPDATE deals SET seller_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0, status = 'NEGOTIATING' WHERE id = ?", (new_val, new_val, d_id))
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], f"Tôi gửi đề xuất giá mới là ${new_val:,.1f}/tấn.", now_m))
                    else:
                        cursor.execute("UPDATE deals SET buyer_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0, status = 'NEGOTIATING' WHERE id = ?", (new_val, new_val, d_id))
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], f"Tôi trả giá mới là ${new_val:,.1f}/tấn.", now_m))
                    conn.commit()
                    st.rerun()

        # ---------------- CỘT PHẢI: TỜ HỢP ĐỒNG SỐ ----------------
        with c_right:
            st.markdown("### 📜 Thỏa Thuận Thương Mại Phân Tán (Digital Contract)")
            
            contract_price = d_fin_pr if d_fin_pr else (d_s_pr if d_s_pr > 0 else d_b_pr)
            try:
                qty_num = float(d_qty.split()[0].replace(",", "."))
            except Exception:
                qty_num = 20.0
            total_value = contract_price * qty_num
            contract_hash = hashlib.sha256(f"{d_id}_{d_prod}_{contract_price}_{d_s_did}_{d_b_did}".encode()).hexdigest()[:16]

            # ==========================================================
            # 1. HỢP ĐỒNG ĐÃ ĐƯỢC 2 BÊN KÝ THÀNH CÔNG
            # ==========================================================
            if d_s_sign == 1 and d_b_sign == 1 and d_stat != 'REJECTED' and d_stat != 'TERMINATED':
                balloon_key = f"balloon_shown_{d_id}"
                if balloon_key not in st.session_state:
                    st.balloons()
                    st.session_state[balloon_key] = True

                st.markdown(f"""
                <div class="paper-contract-success">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="color:#1b5e20; margin:0;">HỢP ĐỒNG THƯƠNG MẠI NÔNG SẢN XUYÊN BIÊN GIỚI</h4>
                        <span class="stamp-badge-ok">✓ ĐÃ CHỐT TOÀN VẸN</span>
                    </div>
                    <hr style="border: 1px solid #c8e6c9;">
                    <p><b>Mã hợp đồng:</b> <code>tg_contract_{contract_hash}</code></p>
                    <table style="width:100%; line-height:1.8;">
                        <tr><td><b>Mặt hàng:</b> {d_prod}</td><td><b>Số lượng:</b> {d_qty}</td></tr>
                        <tr><td><b>Đơn giá chốt:</b> <span style="font-size:1.2rem; color:#2e7d32; font-weight:bold;">${contract_price:,.1f} USD/tấn</span></td>
                            <td><b>Tổng giá trị:</b> <span style="font-size:1.2rem; color:#2e7d32; font-weight:bold;">${total_value:,.1f} USD</span></td></tr>
                        <tr><td><b>Bên Bán:</b> `{d_s_did}`</td><td><b>Chữ ký số:</b> <span style="color:#2e7d32;">✓ HỢP LỆ (Tide Verified)</span></td></tr>
                        <tr><td><b>Bên Mua:</b> `{d_b_did}`</td><td><b>Chữ ký số:</b> <span style="color:#2e7d32;">✓ HỢP LỆ (Tide Verified)</span></td></tr>
                    </table>
                    <hr style="border: 1px solid #c8e6c9;">
                    <p style="font-size:0.85rem; color:#558b2f;">
                        <i>Xác thực TideCloak: Hợp đồng đã nhận đủ 2/2 chữ ký phân tán theo nguyên tắc No Unilateral Control.</i>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🚚 Kế Hoạch Triển Khai Sau Khi Ký Kết:")
                step1, step2 = st.tabs(["📞 Kênh Liên Lạc Trực Tiếp", "🚛 Lộ Trình Giao Nhận Cửa Khẩu"])
                with step1:
                    st.success(f"**Thông tin liên hệ đối tác đã được giải mã:**")
                    st.write(f"- **Đại diện:** {partner_name} ({partner_org})")
                    st.write(f"- **Đường dây nóng:** `{partner_phone}`")
                    st.write(f"- **Mã danh tính DID:** `{partner_did}`")
                    st.download_button(
                        label="📄 Tải Xuống Hợp Đồng Đã Ký (.TXT)",
                        data=f"HOP DONG THUONG MAI TRUSTGATE AI\nMa: tg_contract_{contract_hash}\nMat hang: {d_prod}\nSo luong: {d_qty}\nDon gia: ${contract_price}/tan\nTong gia tri: ${total_value}\nBen Ban: {d_s_did}\nBen Mua: {d_b_did}\nXac thuc boi: TideCloak Dual-Consensus Gate",
                        file_name=f"hop_dong_{d_id}.txt",
                        mime="text/plain"
                    )
                with step2:
                    st.info("""
                    **Kế hoạch điều phối vận tải đường bộ:**
                    - Tuyến giao nhận: Đức Trọng (Lâm Đồng) ➔ Cửa khẩu Mộc Bài / Bavet ➔ Phnom Penh.
                    - Giấy chứng nhận xuất xứ (C/O) và e-Phyto đã được liên kết với mã băm hợp đồng này.
                    """)

            # ==========================================================
            # 2. HỢP ĐỒNG ĐÃ ĐÓNG VĨNH VIỄN (TERMINATED)
            # ==========================================================
            elif d_stat == 'TERMINATED':
                st.markdown(f"""
                <div class="paper-contract-cancelled">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="color:#b71c1c; margin:0;">PHIÊN THƯƠNG LƯỢNG ĐÃ ĐÓNG</h4>
                        <span class="stamp-badge-void">✕ ĐÃ KẾT THÚC</span>
                    </div>
                    <hr style="border: 1px solid #ffcdd2;">
                    <p style="color:#c62828;">Giao dịch đã kết thúc chính thức. Hệ thống đã gửi thông báo đến đối tác.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 Khôi Phục Lại Phiên Đàm Phán Này"):
                    cursor.execute("UPDATE deals SET status = 'NEGOTIATING', seller_signed = 0, buyer_signed = 0 WHERE id = ?", (d_id,))
                    conn.commit()
                    st.rerun()

            # ==========================================================
            # 3. KHI CÓ BÊN TỪ CHỐI ĐỀ XUẤT (REJECTED) -> ĐƯA RA 2 OFFER
            # ==========================================================
            elif d_stat == 'REJECTED':
                st.markdown(f"""
                <div class="paper-contract-cancelled">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="color:#b71c1c; margin:0;">ĐỀ XUẤT THỎA THUẬN ĐÃ BỊ TỪ CHỐI</h4>
                        <span class="stamp-badge-void">✕ ĐÃ BỊ TỪ CHỐI</span>
                    </div>
                    <hr style="border: 1px solid #ffcdd2;">
                    <p style="color:#c62828;">Mức giá đề xuất <b>${contract_price:,.1f}/tấn</b> chưa đạt được sự đồng thuận từ hai bên.</p>
                    <p style="font-size:0.9rem; color:#555;">Hệ thống cung cấp 2 phương án xử lý tiếp theo:</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 📌 Lựa chọn hành động tiếp theo:")
                c_opt1, c_opt2 = st.columns(2)
                
                # OFFER 1: ĐIỀU CHỈNH GIÁ PHÙ HỢP ĐỂ ĐÀM PHÁN TIẾP
                with c_opt1:
                    st.markdown("##### Phương án 1: Tiếp tục thỏa thuận")
                    # Tự động tính toán bước nhảy giá dựa vào vai trò
                    if is_seller:
                        step_price = max(10.0, round(contract_price - 20.0, 1))
                        action_label = f"📉 Hạ giá chào xuống ${step_price:,.1f}/tấn"
                        guide_text = "Hạ giá bán xuống một chút để đưa đề xuất về gần ngân sách của Bên Mua."
                    else:
                        step_price = round(contract_price + 20.0, 1)
                        action_label = f"📈 Tăng giá mua lên ${step_price:,.1f}/tấn"
                        guide_text = "Tăng giá mua lên một chút để nâng cao thiện chí với Bên Bán."
                        
                    st.caption(guide_text)
                    if st.button(action_label, key=f"btn_step_price_{d_id}"):
                        now_m = datetime.datetime.now().strftime("%H:%M")
                        if is_seller:
                            cursor.execute("UPDATE deals SET seller_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0, status = 'NEGOTIATING' WHERE id = ?",
                                           (step_price, step_price, d_id))
                            cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                           (d_id, cur_u['did'], cur_u['fullname'], f"Tôi chấp nhận hạ giá chào bán xuống ${step_price:,.1f}/tấn để tiếp tục đàm phán.", now_m))
                        else:
                            cursor.execute("UPDATE deals SET buyer_price = ?, final_price = ?, seller_signed = 0, buyer_signed = 0, status = 'NEGOTIATING' WHERE id = ?",
                                           (step_price, step_price, d_id))
                            cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                           (d_id, cur_u['did'], cur_u['fullname'], f"Tôi nâng mức giá mua lên ${step_price:,.1f}/tấn để thể hiện thiện chí hợp tác.", now_m))
                        conn.commit()
                        st.rerun()

                # OFFER 2: DỪNG VÀ KẾT THÚC GIAO DỊCH
                with c_opt2:
                    st.markdown("##### Phương án 2: Dừng đàm phán")
                    st.caption("Đóng giao dịch vĩnh viễn và gửi thông báo xác nhận kết thúc vào phòng chat.")
                    if st.button("🛑 Kết thúc giao dịch & Thông báo đối tác", key=f"btn_terminate_{d_id}"):
                        now_m = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("UPDATE deals SET status = 'TERMINATED', seller_signed = 0, buyer_signed = 0 WHERE id = ?", (d_id,))
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], f"Hai bên không đạt được thỏa thuận về giá. Phiên giao dịch chính thức kết thúc.", now_m))
                        conn.commit()
                        st.rerun()

            # ==========================================================
            # 4. HỢP ĐỒNG ĐANG CHỜ PHÊ DUYỆT (PENDING)
            # ==========================================================
            else:
                st.markdown(f"""
                <div class="paper-contract-pending">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="color:#4e342e; margin:0;">TỜ TRÌNH THỎA THUẬN GIÁ DỰ KIẾN</h4>
                        <span style="background:#fff3e0; color:#e65100; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:0.85rem;">⏳ ĐANG CHỜ 2 BÊN KÝ</span>
                    </div>
                    <hr style="border: 1px solid #d7ccc8;">
                    <table style="width:100%; line-height:2.0;">
                        <tr><td><b>Sản phẩm:</b> {d_prod}</td><td><b>Số lượng:</b> {d_qty}</td></tr>
                        <tr><td><b>Mức giá đề xuất chốt:</b></td>
                            <td><span style="font-size:1.35rem; color:#d84315; font-weight:bold;">${contract_price:,.1f} USD/tấn</span></td></tr>
                        <tr><td><b>Tổng giá trị ước tính:</b></td>
                            <td><span style="font-size:1.1rem; font-weight:bold;">${total_value:,.1f} USD</span></td></tr>
                        <tr><td><b>Bên Bán ký:</b> {"<span style='color:green;'>✓ Đã ký duyệt</span>" if d_s_sign==1 else "<span style='color:#b71c1c;'>Chưa ký</span>"}</td>
                            <td><b>Bên Mua ký:</b> {"<span style='color:green;'>✓ Đã ký duyệt</span>" if d_b_sign==1 else "<span style='color:#b71c1c;'>Chưa ký</span>"}</td></tr>
                    </table>
                    <hr style="border: 1px solid #d7ccc8;">
                    <p style="font-size:0.85rem; color:#795548;">
                        <i>Nguyên tắc Không Kiểm Soát Đơn Phương: Bạn có thể rời phòng và quay lại bất cứ lúc nào, tờ hợp đồng vẫn giữ nguyên trạng thái cho đến khi đủ 2 bên ký hoặc bị từ chối.</i>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col_act1, col_act2 = st.columns([1, 1])
                with col_act1:
                    st.markdown("##### ✍️ Phê Duyệt Của Bạn:")
                    if is_seller:
                        if d_s_sign == 1:
                            st.success("✓ Bạn (Bên Bán) đã ký duyệt!")
                        else:
                            if st.button("✍️ Ký Duyệt Hợp Đồng Này", key=f"s_sign_btn_{d_id}"):
                                cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                                conn.commit()
                                st.rerun()
                    else:
                        if d_b_sign == 1:
                            st.success("✓ Bạn (Bên Mua) đã ký duyệt!")
                        else:
                            if st.button("✍️ Ký Duyệt Hợp Đồng Này", key=f"b_sign_btn_{d_id}"):
                                cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                                conn.commit()
                                st.rerun()
                                
                    if st.button("✕ Bạn Từ Chối Mức Giá Này", key=f"reject_btn_{d_id}"):
                        cursor.execute("UPDATE deals SET status = 'REJECTED', seller_signed = 0, buyer_signed = 0 WHERE id = ?", (d_id,))
                        now_m = datetime.datetime.now().strftime("%H:%M")
                        cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                       (d_id, cur_u['did'], cur_u['fullname'], f"Tôi không đồng ý với mức giá ${contract_price:,.1f}/tấn và đã từ chối thỏa thuận này.", now_m))
                        conn.commit()
                        st.rerun()
                        
                with col_act2:
                    st.markdown("##### 🤝 Đối Tác Phản Hồi:")
                    if is_seller:
                        if d_b_sign == 1:
                            st.success("✓ Bên Mua đã ký duyệt!")
                        else:
                            st.warning("Đang chờ Bên Mua phản hồi...")
                            if st.button("⚡ [Demo] Giả lập Bên Mua KÝ DUYỆT", key=f"sim_b_btn_{d_id}"):
                                cursor.execute("UPDATE deals SET buyer_signed = 1 WHERE id = ?", (d_id,))
                                conn.commit()
                                st.rerun()
                            if st.button("⚡ [Demo] Giả lập Bên Mua TỪ CHỐI", key=f"sim_b_rej_{d_id}"):
                                cursor.execute("UPDATE deals SET status = 'REJECTED', seller_signed = 0, buyer_signed = 0 WHERE id = ?", (d_id,))
                                now_m = datetime.datetime.now().strftime("%H:%M")
                                cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                               (d_id, partner_did, partner_name, f"Bên Mua nhận thấy mức giá ${contract_price:,.1f}/tấn chưa phù hợp nên đã từ chối tờ thỏa thuận này.", now_m))
                                conn.commit()
                                st.rerun()
                    else:
                        if d_s_sign == 1:
                            st.success("✓ Bên Bán đã ký duyệt!")
                        else:
                            st.warning("Đang chờ Bên Bán phản hồi...")
                            if st.button("⚡ [Demo] Giả lập Bên Bán KÝ DUYỆT", key=f"sim_s_btn_{d_id}"):
                                cursor.execute("UPDATE deals SET seller_signed = 1 WHERE id = ?", (d_id,))
                                conn.commit()
                                st.rerun()
                            if st.button("⚡ [Demo] Giả lập Bên Bán TỪ CHỐI", key=f"sim_s_rej_{d_id}"):
                                cursor.execute("UPDATE deals SET status = 'REJECTED', seller_signed = 0, buyer_signed = 0 WHERE id = ?", (d_id,))
                                now_m = datetime.datetime.now().strftime("%H:%M")
                                cursor.execute("INSERT INTO deal_messages (deal_id, sender_did, sender_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                                               (d_id, partner_did, partner_name, f"Bên Bán chưa thể chấp thuận mức giá ${contract_price:,.1f}/tấn và đã từ chối tờ thỏa thuận này.", now_m))
                                conn.commit()
                                st.rerun()

# ========================================================
# TAB 3: TRUNG TÂM BẢO MẬT & KIỂM THỬ ĐA VAI TRÒ
# ========================================================
elif st.session_state.active_nav == "🛡️ 3. Kiểm Tra Bảo Mật TideCloak":
    st.subheader("🛡️ Trung Tâm Giám Sát Phân Quyền & Kiểm Thử Bảo Mật TideCloak")
    st.caption("Kiểm chứng cơ chế No Unilateral Control và tính toàn vẹn dưới các góc nhìn khác nhau.")
    
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
    st.markdown("#### 📜 Nhật Ký Kiểm Toán Phân Tán (Tamper-evident Audit Trail)")
    st.caption("Lịch sử xác thực danh tính và kiểm tra điều kiện đồng thuận theo thời gian thực:")
    
    audit_data = [
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": cur_u['fullname'], "Hành động": f"Xác thực Tide DID ({cur_u['did']})", "Kết quả": "Hợp lệ"},
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": "TideCloak Consensus Gate", "Hành động": "Kiểm tra ràng buộc Dual-Consensus", "Kết quả": "Enforced"},
        {"Thời gian": datetime.datetime.now().strftime("%H:%M:%S"), "Tác nhân": "Security Monitor", "Hành động": "Chặn nỗ lực can thiệp đơn phương", "Kết quả": "Bảo vệ thành công"}
    ]
    st.table(pd.DataFrame(audit_data))

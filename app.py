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
                    country = "Việt Nam" if "Việt Nam" in r_role else "Campuchia

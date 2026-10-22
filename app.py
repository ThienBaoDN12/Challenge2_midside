import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="TrustGate AI - Smart Negotiation", layout="wide", page_icon="🤝")

# 1. KHỞI TẠO STATE
if "current_user" not in st.session_state:
    st.session_state.current_user = {
        "name": "Tran Thu Ha",
        "org": "Nong san Lam Vien",
        "role": "Seller (Viet Nam)"
    }

if "market_items" not in st.session_state:
    st.session_state.market_items = [
        {"id": "LST-VN-01", "type": "BAN", "owner": "Nong san Lam Vien (VN)", "product": "Ca phe Robusta S16", "quantity": "20 tan", "price": 2150, "location": "Duc Trong, Lam Dong"},
        {"id": "DMD-KH-01", "type": "MUA", "owner": "Mekong Fresh Trading (KH)", "product": "Ca phe Robusta S16", "quantity": "20 tan", "price": 2000, "location": "Cua khau Moc Bai / Phnom Penh"},
        {"id": "LST-VN-02", "type": "BAN", "owner": "Ho tieu Chu Se (VN)", "product": "Ho tieu den 500g/l", "quantity": "10 tan", "price": 4200, "location": "Gia Lai"}
    ]

if "active_deal" not in st.session_state:
    st.session_state.active_deal = None

# Header và Chuyển đổi vai trò
st.title("TrustGate AI — San Thuong Luong Nong San Da Ben")
st.caption("Mo hinh kiem soat truy cap phan tan: No Unilateral Control (Powered by TideCloak)")

with st.sidebar:
    st.header("Tai Khoan Dang Nhap")
    user_choice = st.radio(
        "Chuyen vai tro thu nghiem:",
        ["Ben Ban: Tran Thu Ha (Lam Vien - VN)", "Ben Mua: Sok Dara (Mekong Fresh - KH)"]
    )
    if "Lam Vien" in user_choice:
        st.session_state.current_user = {"name": "Tran Thu Ha", "org": "Nong san Lam Vien", "role": "Seller (Viet Nam)"}
    else:
        st.session_state.current_user = {"name": "Sok Dara", "org": "Mekong Fresh Trading", "role": "Buyer (Campuchia)"}
    
    st.info(f"**Dang dong vai:** {st.session_state.current_user['name']}\n\n**To chuc:** {st.session_state.current_user['org']}\n\n**Vai tro:** {st.session_state.current_user['role']}")
    
    st.divider()
    st.markdown("### Phim Tat Demo")
    if st.button("Dat lai toan bo giao dich"):
        st.session_state.active_deal = None
        st.rerun()

# 3 Tab chinh
tab_market, tab_deal, tab_security = st.tabs([
    "1. San Thi Truong Chung (Pool)", 
    "2. Phong Thuong Luong Gia", 
    "3. Cong Bao Mat TideCloak"
])

# ========================================================
# TAB 1: SAN THI TRUONG CHUNG
# ========================================================
with tab_market:
    st.subheader("Pool Hang Hoa & Nhu Cau Thi Truong")
    st.write("Dang tai nhu cau hoac chon mot tin niem yet de bat dau mo phien dam phan.")
    
    with st.expander("Dang Tin Moi Len Thi Truong", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        p_type = c1.selectbox("Loai bai dang", ["BAN (Listing)", "MUA (Demand)"])
        p_prod = c2.text_input("Ten nong san", "Ca phe Robusta nhan xanh")
        p_qty = c3.text_input("Khoi luong", "20 tan")
        p_price

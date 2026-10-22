import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="TrustGate AI - Smart Trading", layout="wide", page_icon="🌾")

# Khởi tạo dữ liệu mẫu cho Market Pool
if "market_items" not in st.session_state:
    st.session_state.market_items = [
        {"id": "LST-01", "type": "BÁN", "owner": "Nông sản Lâm Viên (VN)", "product": "Cà phê Robusta S16", "quantity": "60 tấn", "price": 2150, "location": "Đức Trọng, VN"},
        {"id": "DMD-01", "type": "MUA", "owner": "Mekong Fresh (KH)", "product": "Cà phê Robusta S16", "quantity": "20 tấn", "price": 2000, "location": "Phnom Penh, KH"},
        {"id": "LST-02", "type": "BÁN", "owner": "Hồ tiêu Chư Sê (VN)", "product": "Hồ tiêu đen 500g/l", "quantity": "12 tấn", "price": 4200, "location": "Gia Lai, VN"}
    ]

# Trạng thái đàm phán
if "negotiation" not in st.session_state:
    st.session_state.negotiation = {
        "active": True,
        "seller_price": 2150,
        "buyer_price": 2000,
        "ai_suggested_price": None,
        "final_price": None,
        "seller_signed": False,
        "buyer_signed": False
    }

st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.caption("Bảo vệ dữ liệu bí mật & Ngăn chặn quyền kiểm soát đơn phương bằng TideCloak")

tab_market, tab_deal, tab_security = st.tabs([
    "🛒 Sàn Thị Trường Chung (Pool)", 
    "💬 Phòng Thương Lượng Giá & AI", 
    "🛡️ Cổng Bảo Mật TideCloak"
])

# ========================================================
# TAB 1: SÀN THỊ TRƯỜNG CHUNG (MARKETPLACE POOL)
# ========================================================
with tab_market:
    st.subheader("1. Đăng tin lên sàn thị trường chung")
    with st.expander("➕ Đăng nhu cầu BÁN hoặc MUA mới", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        post_type = c1.selectbox("Loại tin", ["BÁN (Seller VN)", "MUA (Buyer KH)"])
        product_name = c2.text_input("Tên nông sản", "Cà phê Robusta S18")
        qty = c3.text_input("Khối lượng / Đơn vị", "25 tấn")
        price = c4.number_input("Mức giá mong muốn (USD/tấn)", min_value=100, value=2100)
        
        if st.button("Đăng tin lên thị trường"):
            role_owner = "Lâm Viên (VN)" if "BÁN" in post_type else "Mekong Trading (KH)"
            st.session_state.market_items.append({
                "id": f"ITEM-{len(st.session_state.market_items)+1}",
                "type": "BÁN" if "BÁN" in post_type else "MUA",
                "owner": role_owner,
                "product": product_name,
                "quantity": qty,
                "price": price,
                "location": "Việt Nam / Campuchia"
            })
            st.success("Đã đăng tin thành công vào Pool thị trường chung!")
            st.rerun()

    st.subheader("2. Danh sách hàng hóa trên thị trường")
    df_market = pd.DataFrame(st.session_state.market_items)
    st.dataframe(df_market, use_container_width=True, hide_index=True)
    
    st.info("💡 Tìm thấy mặt hàng phù hợp? Nhấn sang **Phòng Thương Lượng** để bắt đầu đàm phán mức giá.")

# ========================================================
# TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ & AI COPILOT
# ========================================================
with tab_deal:
    st.subheader("Phòng Thương Lượng Giá: Nông sản Lâm Viên (VN) ↔ Mekong Fresh (KH)")
    
    col_room1, col_room2 = st.columns([1, 1])
    
    with col_room1:
        st.markdown("#### ⚖️ Trạng Thái Trả Giá Của Hai Bên")
        st.write(f"🏷️ **Giá Người bán chào ban đầu:** `${st.session_state.negotiation['seller_price']} / tấn`")
        st.write(f"🏷️ **Giá Người mua đề nghị mua:** `${st.session_state.negotiation['buyer_price']} / tấn`")
        
        diff = st.session_state.negotiation['seller_price'] - st.session_state.negotiation['buyer_price']
        st.warning(f"Chênh lệch hiện tại: **${diff} / tấn**. Người mua từ chối mức giá của Người bán.")
        
        st.markdown("---")
        st.markdown("#### 🤖 AI Trợ Lý Thương Lượng (Negotiation Copilot)")
        st.caption("AI chỉ đọc dữ liệu giá công khai và chi phí vận chuyển; không truy cập kho giá vốn bí mật.")
        
        if st.button("Kích hoạt AI tính toán mức giá cân bằng tối ưu"):
            # Thuật toán tính giá khuyến nghị dựa trên biên độ và cước phí vận tải
            shipping_cost = 35 # USD/tấn
            optimal = (st.session_state.negotiation['seller_price'] + st.session_state.negotiation['buyer_price']) / 2 + (shipping_cost / 2)
            st.session_state.negotiation['ai_suggested_price'] = round(optimal, 1)
            st.session_state.negotiation['final_price'] = st.session_state.negotiation['ai_suggested_price']
            st.rerun()
            
        if st.session_state.negotiation['ai_suggested_price']:
            st.success(f"🎯 **AI Đề Xuất:** Nên chốt ở mức **${st.session_state.negotiation['ai_suggested_price']} / tấn**")
            st.write("*Lý do:* Mức giá này bù đắp 50% phí vận chuyển Mộc Bài - Phnom Penh và đảm bảo biên lợi nhuận cho cả hai bên.")

    with col_room2:
        st.markdown("#### ✍️ Phê Duyệt Chốt Thỏa Thuận (TideCloak Dual-Consensus)")
        st.caption("Nguyên tắc Không Kiểm Soát Đơn Phương: Hợp đồng chỉ chốt khi cả hai bên cùng ký số.")
        
        price_to_close = st.session_state.negotiation['final_price'] if st.session_state.negotiation['final_price'] else st.session_state.negotiation['seller_price']
        st.metric("Giá Chốt Hợp Đồng Dự Kiến", f"${price_to_close} / tấn")
        
        col_s_btn, col_b_btn = st.columns(2)
        with col_s_btn:
            if not st.session_state.negotiation['seller_signed']:
                if st.button("✍️ Người Bán Ký Chấp Thuận"):
                    st.session_state.negotiation['seller_signed'] = True
                    st.rerun()
            else:
                st.success("✅ Người bán đã ký")
                
        with col_b_btn:
            if not st.session_state.negotiation['buyer_signed']:
                if st.button("✍️ Người Mua Ký Chấp Thuận"):
                    st.session_state.negotiation['buyer_signed'] = True
                    st.rerun()
            else:
                st.success("✅ Người mua đã ký")
                
        # Kiểm tra điều kiện đồng thuận 2 bên
        if st.session_state.negotiation['seller_signed'] and st.session_state.negotiation['buyer_signed']:
            st.balloons()
            st.success("🎉 **GIAO DỊCH ĐÃ ĐƯỢC CHỐT THÀNH CÔNG BẰNG TIDECLOAK!**")
            st.write("Hai bên đã đạt được đồng thuận số. Hợp đồng mua bán 20 tấn Robusta chính thức có hiệu lực.")
        else:
            st.warning("⏳ Trạng thái: **ĐANG CHỜ ĐỒNG THUẬN CẢ 2 BÊN**. Không một bên nào hoặc Admin có thể tự ý đóng giao dịch.")

# ========================================================
# TAB 3: BẢO MẬT & KIỂM TOÁN TIDECLOAK
# ========================================================
with tab_security:
    st.subheader("Cổng Giám Sát Phân Quyền & Bảo Mật (Tide Security Gate)")
    
    st.markdown("#### 1. Kiểm thử chống can thiệp đơn phương (Security Test)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🚨 Thử Admin Bypass (Cố tình chốt đơn mà không có 2 chữ ký)"):
            st.error("❌ **BỊ TỪ CHỐI BỞI TIDECLOAK:** Vi phạm chính sách No Unilateral Control! Admin không có khóa ký của người dùng.")
    with col_t2:
        if st.button("🛑 Thu hồi thỏa thuận (Emergency Revoke)"):
            st.session_state.negotiation['seller_signed'] = False
            st.session_state.negotiation['buyer_signed'] = False
            st.warning("🔒 Toàn bộ thỏa thuận và quyền truy cập tạm thời của AI đã bị thu hồi.")
            st.rerun()
            
    st.markdown("---")
    st.markdown("#### 2. Nhật ký truy cập minh bạch (Audit Trail)")
    audit_data = [
        {"Thời gian": str(datetime.datetime.now().strftime("%H:%M:%S")), "Tác nhân": "Seller Lâm Viên", "Hành động": "Đăng tải listing LST-01", "Kết quả": "Công khai"},
        {"Thời gian": str(datetime.datetime.now().strftime("%H:%M:%S")), "Tác nhân": "Buyer Mekong Fresh", "Hành động": "Đề xuất giá $2000", "Kết quả": "Chờ thương lượng"},
        {"Thời gian": str(datetime.datetime.now().strftime("%H:%M:%S")), "Tác nhân": "Tide Consensus Gate", "Hành động": "Kiểm tra chữ ký 2 bên", "Kết quả": "Đang thực thi"}
    ]
    st.table(pd.DataFrame(audit_data))

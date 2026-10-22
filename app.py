import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="TrustGate AI - Smart Negotiation", layout="wide", page_icon="🤝")

# 1. KHỞI TẠO STATE
if "current_user" not in st.session_state:
    st.session_state.current_user = {
        "name": "Trần Thu Hà",
        "org": "Nông sản Lâm Viên",
        "role": "Seller (Việt Nam)"
    }

if "market_items" not in st.session_state:
    st.session_state.market_items = [
        {"id": "LST-VN-01", "type": "BÁN", "owner": "Nông sản Lâm Viên (VN)", "product": "Cà phê Robusta S16", "quantity": "20 tấn", "price": 2150, "location": "Đức Trọng, Lâm Đồng"},
        {"id": "DMD-KH-01", "type": "MUA", "owner": "Mekong Fresh Trading (KH)", "product": "Cà phê Robusta S16", "quantity": "20 tấn", "price": 2000, "location": "Cửa khẩu Mộc Bài / Phnom Penh"},
        {"id": "LST-VN-02", "type": "BÁN", "owner": "Hồ tiêu Chư Sê (VN)", "product": "Hồ tiêu đen 500g/l", "quantity": "10 tấn", "price": 4200, "location": "Gia Lai"}
    ]

if "active_deal" not in st.session_state:
    st.session_state.active_deal = None

# Header và Chuyển đổi tài khoản (Giả lập để dễ quay video demo)
st.title("🌾 TrustGate AI — Sàn Thương Lượng Nông Sản Đa Bên")
st.caption("Mô hình kiểm soát truy cập phân tán: Không ai nắm quyền kiểm soát đơn phương (Powered by TideCloak)")

with st.sidebar:
    st.header("👤 Tài Khoản Đang Đăng Nhập")
    user_choice = st.radio(
        "Chuyển vai trò thử nghiệm:",
        ["Bên Bán: Trần Thu Hà (Lâm Viên - VN)", "Bên Mua: Sok Dara (Mekong Fresh - KH)"]
    )
    if "Lâm Viên" in user_choice:
        st.session_state.current_user = {"name": "Trần Thu Hà", "org": "Nông sản Lâm Viên", "role": "Seller (Việt Nam)"}
    else:
        st.session_state.current_user = {"name": "Sok Dara", "org": "Mekong Fresh Trading", "role": "Buyer (Campuchia)"}
    
    st.info(f"**Đang đóng vai:** {st.session_state.current_user['name']}\n\n**Tổ chức:** {st.session_state.current_user['org']}\n\n**Vai trò:** {st.session_state.current_user['role']}")
    
    st.divider()
    st.markdown("### 🧪 Phím Tắt Demo")
    if st.button("🔄 Đặt lại toàn bộ giao dịch"):
        st.session_state.active_deal = None
        st.rerun()

# Chia 3 Tab chính
tab_market, tab_deal, tab_security = st.tabs([
    "🛒 1. Sàn Thị Trường Chung (Pool)", 
    "💬 2. Phòng Thương Lượng Giá", 
    "🛡️ 3. Cổng Bảo Mật TideCloak"
])

# ========================================================
# TAB 1: SÀN THỊ TRƯỜNG CHUNG
# ========================================================
with tab_market:
    st.subheader("Pool Hàng Hóa & Nhu Cầu Thị Trường")
    st.write("Đăng tải nhu cầu hoặc chọn một tin niêm yết để bắt đầu mở phiên đàm phán.")
    
    with st.expander("➕ Đăng Tin Mới Lên Thị Trường", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        p_type = c1.selectbox("Loại bài đăng", ["BÁN (Listing)", "MUA (Demand)"])
        p_prod = c2.text_input("Tên hàng hóa", "Cà phê Robusta nhân xanh")
        p_qty = c3.text_input("Khối lượng", "20 tấn")
        p_price = c4.number_input("Mức giá chào (USD/tấn)", min_value=100, value=2100)
        
        if st.button("Đăng lên sàn chung"):
            new_id = f"POST-{len(st.session_state.market_items)+1}"
            st.session_state.market_items.append({
                "id": new_id,
                "type": "BÁN" if "BÁN" in p_type else "MUA",
                "owner": f"{st.session_state.current_user['org']} ({st.session_state.current_user['role'][:2]})",
                "product": p_prod,
                "quantity": p_qty,
                "price": p_price,
                "location": "Việt Nam / Campuchia"
            })
            st.success("Đã đăng tin thành công!")
            st.rerun()

    st.write("---")
    # Hiển thị danh sách card hàng hóa
    for idx, item in enumerate(st.session_state.market_items):
        col_info, col_act = st.columns([4, 1])
        with col_info:
            tag_color = "🟢 BÁN" if item['type'] == "BÁN" else "🔵 CẦN MUA"
            st.markdown(f"**[{tag_color}] {item['product']}** — Số lượng: **{item['quantity']}** | Giá mong muốn: **${item['price']}/tấn**")
            st.caption(f"Đăng bởi: {item['owner']} | Địa điểm: {item['location']} | Mã: {item['id']}")
        with col_act:
            if st.button("🤝 Thương lượng", key=f"deal_btn_{idx}"):
                # Tạo phòng thương lượng mới
                st.session_state.active_deal = {
                    "deal_id": f"DR-2026-{idx+1}",
                    "product": item['product'],
                    "quantity": item['quantity'],
                    "seller_org": "Nông sản Lâm Viên (VN)",
                    "buyer_org": "Mekong Fresh Trading (KH)",
                    "seller_price": 2150, # Giá bên bán đưa ra
                    "buyer_price": 2000,  # Giá bên mua trả
                    "ai_invoked": False,
                    "ai_price": None,
                    "final_price": None,
                    "seller_signed": False,
                    "buyer_signed": False
                }
                st.success("Đã mở phòng thương lượng! Chuyển sang Tab 2.")
        st.divider()

# ========================================================
# TAB 2: PHÒNG THƯƠNG LƯỢNG GIÁ (NGƯỜI TỰ ĐÀM PHÁN -> AI)
# ========================================================
with tab_deal:
    deal = st.session_state.active_deal
    if not deal:
        st.info("Chưa có phiên thương lượng nào được kích hoạt. Hãy chọn một mặt hàng từ **Tab 1: Sàn Thị Trường**.")
    else:
        st.subheader(f"Phòng Giao Dịch: {deal['seller_org']} ↔ {deal['buyer_org']}")
        st.markdown(f"**Mặt hàng đàm phán:** {deal['product']} | **Sản lượng:** {deal['quantity']}")
        
        c_left, c_right = st.columns([1, 1])
        
        # BÊN TRÁI: HAI BÊN TỰ TRẢ GIÁ
        with c_left:
            st.markdown("### 1. Hai Bên Tự Đưa Ra Mức Giá")
            st.write("Hai bên tự điều chỉnh mức giá kỳ vọng trước khi quyết định nhờ AI can thiệp.")
            
            c_s_price, c_b_price = st.columns(2)
            with c_s_price:
                st.markdown("**Giá Bên Bán (Lâm Viên):**")
                new_seller_price = st.number_input("USD/tấn (Seller)", value=deal['seller_price'], step=10, key="inp_s_p")
                if new_seller_price != deal['seller_price']:
                    deal['seller_price'] = new_seller_price
                    deal['seller_signed'] = False
                    deal['buyer_signed'] = False
            
            with c_b_price:
                st.markdown("**Giá Bên Mua (Mekong Fresh):**")
                new_buyer_price = st.number_input("USD/tấn (Buyer)", value=deal['buyer_price'], step=10, key="inp_b_p")
                if new_buyer_price != deal['buyer_price']:
                    deal['buyer_price'] = new_buyer_price
                    deal['seller_signed'] = False
                    deal['buyer_signed'] = False

            price_diff = deal['seller_price'] - deal['buyer_price']
            
            if price_diff == 0:
                st.success("🎯 **Hai bên đã tìm được tiếng nói chung!** Giá hai bên đưa ra trùng khớp.")
                deal['final_price'] = deal['seller_price']
            elif price_diff > 0:
                st.warning(f"⚠️ **Bất đồng giá:** Người bán muốn giá cao hơn Người mua **${price_diff}/tấn**. Chưa thể chốt hợp đồng.")
            else:
                st.info("Bên mua đang trả giá cao hơn giá chào của bên bán.")
                deal['final_price'] = deal['seller_price']

            st.markdown("---")
            # KHU VỰC GỌI AI KHI BẾ TẮC
            st.markdown("### 2. Bất Đồng Quan Điểm? Nhờ AI Hỗ Trợ")
            st.caption("AI hoạt động như trọng tài độc lập, tính toán chi phí vận chuyển để đề xuất giá tối ưu cho 2 bên.")
            
            if st.button("🤖 Kích hoạt AI Đề Xuất Giá Trung Gian"):
                deal['ai_invoked'] = True
                # Thuật toán tính giá cân bằng có tính cước vận chuyển đường bộ $35/tấn
                shipping = 35
                optimal = (deal['seller_price'] + deal['buyer_price']) / 2 + (shipping / 2)
                deal['ai_price'] = round(optimal, 1)
                deal['final_price'] = deal['ai_price']
                st.rerun()
                
            if deal['ai_invoked']:
                st.info(f"💡 **AI Khuyến Nghị Chốt:** **${deal['ai_price']}/tấn**\n\n*Phân tích:* Mức giá này giúp bên bán có lợi nhuận, đồng thời nằm trong trần thanh toán và chia sẻ 50% chi phí vận chuyển cho bên mua.")

        # BÊN PHẢI: CHỐT HỢP ĐỒNG BẰNG TIDECLOAK
        with c_right:
            st.markdown("### 3. Phê Duyệt Chốt Thỏa Thuận (Tide Dual-Consensus)")
            st.caption("Hợp đồng chỉ có hiệu lực pháp lý khi cả 2 bên cùng ký xác nhận mức giá cuối cùng.")
            
            target_price = deal['final_price'] if deal['final_price'] else deal['seller_price']
            st.metric("Mức Giá Dự Kiến Chốt", f"${target_price} / tấn")
            
            col_sign_s, col_sign_b = st.columns(2)
            with col_sign_s:
                if not deal['seller_signed']:
                    if st.button("✍️ Người Bán Ký Phê Duyệt"):
                        deal['seller_signed'] = True
                        st.rerun()
                else:
                    st.success("✅ Người bán đã ký")
                    
            with col_sign_b:
                if not deal['buyer_signed']:
                    if st.button("✍️ Người Mua Ký Phê Duyệt"):
                        deal['buyer_signed'] = True
                        st.rerun()
                else:
                    st.success("✅ Người mua đã ký")
            
            st.markdown("---")
            st.markdown("#### Trạng thái hiệu lực của thỏa thuận:")
            if deal['seller_signed'] and deal['buyer_signed']:
                st.balloons()
                st.success(f"🎉 **GIAO DỊCH CHÍNH THỨC THÀNH CÔNG Ở MỨC GIÁ ${target_price}/TẤN!**")
                st.write("Hai bên đã hoàn tất chữ ký số qua TideCloak. Dữ liệu hợp đồng đã được xác thực an toàn.")
            else:
                st.error("🔒 **TRẠNG THÁI: CHƯA ĐỦ ĐỒNG THUẬN (FAIL-CLOSED)**")
                st.caption("Chính sách TideCloak: Bất kể AI đề xuất gì hoặc người dùng tự nhập giá, nếu thiếu chữ ký của 1 trong 2 bên, hợp đồng hoàn toàn không có hiệu lực.")

# ========================================================
# TAB 3: BẢO MẬT & KIỂM TOÁN TIDECLOAK
# ========================================================
with tab_security:
    st.subheader("Cổng Giám Sát Phân Quyền & Kiểm Thử Bảo Mật (TideCloak Enforcement)")
    
    st.markdown("#### Kiểm thử khả năng ngăn chặn can thiệp đơn phương")
    c_sec1, c_sec2 = st.columns(2)
    with c_sec1:
        if st.button("🚨

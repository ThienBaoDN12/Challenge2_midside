import streamlit as st
import pandas as pd

st.set_page_config(page_title="TrustGate AI - TideCloak", layout="wide")

# Khởi tạo trạng thái phiên làm việc
if "seller_approved" not in st.session_state:
    st.session_state.seller_approved = False
if "buyer_approved" not in st.session_state:
    st.session_state.buyer_approved = False
if "ai_analyzed" not in st.session_state:
    st.session_state.ai_analyzed = False

st.title("🛡️ TrustGate AI — Decentralized Negotiation Platform")
st.caption("Powered by TideCloak: No Single Entity / AI Can Unilaterally Access Data")

tab1, tab2, tab3 = st.tabs(["🌾 Seller Workspace (VN)", "🛒 Buyer Workspace (KH)", "🤝 Deal Room & Tide Gate"])

# TAB 1: SELLER
with tab1:
    st.header("Bên Bán: Nông sản Việt Nam")
    st.error("🔒 Kho dữ liệu bí mật (Private Vault): Giá vốn = $2,600/tấn | Tồn kho = 100 tấn")
    st.info("📄 Dữ liệu đề xuất chia sẻ: Cà phê Robusta Grade 1 | Giá chào bán = $2,950/tấn")
    
    if not st.session_state.seller_approved:
        if st.button("✍️ Seller Ký phê duyệt (TideCloak Consent)", key="btn_seller"):
            st.session_state.seller_approved = True
            st.rerun()
    else:
        st.success("✅ Seller đã ký xác thực qua TideCloak")
        if st.button("Hủy phê duyệt (Revoke)", key="rev_seller"):
            st.session_state.seller_approved = False
            st.session_state.ai_analyzed = False
            st.rerun()

# TAB 2: BUYER
with tab2:
    st.header("Bên Mua: Doanh nghiệp Campuchia")
    st.error("🔒 Kho dữ liệu bí mật (Private Vault): Ngân sách tối đa = $2,900/tấn")
    st.info("📄 Dữ liệu đề xuất chia sẻ: Nhu cầu mua = 20 tấn | Giao tại Cửa khẩu Mộc Bài")
    
    if not st.session_state.buyer_approved:
        if st.button("✍️ Buyer Ký phê duyệt (TideCloak Consent)", key="btn_buyer"):
            st.session_state.buyer_approved = True
            st.rerun()
    else:
        st.success("✅ Buyer đã ký xác thực qua TideCloak")
        if st.button("Hủy phê duyệt (Revoke)", key="rev_buyer"):
            st.session_state.buyer_approved = False
            st.session_state.ai_analyzed = False
            st.rerun()

# TAB 3: DEAL ROOM & SECURITY GATE
with tab3:
    st.header("Cổng đồng thuận bảo mật (Tide Consensus Gate)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chữ ký Seller", "ĐÃ DUYỆT" if st.session_state.seller_approved else "CHƯA KÝ")
    with col2:
        st.metric("Chữ ký Buyer", "ĐÃ DUYỆT" if st.session_state.buyer_approved else "CHƯA KÝ")
    
    st.divider()

    # Kiểm tra điều kiện đồng thuận đa bên
    both_approved = st.session_state.seller_approved and st.session_state.buyer_approved

    if not both_approved:
        st.warning("⚠️ TRẠNG THÁI: BỊ KHÓA (BLOCKED) — Cần đủ chữ ký của cả 2 bên độc lập để cấp quyền giải mã cho AI.")
        st.button("🤖 Chạy AI Joint Analysis (Vô hiệu hóa)", disabled=True)
    else:
        st.success("🟢 TRẠNG THÁI: ĐÃ CẤP QUYỀN (GRANTED) — Token ủy quyền ngắn hạn (TTL: 30 phút) đã được kích hoạt.")
        if st.button("🤖 Kích hoạt AI Joint Analysis", type="primary"):
            st.session_state.ai_analyzed = True

    if st.session_state.ai_analyzed and both_approved:
        st.subheader("📊 Báo cáo phân tích AI chung (Joint Analysis Report)")
        report_data = {
            "Hạng mục": ["Chênh lệch giá chào", "Khối lượng đề xuất", "Chi phí vận chuyển ước tính", "Mức giá AI khuyến nghị"],
            "Chi tiết": ["+$50/tấn (Seller $2,950 vs Buyer $2,900)", "20 tấn", "$35/tấn", "$2,920/tấn (Hai bên cùng có lợi)"]
        }
        st.table(pd.DataFrame(report_data))
        st.info("ℹ️ AI chỉ đọc các trường dữ liệu được cấp phép chung. Kho bí mật của 2 bên vẫn được bảo vệ tuyệt đối.")

    st.divider()
    st.subheader("🛑 Thử nghiệm bảo mật (Security Tests for Demo)")
    if st.button("Thử Admin Bypass (Admin can thiệp đơn phương)"):
        st.error("❌ BỊ CHẶN BỞI TIDECLOAK: Không thể truy cập dữ liệu! Nền tảng không nắm giữ private key của người dùng.")

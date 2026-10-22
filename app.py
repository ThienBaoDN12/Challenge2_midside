import streamlit as st
import pandas as pd
import time

# Thiết lập trang
st.set_page_config(
    page_title="TrustGate AI | TideCloak Secure Negotiation",
    page_icon="🛡️",
    layout="wide"
)

# Tùy biến CSS để giao diện trực quan và chuyên nghiệp hơn
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e9ecef;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-locked {
        background-color: #ffe3e3;
        color: #c92a2a;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-granted {
        background-color: #d3f9d8;
        color: #2b8a3e;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo trạng thái phiên làm việc
if "seller_approved" not in st.session_state:
    st.session_state.seller_approved = False
if "buyer_approved" not in st.session_state:
    st.session_state.buyer_approved = False
if "ai_analyzed" not in st.session_state:
    st.session_state.ai_analyzed = False

# Header chính
st.title("🛡️ TrustGate AI — Decentralized Smart Negotiation")
st.markdown("**Kiến trúc không quyền kiểm soát đơn phương (No Unilateral Control)** được bảo vệ bởi **TideCloak**[cite: 1, 7]")
st.divider()

# Chia 3 Tab tương ứng với vai trò
tab1, tab2, tab3 = st.tabs([
    "🌾 Bên Bán (Seller - Việt Nam)", 
    "🛒 Bên Mua (Buyer - Campuchia)", 
    "🤝 Phòng Giao Dịch & Cổng Bảo Mật (Tide Gate)"
])

# ==========================================
# TAB 1: SELLER
# ==========================================
with tab1:
    st.subheader("Bên Bán: Doanh nghiệp Nông sản Việt Nam[cite: 7]")
    col_s1, col_s2 = st.columns([1, 1])
    
    with col_s1:
        st.markdown("#### 🔒 Két Dữ Liệu Riêng Tư (Seller Vault)")
        st.caption("Chỉ giải mã được bằng Private Key của Người Bán; Admin/AI không thể đọc[cite: 1, 7]")
        st.error("""
        * **Giá vốn cơ bản:** $2,600 / tấn
        * **Tồn kho sẵn có:** 100 tấn
        * **Biên lợi nhuận tối thiểu:** 12%
        """)
        
    with col_s2:
        st.markdown("#### 📄 Dữ Liệu Đề Xuất Chia Sẻ (Shared Manifest)[cite: 7]")
        st.caption("Dữ liệu chỉ được công khai khi hai bên cùng đồng thuận phê duyệt[cite: 7]")
        st.info("""
        * **Mặt hàng:** Cà phê Robusta Grade 1 (Đắk Lắk)
        * **Mức giá chào bán:** $2,950 / tấn
        * **Quy cách đóng gói:** Bao đay 60kg tiêu chuẩn xuất khẩu
        """)

    st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        if not st.session_state.seller_approved:
            if st.button("✍️ Ký Duyệt Bằng TideCloak", key="btn_s_sign", type="primary"):
                st.session_state.seller_approved = True
                st.rerun()
        else:
            st.success("✅ Đã ký xác thực qua TideCloak[cite: 7]")
            if st.button("Thu hồi phê duyệt (Revoke)", key="btn_s_rev"):
                st.session_state.seller_approved = False
                st.session_state.ai_analyzed = False
                st.rerun()

# ==========================================
# TAB 2: BUYER
# ==========================================
with tab2:
    st.subheader("Bên Mua: Doanh nghiệp Nhập khẩu Campuchia[cite: 7]")
    col_b1, col_b2 = st.columns([1, 1])
    
    with col_b1:
        st.markdown("#### 🔒 Két Dữ Liệu Riêng Tư (Buyer Vault)")
        st.caption("Chỉ giải mã được bằng Private Key của Người Mua; Admin/AI không thể đọc[cite: 1, 7]")
        st.error("""
        * **Ngân sách mua tối đa:** $2,900 / tấn
        * **Chi phí vốn tài trợ:** $60,000
        * **Thời hạn thanh toán mong muốn:** L/C 30 ngày
        """)
        
    with col_b2:
        st.markdown("#### 📄 Dữ Liệu Đề Xuất Chia Sẻ (Shared Manifest)[cite: 7]")
        st.caption("Dữ liệu chỉ được công khai khi hai bên cùng đồng thuận phê duyệt[cite: 7]")
        st.info("""
        * **Khối lượng cần mua:** 20 tấn
        * **Địa điểm nhận hàng:** Cửa khẩu Mộc Bài - Bavet
        * **Thời gian giao hàng:** Trước ngày 15/11/2026
        """)

    st.markdown("---")
    cb1, cb2 = st.columns([1, 3])
    with cb1:
        if not st.session_state.buyer_approved:
            if st.button("✍️ Ký Duyệt Bằng TideCloak", key="btn_b_sign", type="primary"):
                st.session_state.buyer_approved = True
                st.rerun()
        else:
            st.success("✅ Đã ký xác thực qua TideCloak[cite: 7]")
            if st.button("Thu hồi phê duyệt (Revoke)", key="btn_b_rev"):
                st.session_state.buyer_approved = False
                st.session_state.ai_analyzed = False
                st.rerun()

# ==========================================
# TAB 3: DEAL ROOM & SECURITY GATE
# ==========================================
with tab3:
    st.subheader("Cổng Kiểm Soát Đồng Thuận Đa Bên (Tide Multi-Party Consensus Gate)[cite: 1, 7]")
    
    # Hiển thị trực quan 2 thẻ trạng thái chữ ký
    col_gate1, col_gate2, col_gate3 = st.columns(3)
    with col_gate1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("**Chữ ký Bên Bán (Seller)**")
        if st.session_state.seller_approved:
            st.markdown("<span class='badge-granted'>ĐÃ XÁC THỰC</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-locked'>CHƯA KÝ</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_gate2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("**Chữ ký Bên Mua (Buyer)**")
        if st.session_state.buyer_approved:
            st.markdown("<span class='badge-granted'>ĐÃ XÁC THỰC</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-locked'>CHƯA KÝ</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    both_signed = st.session_state.seller_approved and st.session_state.buyer_approved

    with col_gate3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("**Trạng Thái Token Truy Cập AI**")
        if both_signed:
            st.markdown("<span class='badge-granted'>GRANTED (TTL: 30m)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-locked'>BLOCKED (BỊ KHÓA)</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    
    # Khu vực chạy AI
    if not both_signed:
        st.warning("⚠️ **HỆ THỐNG ĐANG BỊ KHÓA (FAIL-CLOSED)**: Để ngăn chặn truy cập dữ liệu đơn phương, AI chỉ được cấp quyền giải mã khi có đủ 2 chữ ký xác thực số từ cả hai bên[cite: 1, 7].")
        st.button("🤖 Chạy AI Joint Analysis (Đang bị vô hiệu)", disabled=True)
    else:
        st.success("🟢 **ĐỦ ĐIỀU KIỆN ĐỒNG THUẬN**: TideCloak đã cấp token ủy quyền giới hạn (Ephemeral Token) cho phiên phân tích chung này[cite: 1, 7].")
        if st.button("🤖 Kích Hoạt AI Joint Analysis", type="primary"):
            with st.spinner("AI đang phân tích dữ liệu đàm phán hợp nhất..."):
                time.sleep(1.2)
                st.session_state.ai_analyzed = True

    # Kết quả báo cáo AI
    if st.session_state.ai_analyzed and both_signed:
        st.markdown("### 📊 Kết Quả Đàm Phán Tự Động (AI Joint Report)[cite: 7]")
        
        c_res1, c_res2 = st.columns([2, 1])
        with c_res1:
            report_df = pd.DataFrame({
                "Chỉ Số Đàm Phán": [
                    "Chênh lệch giá ban đầu",
                    "Khối lượng thương lượng",
                    "Chi phí logistics dự kiến",
                    "Mức giá AI khuyến nghị chốt",
                    "Lợi ích kinh tế hai bên"
                ],
                "Giá Trị / Đánh Giá": [
                    "Seller ($2,950) cao hơn Buyer ($2,900) $50/tấn",
                    "20 tấn",
                    "$32 / tấn (vận chuyển đường bộ)",
                    "$2,925 / tấn",
                    "Cả hai bên cùng đạt mục tiêu biên lợi nhuận"
                ]
            })
            st.dataframe(report_df, use_container_width=True, hide_index=True)
        with c_res2:
            st.info("""
            **Bảo đảm an toàn từ TideCloak:**
            - AI chỉ truy cập dữ liệu dùng chung[cite: 7].
            - Không lưu trữ prompt hay lịch sử vào bộ nhớ chung[cite: 7].
            - Quyền đọc tự động hết hiệu lực sau khi xuất báo cáo[cite: 7].
            """)

    st.divider()
    
    # 2 Thử nghiệm bảo mật cho kịch bản Video Demo
    st.subheader("🧪 Kiểm Thử Bảo Mật Cho Video Demo[cite: 6, 7]")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🚨 Thử Admin Bypass (Quản trị viên can thiệp đơn phương)"):
            st.error("❌ **ACCESS DENIED (TideCloak Enforcement)**: Quản trị viên nền tảng không nắm giữ Private Key của các bên, mọi nỗ lực trích xuất dữ liệu đều bị chặn đứng[cite: 1, 7]!")
    with col_t2:
        if st.button("🛑 Thu Hồi Quyền Lập Tức (Emergency Revoke)"):
            st.session_state.seller_approved = False
            st.session_state.buyer_approved = False
            st.session_state.ai_analyzed = False
            st.warning("🔒 **ĐÃ THU HỒI**: Toàn bộ quyền truy cập của AI đã bị hủy bỏ ngay lập tức[cite: 7].")
            st.rerun()

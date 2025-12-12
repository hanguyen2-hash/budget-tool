import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Agency Resource Estimator", layout="wide")

st.title("🤖 Project Hours Estimator (Dynamic Multi-Option)")
st.caption("So sánh nhiều kịch bản Budget và Staff Hours cùng lúc")
st.markdown("---")

# --- 2. KHAI BÁO HỆ SỐ MÔ HÌNH (THE BRAIN) ---
# (Giữ nguyên logic của bạn)
MODEL_COEFFICIENTS = {
    "Delivery Chief": {
        "Intercept": 1.5, "guaranteed_creators": 0.02, "duration_weeks": 0.05,
        "Client_Difficulty_Rating": 0.1, "vn_vetting_yes": 0.0, "Sector_Public": 0.2
    },
    "Acct Supervisor US": {
        "Intercept": 2.0, "guaranteed_creators": 0.05, "duration_weeks": 0.08,
        "Client_Difficulty_Rating": 0.15, "vn_vetting_yes": 0.1, "Sector_Public": 0.0
    },
    "Acct Manager US": {
        "Intercept": 3.2, "guaranteed_creators": 0.1, "duration_weeks": 0.12,
        "Client_Difficulty_Rating": 0.2, "vn_vetting_yes": 0.0, "Sector_Public": 0.1
    },
    "Assistant SA": {
        "Intercept": 3.0, "guaranteed_creators": 0.15, "duration_weeks": 0.1,
        "Client_Difficulty_Rating": 0.05, "vn_vetting_yes": 0.3, "Sector_Public": 0.0
    },
    "Tech Prod Head": {
        "Intercept": 0.5, "guaranteed_creators": 0.01, "duration_weeks": 0.02,
        "Client_Difficulty_Rating": 0.0, "vn_vetting_yes": 0.0, "Sector_Public": 0.0
    }
}

# --- 3. QUẢN LÝ SESSION STATE (BỘ NHỚ ĐỘNG) ---
if 'budgets' not in st.session_state:
    # Tạo sẵn 1 Option mặc định khi mở app
    st.session_state.budgets = [{
        'id': 0, 'name': 'Option 1',
        'money': 125000, 'creators': 5, 'duration': 14,
        'client_diff': 3, 'mgmt_diff': 3, 'sector': 'General', 'vetting': 'No'
    }]

if 'next_id' not in st.session_state:
    st.session_state.next_id = 1

def add_budget():
    new_id = st.session_state.next_id
    st.session_state.budgets.append({
        'id': new_id, 'name': f'Option {len(st.session_state.budgets) + 1}',
        'money': 0, 'creators': 5, 'duration': 12,
        'client_diff': 3, 'mgmt_diff': 3, 'sector': 'General', 'vetting': 'No'
    })
    st.session_state.next_id += 1

def delete_budget(index):
    st.session_state.budgets.pop(index)

# --- 4. ENGINE TÍNH TOÁN (ĐÃ SỬA ĐỂ NHẬN INPUT DYNAMIC) ---
def calculate_hours_for_option(coeffs, inputs):
    # inputs là một dictionary chứa thông số của option đó
    linear_y = coeffs.get("Intercept", 0)
    
    # Cộng biến số
    linear_y += coeffs.get("guaranteed_creators", 0) * inputs['creators']
    linear_y += coeffs.get("duration_weeks", 0) * inputs['duration']
    linear_y += coeffs.get("Client_Difficulty_Rating", 0) * inputs['client_diff']
    linear_y += coeffs.get("Influencer_Management_Difficulty_Rating", 0) * inputs['mgmt_diff']
    
    # Cộng biến Dummy (Sector)
    sector_key = f"Sector_{inputs['sector']}"
    if sector_key in coeffs:
        linear_y += coeffs[sector_key]
        
    # Cộng biến Dummy (Vetting)
    if inputs['vetting'] == "Yes":
        linear_y += coeffs.get("vn_vetting_yes", 0)
        
    return np.exp(linear_y)

# --- 5. SIDEBAR: NHẬP LIỆU CHO TỪNG OPTION ---
with st.sidebar:
    st.header("🎚️ Project Parameters")
    st.button("➕ Add New Option", on_click=add_budget, use_container_width=True)
    st.divider()

    # Vòng lặp tạo input cho từng Option
    for i, budget in enumerate(st.session_state.budgets):
        unique_id = budget['id']
        
        with st.expander(f"📂 {budget['name']}", expanded=(i==0)): # Chỉ mở cái đầu tiên
            # Đổi tên Option
            budget['name'] = st.text_input("Name", value=budget['name'], key=f"name_{unique_id}")
            
            # Nhập tiền & Số lượng
            col_a, col_b = st.columns(2)
            with col_a:
                budget['money'] = st.number_input("Budget ($)", value=budget['money'], step=5000, key=f"money_{unique_id}")
            with col_b:
                budget['creators'] = st.number_input("Creators", value=budget['creators'], step=1, key=f"creat_{unique_id}")
            
            budget['duration'] = st.number_input("Duration (Weeks)", value=budget['duration'], key=f"dur_{unique_id}")
            
            st.markdown("---")
            st.caption("Advanced Factors")
            
            # Các biến độ khó & Sector
            budget['client_diff'] = st.slider("Client Difficulty", 1, 5, budget['client_diff'], key=f"cdiff_{unique_id}")
            budget['mgmt_diff'] = st.slider("Mgmt Difficulty", 1, 5, budget['mgmt_diff'], key=f"mdiff_{unique_id}")
            budget['sector'] = st.selectbox("Sector", ["General", "Public", "Tech", "Consumer"], index=["General", "Public", "Tech", "Consumer"].index(budget['sector']), key=f"sec_{unique_id}")
            budget['vetting'] = st.selectbox("VN Vetting?", ["No", "Yes"], index=["No", "Yes"].index(budget['vetting']), key=f"vet_{unique_id}")
            
            # Nút Xóa
            if len(st.session_state.budgets) > 1:
                st.button("🗑️ Delete", key=f"del_{unique_id}", on_click=delete_budget, args=(i,), type="primary")

# --- 6. HIỂN THỊ KẾT QUẢ (MAIN AREA) ---
if not st.session_state.budgets:
    st.warning("Please add an option from the sidebar.")
    st.stop()

# Chia cột hiển thị
cols = st.columns(len(st.session_state.budgets))

for i, budget in enumerate(st.session_state.budgets):
    with cols[i]:
        # --- BƯỚC TÍNH TOÁN ---
        total_hours_option = 0
        breakdown = []
        
        # Chạy vòng lặp qua từng Role trong Model Coefficients
        for role, coeffs in MODEL_COEFFICIENTS.items():
            hours = calculate_hours_for_option(coeffs, budget) # Gọi hàm tính toán mới
            total_hours_option += hours
            breakdown.append({"Role": role, "Hours": round(hours, 1)})
            
        est_cost = total_hours_option * 100 # Giả định rate $100
        
        # --- BƯỚC HIỂN THỊ (CARD STYLE) ---
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
            <div style="background-color: #D32F2F; padding: 10px;">
                <h4 style="color: white; text-align: center; margin: 0;">{budget['name']}</h4>
                <h2 style="color: white; text-align: center; margin: 0;">${budget['money']:,.0f}</h2>
            </div>
            <div style="padding: 15px; background-color: #f9f9f9;">
                <p><strong>👥 Creators:</strong> {budget['creators']}</p>
                <p><strong>⏳ Duration:</strong> {budget['duration']} weeks</p>
                <p style="font-size: 0.8em; color: gray;">Sector: {budget['sector']} | Vetting: {budget['vetting']}</p>
                <hr>
                <h3 style="text-align: center; color: #1b5e20;">
                    {total_hours_option:,.1f} Hours
                </h3>
                <p style="text-align: center; font-size: 0.8em; color: gray;">Est. Internal Cost: ${est_cost:,.0f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hiển thị bảng chi tiết (Expandable)
        with st.expander("📊 Role Breakdown"):
            df_breakdown = pd.DataFrame(breakdown)
            # Dùng st.dataframe đơn giản để tránh lỗi matplotlib
            st.dataframe(df_breakdown, hide_index=True, use_container_width=True)
            
            # Vẽ biểu đồ nhỏ
            st.bar_chart(df_breakdown.set_index("Role"))

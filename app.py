import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Agency Resource Estimator", layout="wide")

st.title("🤖 Project Hours Estimator (Tabs View)")
st.caption("Quản lý chi tiết từng kịch bản ngân sách")
st.markdown("---")

# --- 2. KHAI BÁO HỆ SỐ MÔ HÌNH (GIỮ NGUYÊN) ---
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

# --- 3. QUẢN LÝ SESSION STATE ---
if 'budgets' not in st.session_state:
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

# --- 4. ENGINE TÍNH TOÁN ---
def calculate_hours_for_option(coeffs, inputs):
    linear_y = coeffs.get("Intercept", 0)
    linear_y += coeffs.get("guaranteed_creators", 0) * inputs['creators']
    linear_y += coeffs.get("duration_weeks", 0) * inputs['duration']
    linear_y += coeffs.get("Client_Difficulty_Rating", 0) * inputs['client_diff']
    linear_y += coeffs.get("Influencer_Management_Difficulty_Rating", 0) * inputs['mgmt_diff']
    
    sector_key = f"Sector_{inputs['sector']}"
    if sector_key in coeffs:
        linear_y += coeffs[sector_key]
        
    if inputs['vetting'] == "Yes":
        linear_y += coeffs.get("vn_vetting_yes", 0)
        
    return np.exp(linear_y)

# --- 5. SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("🎚️ Project Parameters")
    st.button("➕ Add New Option", on_click=add_budget, use_container_width=True)
    st.divider()

    for i, budget in enumerate(st.session_state.budgets):
        unique_id = budget['id']
        with st.expander(f"📂 {budget['name']}", expanded=(i==0)):
            budget['name'] = st.text_input("Name", value=budget['name'], key=f"name_{unique_id}")
            
            col_a, col_b = st.columns(2)
            with col_a:
                budget['money'] = st.number_input("Budget ($)", value=budget['money'], step=5000, key=f"money_{unique_id}")
            with col_b:
                budget['creators'] = st.number_input("Creators", value=budget['creators'], step=1, key=f"creat_{unique_id}")
            
            budget['duration'] = st.number_input("Duration (Weeks)", value=budget['duration'], key=f"dur_{unique_id}")
            
            st.caption("Advanced Settings")
            budget['client_diff'] = st.slider("Client Diff", 1, 5, budget['client_diff'], key=f"cdiff_{unique_id}")
            budget['mgmt_diff'] = st.slider("Mgmt Diff", 1, 5, budget['mgmt_diff'], key=f"mdiff_{unique_id}")
            budget['sector'] = st.selectbox("Sector", ["General", "Public", "Tech", "Consumer"], index=["General", "Public", "Tech", "Consumer"].index(budget['sector']), key=f"sec_{unique_id}")
            budget['vetting'] = st.selectbox("VN Vetting?", ["No", "Yes"], index=["No", "Yes"].index(budget['vetting']), key=f"vet_{unique_id}")
            
            if len(st.session_state.budgets) > 1:
                st.button("🗑️ Delete", key=f"del_{unique_id}", on_click=delete_budget, args=(i,), type="primary")

# --- 6. KHU VỰC HIỂN THỊ (TAB VIEW) ---
if not st.session_state.budgets:
    st.warning("Please add an option from the sidebar.")
    st.stop()

# Lấy danh sách tên các Tabs từ dữ liệu
tab_names = [b['name'] for b in st.session_state.budgets]
tabs = st.tabs(tab_names) # Tạo Tabs động

# Lặp qua từng Tab để hiển thị nội dung
for tab, budget in zip(tabs, st.session_state.budgets):
    with tab:
        # --- BƯỚC TÍNH TOÁN ---
        total_hours_option = 0
        breakdown = []
        
        for role, coeffs in MODEL_COEFFICIENTS.items():
            hours = calculate_hours_for_option(coeffs, budget)
            total_hours_option += hours
            breakdown.append({"Role": role, "Hours": round(hours, 1)})
            
        est_cost = total_hours_option * 100 
        
        # --- HIỂN THỊ CARD TỔNG QUAN ---
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #333;">${budget['money']:,.0f}</h2>
                    <p style="margin: 0; color: #666;">Total Budget</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; color: #D32F2F;">{total_hours_option:,.1f} Hours</h2>
                    <p style="margin: 0; color: #666;">Est. Staff Time (Internal Cost: ${est_cost:,.0f})</p>
                </div>
            </div>
            <hr>
            <div style="display: flex; gap: 30px;">
                <span><strong>👥 Creators:</strong> {budget['creators']}</span>
                <span><strong>⏳ Duration:</strong> {budget['duration']} Weeks</span>
                <span><strong>🏭 Sector:</strong> {budget['sector']}</span>
                <span><strong>🔎 Vetting:</strong> {budget['vetting']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- HIỂN THỊ CHI TIẾT (BẢNG + BIỂU ĐỒ) ---
        col1, col2 = st.columns([1, 2]) # Chia cột lệch (Bảng nhỏ, Biểu đồ to)
        
        df_breakdown = pd.DataFrame(breakdown)
        
        with col1:
            st.subheader("📋 Role Breakdown")
            # Highlight các role tốn nhiều giờ nhất
            st.dataframe(
                df_breakdown.style.background_gradient(cmap="Reds", subset=["Hours"]),
                use_container_width=True,
                hide_index=True
            )
            
        with col2:
            st.subheader("📊 Visualization")
            st.bar_chart(df_breakdown.set_index("Role"))

import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Agency Resource Estimator", layout="wide")

st.title("🤖 Project Hours Estimator (Compare Mode)")
st.caption("So sánh tổng quan và xem chi tiết từng kịch bản")
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

# Hàm phụ trợ để tính tổng giờ cho 1 budget (để dùng cho Summary)
def get_total_hours(budget):
    total = 0
    for role, coeffs in MODEL_COEFFICIENTS.items():
        total += calculate_hours_for_option(coeffs, budget)
    return total

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

# --- 6. MAIN AREA: TẠO TABS ---
if not st.session_state.budgets:
    st.warning("Please add an option from the sidebar.")
    st.stop()

# Tạo danh sách tên tab: Tab đầu là Summary, các tab sau là tên Option
tab_names = ["📊 COMPARE ALL"] + [b['name'] for b in st.session_state.budgets]
tabs = st.tabs(tab_names)

# --- TAB 1: SUMMARY / COMPARISON ---
with tabs[0]:
    st.subheader("Leaderboard Summary")
    
    # 1. Gom dữ liệu để so sánh
    summary_data = []
    for budget in st.session_state.budgets:
        t_hours = get_total_hours(budget)
        est_cost = t_hours * 100 # Internal Cost giả định
        
        # Tính ROI giả định (Ví dụ: Reach / Staff Cost)
        # Giả sử reach = creators * 15000
        est_reach = budget['creators'] * 15000 
        efficiency = est_reach / t_hours if t_hours > 0 else 0
        
        summary_data.append({
            "Option Name": budget['name'],
            "Total Budget": budget['money'],
            "Total Staff Hours": round(t_hours, 1),
            "Internal Cost ($)": round(est_cost, 0),
            "Creators": budget['creators'],
            "Duration (Wks)": budget['duration']
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # 2. Hiển thị Bảng so sánh
    st.dataframe(
        df_summary,
        column_config={
            "Total Budget": st.column_config.NumberColumn(format="$%d"),
            "Internal Cost ($)": st.column_config.NumberColumn(format="$%d"),
            "Total Staff Hours": st.column_config.ProgressColumn(
                "Staff Load", 
                format="%.1f hrs", 
                min_value=0, 
                max_value=max(df_summary["Total Staff Hours"])*1.2
            ),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # 3. Biểu đồ so sánh trực quan
    col1, col2 = st.columns(2)
    with col1:
        st.caption("💰 Budget Comparison")
        st.bar_chart(df_summary.set_index("Option Name")["Total Budget"], color="#4CAF50")
    with col2:
        st.caption("⏱️ Staff Hours Comparison")
        st.bar_chart(df_summary.set_index("Option Name")["Total Staff Hours"], color="#D32F2F")

# --- CÁC TAB CHI TIẾT (DETAIL TABS) ---
# Duyệt qua các tabs còn lại (từ index 1 trở đi) tương ứng với từng budget
for i, budget in enumerate(st.session_state.budgets):
    with tabs[i + 1]: # +1 vì tab 0 là Summary
        
        # --- TÍNH TOÁN CHI TIẾT ---
        total_hours_option = 0
        breakdown = []
        
        for role, coeffs in MODEL_COEFFICIENTS.items():
            hours = calculate_hours_for_option(coeffs, budget)
            total_hours_option += hours
            breakdown.append({"Role": role, "Hours": round(hours, 1)})
            
        est_cost = total_hours_option * 100 
        
        # --- VISUAL CARD ---
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
            <h3 style="margin-top:0; color: #333;">Details for: {budget['name']}</h3>
            <div style="display: flex; gap: 40px; margin-top: 15px;">
                <div>
                    <span style="font-size: 24px; font-weight: bold; color: #2E7D32;">${budget['money']:,.0f}</span><br>
                    <span style="color: gray;">Budget</span>
                </div>
                <div>
                    <span style="font-size: 24px; font-weight: bold; color: #C62828;">{total_hours_option:,.1f}</span><br>
                    <span style="color: gray;">Staff Hours</span>
                </div>
                 <div>
                    <span style="font-size: 24px; font-weight: bold; color: #1565C0;">{budget['creators']}</span><br>
                    <span style="color: gray;">Creators</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- BẢNG & BIỂU ĐỒ ---
        c1, c2 = st.columns([1, 1])
        df_breakdown = pd.DataFrame(breakdown)
        
        with c1:
            st.write("##### 📋 Breakdown by Role")
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
            
        with c2:
            st.write("##### 📊 Visual")
            st.bar_chart(df_breakdown.set_index("Role"))

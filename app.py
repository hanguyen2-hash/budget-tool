import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Agency Budget Proposal", layout="wide")

st.title("🤖 Agency Budget Proposal Generator")
st.caption("Tạo báo giá và ước tính giờ nhân sự tự động")
st.markdown("---")

# --- 2. HỆ SỐ MÔ HÌNH (GIỮ NGUYÊN) ---
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
    # Option 1 mặc định giống ảnh
    st.session_state.budgets = [{
        'id': 0, 'name': 'OPTION 1',
        'money': 125000, 'creators': 27, 'duration': 14,
        'client_diff': 3, 'mgmt_diff': 3, 'sector': 'General', 'vetting': 'No'
    }]

if 'next_id' not in st.session_state:
    st.session_state.next_id = 1

def add_budget():
    new_id = st.session_state.next_id
    st.session_state.budgets.append({
        'id': new_id, 'name': f'OPTION {len(st.session_state.budgets) + 1}',
        'money': 250000, 'creators': 63, 'duration': 14,
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🎚️ Project Settings")
    st.button("➕ Add Comparison Option", on_click=add_budget, use_container_width=True)
    st.divider()

    for i, budget in enumerate(st.session_state.budgets):
        unique_id = budget['id']
        with st.expander(f"📂 {budget['name']}", expanded=(i==0)):
            budget['name'] = st.text_input("Name", value=budget['name'], key=f"name_{unique_id}")
            budget['money'] = st.number_input("Budget ($)", value=budget['money'], step=5000, key=f"money_{unique_id}")
            budget['creators'] = st.number_input("Creators", value=budget['creators'], step=1, key=f"creat_{unique_id}")
            budget['duration'] = st.number_input("Duration (Weeks)", value=budget['duration'], key=f"dur_{unique_id}")
            
            st.caption("Advanced Factors")
            budget['client_diff'] = st.slider("Client Diff", 1, 5, budget['client_diff'], key=f"cdiff_{unique_id}")
            budget['mgmt_diff'] = st.slider("Mgmt Diff", 1, 5, budget['mgmt_diff'], key=f"mdiff_{unique_id}")
            budget['sector'] = st.selectbox("Sector", ["General", "Public", "Tech", "Consumer"], index=["General", "Public", "Tech", "Consumer"].index(budget['sector']), key=f"sec_{unique_id}")
            budget['vetting'] = st.selectbox("VN Vetting?", ["No", "Yes"], index=["No", "Yes"].index(budget['vetting']), key=f"vet_{unique_id}")
            
            if len(st.session_state.budgets) > 1:
                st.button("🗑️ Delete", key=f"del_{unique_id}", on_click=delete_budget, args=(i,), type="primary")

# --- 6. MAIN DISPLAY (TABS) ---
if not st.session_state.budgets:
    st.warning("Please add an option from the sidebar.")
    st.stop()

tab_names = ["📊 EXECUTIVE SUMMARY"] + [f"🔎 {b['name']} Details" for b in st.session_state.budgets]
tabs = st.tabs(tab_names)

# === TAB 1: SUMMARY GIỐNG ẢNH ===
with tabs[0]:
    # Tạo cột động dựa trên số lượng option
    cols = st.columns(len(st.session_state.budgets))
    
    for i, budget in enumerate(st.session_state.budgets):
        with cols[i]:
            # --- TÍNH TOÁN SỐ LIỆU ---
            # 1. Staff Hours
            total_hours = 0
            breakdown_html = ""
            for role, coeffs in MODEL_COEFFICIENTS.items():
                hrs = calculate_hours_for_option(coeffs, budget)
                total_hours += hrs
                # Tạo dòng nhỏ cho từng role trong phần Note xanh
                breakdown_html += f"<div><small>{role}: {int(hrs)} hrs</small></div>"
            
            internal_cost = total_hours * 100 # Giả định rate
            
            # 2. Metrics giả lập (dựa trên creators & budget)
            est_reach = budget['creators'] * 14000 # Giả định
            est_impr = est_reach * 4.3 
            cogs_influencer = budget['money'] * 0.3 # 30% trả cho KOL
            cogs_boosting = budget['money'] * 0.15 # 15% chạy Ads
            margin = budget['money'] - cogs_influencer - cogs_boosting - internal_cost
            margin_pct = (margin / budget['money']) * 100 if budget['money'] > 0 else 0

            # --- RENDER HTML CARD (GIỐNG HỆT ẢNH) ---
            st.markdown(f"""
            <div style="background-color: #D32F2F; color: white; padding: 10px; text-align: center; border-radius: 5px 5px 0 0;">
                <h3 style="margin:0; color: white;">{budget['name']}</h3>
                <h1 style="margin:0; font-size: 32px; color: white;">${budget['money']:,.0f}</h1>
                <small>discounted from ${budget['money']*1.1:,.0f} market value</small>
            </div>

            <div style="background-color: white; padding: 15px; border: 1px solid #ddd; border-top: none;">
                <h5 style="margin-top:0;">Minimum guarantee</h5>
                <p><strong>{budget['creators']}+</strong> <span style="color:gray">social posts & stories</span></p>
                <p><strong>{int(est_reach):,}+</strong> <span style="color:gray">est. reach (not impressions)</span></p>
                <p><strong>{int(est_impr):,}+</strong> <span style="color:gray">est. impressions</span></p>
                <p><strong>{max(1, int(budget['creators']/3))}+</strong> <span style="color:gray">trusted messengers</span></p>
            </div>

            <div style="background-color: #E8F5E9; padding: 15px; border: 1px solid #ddd; margin-top: -1px;">
                <h5 style="margin-top:0; color: #D32F2F;">NOTE for Delivery Team</h5>
                <p style="margin-bottom: 5px;"><strong>{int(total_hours)} est. Agency staff hours</strong></p>
                <div style="padding-left: 10px; color: #555; margin-bottom: 10px;">
                    {breakdown_html}
                </div>
                <small>• Avg IG follower: 19,500</small><br>
                <small>• CPM (boosting): $31.47</small>
            </div>

            <div style="background-color: #FFF3E0; padding: 15px; border: 1px solid #ddd; margin-top: -1px; border-radius: 0 0 5px 5px;">
                <h5 style="margin-top:0; color: #D32F2F;">DEAL MARGIN Analysis</h5>
                
                <div style="display: flex; justify-content: space-between;">
                    <span>Campaign Fee</span>
                    <strong>${budget['money']:,.0f}</strong>
                </div>
                
                <div style="display: flex; justify-content: space-between; color: #555;">
                    <span>COGS - Boosting</span>
                    <span>-${cogs_boosting:,.0f}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; color: #555;">
                    <span>COGS - Influencers</span>
                    <span>-${cogs_influencer:,.0f}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; color: #555;">
                    <span>Internal Staff Cost</span>
                    <span>-${internal_cost:,.0f}</span>
                </div>
                
                <hr style="margin: 5px 0;">
                
                <div style="display: flex; justify-content: space-between;">
                    <strong>NET EARNINGS</strong>
                    <strong style="color: #2E7D32;">${margin:,.0f}</strong>
                </div>
                 <div style="display: flex; justify-content: space-between;">
                    <span>Margin %</span>
                    <strong style="color: #D32F2F;">{margin_pct:.1f}%</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

# === CÁC TAB CHI TIẾT (GIỮ NGUYÊN CODE CŨ) ===
for i, budget in enumerate(st.session_state.budgets):
    with tabs[i + 1]:
        # Tính toán lại để hiển thị biểu đồ chi tiết
        total_hours_option = 0
        breakdown = []
        for role, coeffs in MODEL_COEFFICIENTS.items():
            hours = calculate_hours_for_option(coeffs, budget)
            total_hours_option += hours
            breakdown.append({"Role": role, "Hours": round(hours, 1)})
            
        st.subheader(f"📊 Detailed Breakdown: {budget['name']}")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.dataframe(pd.DataFrame(breakdown), use_container_width=True, hide_index=True)
        with c2:
            st.bar_chart(pd.DataFrame(breakdown).set_index("Role"))

import streamlit as st
import pandas as pd
import numpy as np
import textwrap

st.set_page_config(page_title="Multi-Platform Budget", layout="wide")

# --- 1. DATABASE GIÁ & METRICS (Giữ nguyên) ---
PRICING_DB = {
    "Nano (1k-10k)": {
        "IG": {"flw": 3258, "post": 268.22, "story": 160.24},
        "TT": {"flw": 4373, "video": 184.57},
        "X":  {"flw": 4952, "tweet": 131.34}
    },
    "Micro (10k-50k)": {
        "IG": {"flw": 21417, "post": 443.84, "story": 301.84},
        "TT": {"flw": 25013, "video": 335.92},
        "X":  {"flw": 21765, "tweet": 207.33}
    },
    "Mid (50k-150k)": {
        "IG": {"flw": 87664, "post": 1140.22, "story": 783.57},
        "TT": {"flw": 90230, "video": 697.04},
        "X":  {"flw": 85206, "tweet": 504.20}
    },
    "Macro (150k-500k)": {
        "IG": {"flw": 264830, "post": 3315.63, "story": 2260.49},
        "TT": {"flw": 275338, "video": 1806.50},
        "X":  {"flw": 266771, "tweet": 1490.99}
    },
    "Mega (500k+)": {
        "IG": {"flw": 2206768, "post": 11059.85, "story": 7525.33},
        "TT": {"flw": 2087679, "video": 5757.25},
        "X":  {"flw": 1838483, "tweet": 4656.37}
    }
}

# --- 2. HÀM TÍNH TOÁN (ĐÃ UPDATE .get() ĐỂ TRÁNH LỖI KHI ẨN CỘT) ---
def calculate_multi_platform_cost(df):
    total_cost = 0
    total_reach = 0
    total_creators = 0
    breakdown = {"IG": 0, "TT": 0, "X": 0} 

    for _, row in df.iterrows():
        tier = row['Tier']
        data = PRICING_DB[tier]

        # Sử dụng .get('Column Name', 0) để nếu cột bị ẩn thì mặc định là 0
        
        # --- INSTAGRAM ---
        qty_ig = row.get('Qty IG', 0)
        if qty_ig > 0:
            posts = row.get('IG Posts', 0)
            stories = row.get('IG Stories', 0)
            cost_one_ig = (data['IG']['post'] * posts) + (data['IG']['story'] * stories)
            total_cost += cost_one_ig * qty_ig
            total_reach += data['IG']['flw'] * qty_ig
            total_creators += qty_ig
            breakdown["IG"] += cost_one_ig * qty_ig

        # --- TIKTOK ---
        qty_tt = row.get('Qty TikTok', 0)
        if qty_tt > 0:
            videos = row.get('TT Videos', 0)
            cost_one_tt = data['TT']['video'] * videos
            total_cost += cost_one_tt * qty_tt
            total_reach += data['TT']['flw'] * qty_tt
            total_creators += qty_tt
            breakdown["TT"] += cost_one_tt * qty_tt

        # --- X (TWITTER) ---
        qty_x = row.get('Qty X', 0)
        if qty_x > 0:
            tweets = row.get('X Tweets', 0)
            cost_one_x = data['X']['tweet'] * tweets
            total_cost += cost_one_x * qty_x
            total_reach += data['X']['flw'] * qty_x
            total_creators += qty_x
            breakdown["X"] += cost_one_x * qty_x
            
    return total_creators, total_cost, total_reach, breakdown

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🤖 Smart Budget Generator")
st.markdown("---")

col_sidebar, col_main = st.columns([1.2, 2])

with col_sidebar:
    st.header("⚙️ Configuration")
    
    # 1. CHỌN CHANNEL (TÍNH NĂNG MỚI)
    st.subheader("1. Select Active Channels")
    platforms = st.multiselect(
        "Choose platforms for this campaign:",
        ["Instagram", "TikTok", "X (Twitter)"],
        default=["Instagram", "TikTok"] # Mặc định chọn 2 cái phổ biến
    )
    
    st.divider()
    
    # 2. BUDGET INPUT
    st.subheader("2. Financials")
    campaign_fee = st.number_input("Total Client Budget ($)", value=125000, step=5000)

    st.divider()
    st.info("👇 Customize quantity in the table below")

# --- 4. DATA EDITOR ĐỘNG (DYNAMIC) ---
# Tạo Dataframe gốc chứa tất cả các cột có thể có
base_data = [
    {"Tier": "Nano (1k-10k)",     "Qty IG": 3, "IG Posts": 2, "IG Stories": 1, "Qty TikTok": 1, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Micro (10k-50k)",   "Qty IG": 1, "IG Posts": 2, "IG Stories": 1, "Qty TikTok": 1, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Mid (50k-150k)",    "Qty IG": 1, "IG Posts": 2, "IG Stories": 0, "Qty TikTok": 1, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Macro (150k-500k)", "Qty IG": 0, "IG Posts": 1, "IG Stories": 1, "Qty TikTok": 0, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Mega (500k+)",      "Qty IG": 0, "IG Posts": 1, "IG Stories": 1, "Qty TikTok": 0, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
]
full_df = pd.DataFrame(base_data)

# XÂY DỰNG DANH SÁCH CỘT CẦN HIỂN THỊ DỰA TRÊN LỰA CHỌN
visible_cols = ["Tier"]
column_config_dynamic = {
    "Tier": st.column_config.TextColumn("Tier", disabled=True, width="medium"),
}

if "Instagram" in platforms:
    visible_cols.extend(["Qty IG", "IG Posts", "IG Stories"])
    column_config_dynamic.update({
        "Qty IG": st.column_config.NumberColumn("IG 👤", min_value=0, help="Số lượng Creator IG"),
        "IG Posts": st.column_config.NumberColumn("Post/p", min_value=0),
        "IG Stories": st.column_config.NumberColumn("Story/p", min_value=0),
    })

if "TikTok" in platforms:
    visible_cols.extend(["Qty TikTok", "TT Videos"])
    column_config_dynamic.update({
        "Qty TikTok": st.column_config.NumberColumn("TT 👤", min_value=0, help="Số lượng Creator TikTok"),
        "TT Videos": st.column_config.NumberColumn("Vid/p", min_value=0),
    })

if "X (Twitter)" in platforms:
    visible_cols.extend(["Qty X", "X Tweets"])
    column_config_dynamic.update({
        "Qty X": st.column_config.NumberColumn("X 👤", min_value=0, help="Số lượng Creator X"),
        "X Tweets": st.column_config.NumberColumn("Tweet/p", min_value=0),
    })

# HIỂN THỊ BẢNG ĐÃ LỌC CỘT
# Lưu ý: Chúng ta lọc cột của dataframe TRƯỚC khi đưa vào data_editor
edited_df = st.data_editor(
    full_df[visible_cols], # Chỉ lấy các cột user đã chọn
    column_config=column_config_dynamic,
    hide_index=True,
    use_container_width=True,
    key="matrix_editor"
)

# --- 5. TÍNH TOÁN KẾT QUẢ ---
# Hàm tính toán sẽ nhận dataframe chỉ có các cột hiển thị, 
# nhưng nhờ lệnh .get() bên trong hàm, nó sẽ coi các cột thiếu là 0
total_creators, cogs_influencer, total_reach, breakdown = calculate_multi_platform_cost(edited_df)

cogs_boosting = campaign_fee * 0.15
staff_hours = 100 + (total_creators * 3)
internal_cost = staff_hours * 100

total_cogs = cogs_influencer + cogs_boosting + internal_cost
margin = campaign_fee - total_cogs
margin_pct = (margin / campaign_fee * 100) if campaign_fee > 0 else 0
margin_color = "#2E7D32" if margin >= 0 else "#D32F2F"

# --- 6. HIỂN THỊ KẾT QUẢ ---
with col_main:
    # Card HTML hiển thị (đã xử lý textwrap)
    html_content = textwrap.dedent(f"""
        <div style="background-color: #FFF8E1; padding: 20px; border-radius: 10px; border: 1px solid #FFECB3; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin:0; color: #F57F17;">Proposal Analysis</h2>
                <div style="text-align: right;">
                    <span style="font-size: 2em; font-weight: bold; color: {margin_color}">${margin:,.0f}</span><br>
                    <span style="color: {margin_color}; font-weight: bold;">{margin_pct:.1f}% Margin</span>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="background: white; padding: 15px; border-radius: 8px;">
                    <strong style="color: #555;">REVENUE</strong>
                    <h3 style="margin: 5px 0;">${campaign_fee:,.0f}</h3>
                    <small style="color: gray;">Client Budget</small>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px;">
                    <strong style="color: #555;">TOTAL COST</strong>
                    <h3 style="margin: 5px 0; color: #D32F2F;">-${total_cogs:,.0f}</h3>
                    <small style="color: gray;">Influencers + Ads + Staff</small>
                </div>
            </div>

            <hr style="border: 0; border-top: 1px dashed #ccc; margin: 20px 0;">

            <h4 style="margin-top:0;">💰 Cost Breakdown</h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Influencers (Net)</span>
                <strong>${cogs_influencer:,.0f}</strong>
            </div>
            <div style="padding-left: 15px; font-size: 0.9em; color: #666; margin-bottom: 10px; border-left: 3px solid #eee;">
                {f"<div>• Instagram: ${breakdown['IG']:,.0f}</div>" if breakdown['IG']>0 else ""}
                {f"<div>• TikTok: ${breakdown['TT']:,.0f}</div>" if breakdown['TT']>0 else ""}
                {f"<div>• X (Twitter): ${breakdown['X']:,.0f}</div>" if breakdown['X']>0 else ""}
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Boosting (Ads)</span>
                <strong>${cogs_boosting:,.0f}</strong>
            </div>
             <div style="display: flex; justify-content: space-between;">
                <span>Internal Staff</span>
                <strong>${internal_cost:,.0f}</strong>
            </div>
        </div>
    """)
    
    clean_html = "\n".join([line.strip() for line in html_content.split("\n")])
    st.markdown(clean_html, unsafe_allow_html=True)
    
    st.write("") # Spacer

    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Creators", total_creators)
    m2.metric("Est. Total Reach", f"{int(total_reach):,}")
    cpm = (cogs_influencer/total_reach*1000) if total_reach > 0 else 0
    m3.metric("CPM (Content)", f"${cpm:.2f}")

    # Chart
    if cogs_influencer > 0:
        st.subheader("Platform Spend")
        # Lọc chart data chỉ hiển thị platform có chi phí > 0
        chart_data = []
        if breakdown['IG'] > 0: chart_data.append({"Platform": "Instagram", "Cost": breakdown['IG']})
        if breakdown['TT'] > 0: chart_data.append({"Platform": "TikTok", "Cost": breakdown['TT']})
        if breakdown['X'] > 0: chart_data.append({"Platform": "X (Twitter)", "Cost": breakdown['X']})
        
        if chart_data:
            st.bar_chart(pd.DataFrame(chart_data), x="Platform", y="Cost", color="#F57F17")

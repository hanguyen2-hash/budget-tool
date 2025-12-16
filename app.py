import streamlit as st
import pandas as pd
import numpy as np
import textwrap

st.set_page_config(page_title="Multi-Platform Budget", layout="wide")

# --- 1. DATABASE GIÁ & METRICS (Dữ liệu từ ảnh Excel của bạn) ---
# Đơn vị: USD
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

# --- 2. HÀM TÍNH TOÁN ĐA NỀN TẢNG ---
def calculate_multi_platform_cost(df):
    total_cost = 0
    total_reach = 0
    total_creators = 0
    
    breakdown = {"IG": 0, "TT": 0, "X": 0} # Để vẽ biểu đồ nếu cần

    for _, row in df.iterrows():
        tier = row['Tier']
        data = PRICING_DB[tier]

        # --- TÍNH TOÁN CHO INSTAGRAM ---
        qty_ig = row['Qty IG']
        if qty_ig > 0:
            cost_one_ig = (data['IG']['post'] * row['IG Posts']) + (data['IG']['story'] * row['IG Stories'])
            total_cost += cost_one_ig * qty_ig
            total_reach += data['IG']['flw'] * qty_ig
            total_creators += qty_ig
            breakdown["IG"] += cost_one_ig * qty_ig

        # --- TÍNH TOÁN CHO TIKTOK ---
        qty_tt = row['Qty TikTok']
        if qty_tt > 0:
            cost_one_tt = data['TT']['video'] * row['TT Videos']
            total_cost += cost_one_tt * qty_tt
            total_reach += data['TT']['flw'] * qty_tt
            total_creators += qty_tt
            breakdown["TT"] += cost_one_tt * qty_tt

        # --- TÍNH TOÁN CHO X (TWITTER) ---
        qty_x = row['Qty X']
        if qty_x > 0:
            cost_one_x = data['X']['tweet'] * row['X Tweets']
            total_cost += cost_one_x * qty_x
            total_reach += data['X']['flw'] * qty_x
            total_creators += qty_x
            breakdown["X"] += cost_one_x * qty_x
            
    return total_creators, total_cost, total_reach, breakdown

# --- 3. GIAO DIỆN ---
st.title("🤖 Precision Budget Generator")
st.caption("Multi-platform pricing based on provided rate card.")
st.markdown("---")

col_sidebar, col_main = st.columns([1, 2])

with col_sidebar:
    st.subheader("1. Campaign Settings")
    campaign_fee = st.number_input("Total Client Budget ($)", value=125000, step=5000)
    
    st.divider()
    st.subheader("2. Influencer Matrix")
    st.info("👇 Enter quantity & deliverables per platform below")

# --- 4. DATA EDITOR CHÍNH (MA TRẬN) ---
# Tạo dữ liệu mặc định khớp với ảnh "FOR CAMPAIGN - INITIAL" bạn gửi
    default_mix = pd.DataFrame([
        {
            "Tier": "Nano (1k-10k)", 
            "Qty IG": 3, "IG Posts": 2, "IG Stories": 1, 
            "Qty TikTok": 1, "TT Videos": 2,
            "Qty X": 0, "X Tweets": 0
        },
        {
            "Tier": "Micro (10k-50k)", 
            "Qty IG": 1, "IG Posts": 2, "IG Stories": 1, 
            "Qty TikTok": 1, "TT Videos": 2,
            "Qty X": 0, "X Tweets": 0
        },
        {
            "Tier": "Mid (50k-150k)", 
            "Qty IG": 1, "IG Posts": 2, "IG Stories": 0, 
            "Qty TikTok": 1, "TT Videos": 2,
            "Qty X": 0, "X Tweets": 0
        },
        {
            "Tier": "Macro (150k-500k)", 
            "Qty IG": 0, "IG Posts": 1, "IG Stories": 1, 
            "Qty TikTok": 0, "TT Videos": 1,
            "Qty X": 0, "X Tweets": 0
        },
        {
            "Tier": "Mega (500k+)", 
            "Qty IG": 0, "IG Posts": 1, "IG Stories": 1, 
            "Qty TikTok": 0, "TT Videos": 1,
            "Qty X": 0, "X Tweets": 0
        },
    ])

    # Cấu hình bảng nhập liệu để dễ nhìn hơn
    edited_df = st.data_editor(
        default_mix,
        column_config={
            "Tier": st.column_config.TextColumn("Tier", disabled=True, width="medium"),
            "Qty IG": st.column_config.NumberColumn("IG 👤", min_value=0, help="Number of Instagram Creators"),
            "IG Posts": st.column_config.NumberColumn("Post/p", min_value=0, help="Posts per person"),
            "IG Stories": st.column_config.NumberColumn("Story/p", min_value=0, help="Stories per person"),
            "Qty TikTok": st.column_config.NumberColumn("TT 👤", min_value=0, help="Number of TikTok Creators"),
            "TT Videos": st.column_config.NumberColumn("Vid/p", min_value=0, help="Videos per person"),
            "Qty X": st.column_config.NumberColumn("X 👤", min_value=0, help="Number of X Creators"),
            "X Tweets": st.column_config.NumberColumn("Tweet/p", min_value=0, help="Tweets per person"),
        },
        hide_index=True,
        use_container_width=True,
        height=300
    )

# --- 5. TÍNH TOÁN & HIỂN THỊ ---
total_creators, cogs_influencer, total_reach, breakdown = calculate_multi_platform_cost(edited_df)

# Các chi phí khác
cogs_boosting = campaign_fee * 0.15
# Staff Cost: Giả sử mỗi creator tốn 5h quản lý, mỗi platform thêm độ khó
staff_hours = 100 + (total_creators * 3) 
internal_cost = staff_hours * 100

total_cogs = cogs_influencer + cogs_boosting + internal_cost
margin = campaign_fee - total_cogs
margin_pct = (margin / campaign_fee * 100) if campaign_fee > 0 else 0
margin_color = "#2E7D32" if margin >= 0 else "#D32F2F"

# Render kết quả
with col_main:
    # 1. HTML Card Summary
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
                <div>• Instagram: ${breakdown['IG']:,.0f}</div>
                <div>• TikTok: ${breakdown['TT']:,.0f}</div>
                <div>• X (Twitter): ${breakdown['X']:,.0f}</div>
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

    # 2. Performance Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Creators", total_creators, help="Tổng số KOLs huy động")
    m2.metric("Est. Total Reach", f"{int(total_reach):,}", help="Tổng lượng follower tiếp cận")
    m3.metric("CPM (Content only)", f"${(cogs_influencer/total_reach*1000) if total_reach else 0:.2f}", help="Cost per 1000 Reach (chỉ tính phí KOL)")

    # 3. Chart phân bổ ngân sách
    st.subheader("Budget Allocation by Platform")
    if cogs_influencer > 0:
        chart_data = pd.DataFrame({
            "Platform": ["Instagram", "TikTok", "X (Twitter)"],
            "Cost": [breakdown['IG'], breakdown['TT'], breakdown['X']]
        })
        st.bar_chart(chart_data, x="Platform", y="Cost", color="#F57F17")
    else:
        st.info("Add influencers to see cost breakdown.")

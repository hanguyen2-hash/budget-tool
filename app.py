import streamlit as st
import pandas as pd
import numpy as np
import textwrap

# --- 1. CẤU HÌNH & DATA THAM CHIẾU (Dựa trên ảnh Excel của bạn) ---
st.set_page_config(page_title="Agency Budget Proposal", layout="wide")

# Database giá và follower trung bình (Lấy từ cột Instagram trong ảnh)
TIER_DATA = {
    "Nano (1k-10k)":      {"avg_flw": 3258,    "price_post": 268,   "price_story": 160},
    "Micro (10k-50k)":    {"avg_flw": 21417,   "price_post": 443,   "price_story": 301},
    "Mid (50k-150k)":     {"avg_flw": 87664,   "price_post": 1140,  "price_story": 783},
    "Macro (150k-500k)":  {"avg_flw": 264830,  "price_post": 3315,  "price_story": 2260},
    "Mega (500k+)":       {"avg_flw": 2206768, "price_post": 11059, "price_story": 7525}
}

# --- 2. HÀM TÍNH TOÁN (LOGIC MỚI) ---
def calculate_mix_metrics(mix_df):
    """Tính toán tổng hợp dựa trên bảng phân bổ"""
    total_creators = 0
    total_cost_influencer = 0
    total_reach_raw = 0
    
    for index, row in mix_df.iterrows():
        tier = row['Tier']
        qty = row['Quantity']
        posts = row['Posts/Infl']
        stories = row['Stories/Infl']
        
        if qty > 0:
            ref = TIER_DATA[tier]
            
            # 1. Tính Cost (COGS Influencer)
            cost_per_person = (ref['price_post'] * posts) + (ref['price_story'] * stories)
            total_cost_influencer += cost_per_person * qty
            
            # 2. Tính Reach (Giả định Reach = Follower * Qty)
            # Lưu ý: Bạn có thể nhân thêm hệ số reach rate (ví dụ 0.3) nếu muốn
            total_reach_raw += (ref['avg_flw'] * qty)
            
            total_creators += qty
            
    return total_creators, total_cost_influencer, total_reach_raw

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🤖 Budget Generator (Tier-based)")
st.markdown("---")

# --- SIDEBAR: CẤU HÌNH PLAN ---
with st.sidebar:
    st.header("🎚️ Campaign Input")
    
    # INPUT 1: Tổng ngân sách khách hàng trả (Fee)
    campaign_budget = st.number_input("Total Client Budget ($)", value=125000, step=5000)
    
    st.divider()
    st.subheader("Influencer Mix Strategy")
    
    # INPUT 2: Bảng nhập liệu Mix (Thay thế cho các slider đơn lẻ)
    # Tạo dữ liệu mặc định ban đầu
    default_data = pd.DataFrame([
        {"Tier": "Nano (1k-10k)",     "Quantity": 4, "Posts/Infl": 2, "Stories/Infl": 1},
        {"Tier": "Micro (10k-50k)",   "Quantity": 2, "Posts/Infl": 2, "Stories/Infl": 1},
        {"Tier": "Mid (50k-150k)",    "Quantity": 1, "Posts/Infl": 1, "Stories/Infl": 1},
        {"Tier": "Macro (150k-500k)", "Quantity": 0, "Posts/Infl": 1, "Stories/Infl": 0},
        {"Tier": "Mega (500k+)",      "Quantity": 0, "Posts/Infl": 1, "Stories/Infl": 0},
    ])
    
    # Hiển thị bảng cho người dùng sửa
    edited_df = st.data_editor(
        default_data,
        column_config={
            "Tier": st.column_config.TextColumn("Tier", disabled=True), # Không cho sửa tên Tier
            "Quantity": st.column_config.NumberColumn("Qty Creators", min_value=0, step=1),
            "Posts/Infl": st.column_config.NumberColumn("Posts/Inf", min_value=0, step=1),
            "Stories/Infl": st.column_config.NumberColumn("Stories/Inf", min_value=0, step=1),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.caption("Edit the table above to configure the mix.")

# --- 4. TÍNH TOÁN KẾT QUẢ TỪ BẢNG ---
# Gọi hàm tính toán
total_creators, est_cogs_influencer, est_reach = calculate_mix_metrics(edited_df)

# Các chi phí khác (Giữ nguyên logic cũ hoặc chỉnh sửa tùy ý)
est_cogs_boosting = campaign_budget * 0.15  # 15% cho Ads
est_impr = est_reach * 1.5                  # Giả định Impression = 1.5 * Reach (hoặc số khác)

# Tính Staff Hours (Logic cũ - đơn giản hóa)
# Vì logic cũ dùng hệ số hồi quy phức tạp, ở đây mình tạm tính đơn giản để demo luồng
# Bạn có thể map lại vào hàm hồi quy cũ nếu cần
est_staff_hours = 100 + (total_creators * 2.5) 
internal_cost = est_staff_hours * 100 

# Tính Margin
total_cogs = est_cogs_influencer + est_cogs_boosting + internal_cost
margin = campaign_budget - total_cogs
margin_pct = (margin / campaign_budget * 100) if campaign_budget > 0 else 0
margin_color = "#2E7D32" if margin >= 0 else "#D32F2F"

# --- 5. HIỂN THỊ KẾT QUẢ (CARD HTML) ---
# Dùng textwrap.dedent + strip như đã hướng dẫn trước đó để không bị lỗi hiển thị
html_content = textwrap.dedent(f"""
    <div style="background-color: #FFF3E0; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
        <h3 style="margin-top:0; color: #D32F2F; text-align: center;">DEAL MARGIN ANALYSIS</h3>
        <p style="text-align: center; color: gray; font-size: 0.9em;">Based on Mix: {total_creators} Creators</p>
        <hr>
        
        <div style="display: flex; justify-content: space-between;">
            <span>Campaign Fee (Revenue)</span>
            <strong>${campaign_budget:,.0f}</strong>
        </div>
        
        <div style="display: flex; justify-content: space-between; color: #555; margin-top: 10px;">
            <span>COGS - Influencers (Calculated)</span>
            <span style="color: #D32F2F">-${est_cogs_influencer:,.0f}</span>
        </div>
        <small style="color: gray; display: block; text-align: right;">(Avg cost/creator: ${est_cogs_influencer/total_creators if total_creators else 0:,.0f})</small>
        
        <div style="display: flex; justify-content: space-between; color: #555;">
            <span>COGS - Boosting (15%)</span>
            <span style="color: #D32F2F">-${est_cogs_boosting:,.0f}</span>
        </div>
        
        <div style="display: flex; justify-content: space-between; color: #555;">
            <span>Internal Staff Cost</span>
            <span style="color: #D32F2F">-${internal_cost:,.0f}</span>
        </div>
        
        <hr style="margin: 15px 0;">
        
        <div style="display: flex; justify-content: space-between; font-size: 1.2em;">
            <strong>NET EARNINGS</strong>
            <strong style="color: {margin_color};">${margin:,.0f}</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span>Margin %</span>
            <strong style="color: {margin_color};">{margin_pct:.1f}%</strong>
        </div>
    </div>
    
    <div style="margin-top: 20px; background-color: white; padding: 15px; border: 1px solid #eee; border-radius: 5px;">
        <h5 style="margin:0">Estimated Performance</h5>
        <p><strong>{int(est_reach):,}</strong> <span style="color:gray">Total Reach</span></p>
        <p><strong>{int(est_impr):,}</strong> <span style="color:gray">Est. Impressions</span></p>
    </div>
""")

clean_html = "\n".join([line.strip() for line in html_content.split("\n")])
st.markdown(clean_html, unsafe_allow_html=True)

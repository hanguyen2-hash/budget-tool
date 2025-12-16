import streamlit as st
import pandas as pd
import numpy as np
import textwrap

st.set_page_config(page_title="Dynamic Budget Tool", layout="wide")

# --- 1. CẤU HÌNH DỮ LIỆU GỐC (BASE RATE CARD) ---
# Dữ liệu từ ảnh bạn cung cấp
INITIAL_RATE_CARD = [
    {"Tier": "Nano (1k-10k)",     "IG Flw": 3258,    "IG Post ($)": 268.22,   "IG Story ($)": 160.24,  "TT Flw": 4373,    "TT Video ($)": 184.57,  "X Flw": 4952,    "X Tweet ($)": 131.34},
    {"Tier": "Micro (10k-50k)",   "IG Flw": 21417,   "IG Post ($)": 443.84,   "IG Story ($)": 301.84,  "TT Flw": 25013,   "TT Video ($)": 335.92,  "X Flw": 21765,   "X Tweet ($)": 207.33},
    {"Tier": "Mid (50k-150k)",    "IG Flw": 87664,   "IG Post ($)": 1140.22,  "IG Story ($)": 783.57,  "TT Flw": 90230,   "TT Video ($)": 697.04,  "X Flw": 85206,   "X Tweet ($)": 504.20},
    {"Tier": "Macro (150k-500k)", "IG Flw": 264830,  "IG Post ($)": 3315.63,  "IG Story ($)": 2260.49, "TT Flw": 275338,  "TT Video ($)": 1806.50, "X Flw": 266771,  "X Tweet ($)": 1490.99},
    {"Tier": "Mega (500k+)",      "IG Flw": 2206768, "IG Post ($)": 11059.85, "IG Story ($)": 7525.33, "TT Flw": 2087679, "TT Video ($)": 5757.25, "X Flw": 1838483, "X Tweet ($)": 4656.37},
]

# --- 2. HÀM CHUYỂN ĐỔI DATAFRAME -> DICTIONARY ---
# Hàm này giúp biến bảng người dùng đã sửa thành format mà hàm tính toán hiểu được
def convert_df_to_pricing_db(df):
    pricing_db = {}
    for _, row in df.iterrows():
        tier = row['Tier']
        pricing_db[tier] = {
            "IG": {"flw": row['IG Flw'], "post": row['IG Post ($)'], "story": row['IG Story ($)']},
            "TT": {"flw": row['TT Flw'], "video": row['TT Video ($)']},
            "X":  {"flw": row['X Flw'], "tweet": row['X Tweet ($)']}
        }
    return pricing_db

# --- 3. HÀM TÍNH TOÁN (CẬP NHẬT NHẬN DYNAMIC DB) ---
def calculate_cost(mix_df, pricing_db):
    total_cost = 0
    total_reach = 0
    total_creators = 0
    breakdown = {"IG": 0, "TT": 0, "X": 0}

    for _, row in mix_df.iterrows():
        tier = row['Tier']
        # Lấy data từ pricing_db mới (được tạo ra từ bảng Rate Card)
        data = pricing_db.get(tier) 
        
        if not data: continue # Skip nếu không tìm thấy tier

        # --- INSTAGRAM ---
        qty_ig = row.get('Qty IG', 0)
        if qty_ig > 0:
            posts = row.get('IG Posts', 0)
            stories = row.get('IG Stories', 0)
            cost = (data['IG']['post'] * posts) + (data['IG']['story'] * stories)
            total_cost += cost * qty_ig
            total_reach += data['IG']['flw'] * qty_ig
            total_creators += qty_ig
            breakdown["IG"] += cost * qty_ig

        # --- TIKTOK ---
        qty_tt = row.get('Qty TikTok', 0)
        if qty_tt > 0:
            videos = row.get('TT Videos', 0)
            cost = data['TT']['video'] * videos
            total_cost += cost * qty_tt
            total_reach += data['TT']['flw'] * qty_tt
            total_creators += qty_tt
            breakdown["TT"] += cost * qty_tt

        # --- X (TWITTER) ---
        qty_x = row.get('Qty X', 0)
        if qty_x > 0:
            tweets = row.get('X Tweets', 0)
            cost = data['X']['tweet'] * tweets
            total_cost += cost * qty_x
            total_reach += data['X']['flw'] * qty_x
            total_creators += qty_x
            breakdown["X"] += cost * qty_x
            
    return total_creators, total_cost, total_reach, breakdown

# --- GIAO DIỆN CHÍNH ---
st.title("🤖 Dynamic Budget Tool")
st.caption("Customize rate cards and campaign mix.")

# ==========================================
# PHẦN 1: RATE CARD SETTINGS (TÍNH NĂNG MỚI)
# ==========================================
with st.expander("⚙️ RATE CARD CONFIGURATION (Click to Expand)", expanded=True):
    c1, c2 = st.columns([1, 3])
    
    with c1:
        st.markdown("##### Global Adjustment")
        # Input % thay đổi giá
        price_adj_pct = st.number_input(
            "Price Change (%)", 
            min_value=-50.0, 
            max_value=200.0, 
            value=0.0, 
            step=5.0,
            help="Tăng/Giảm toàn bộ giá trong bảng (VD: nhập 20 để tăng giá 20%)"
        )
        
        st.info(f"Multiplier: {1 + price_adj_pct/100:.2f}x")

    with c2:
        st.markdown("##### Market Rate Table (Editable)")
        # 1. Load dữ liệu gốc
        df_rate = pd.DataFrame(INITIAL_RATE_CARD)
        
        # 2. Áp dụng Price Change (%) vào các cột giá tiền
        # Logic: Chỉ nhân % cho các cột có ký hiệu ($)
        price_cols = [c for c in df_rate.columns if "($)" in c]
        for col in price_cols:
            df_rate[col] = df_rate[col] * (1 + price_adj_pct/100)

        # 3. Hiển thị bảng Editor
        edited_rate_card = st.data_editor(
            df_rate,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Tier": st.column_config.TextColumn("Tier", disabled=True),
                "IG Post ($)": st.column_config.NumberColumn(format="$%.0f"),
                "IG Story ($)": st.column_config.NumberColumn(format="$%.0f"),
                "TT Video ($)": st.column_config.NumberColumn(format="$%.0f"),
                "X Tweet ($)": st.column_config.NumberColumn(format="$%.0f"),
            }
        )
        
        # 4. Chuyển đổi dữ liệu từ bảng Editor thành Dictionary để dùng cho tính toán
        # Điều này giúp: Nếu user sửa tay số liệu trong bảng, code sẽ dùng số đã sửa
        DYNAMIC_PRICING_DB = convert_df_to_pricing_db(edited_rate_card)

st.markdown("---")

# ==========================================
# PHẦN 2: CAMPAIGN MIX (GIỮ NGUYÊN LOGIC CŨ)
# ==========================================
col_sidebar, col_main = st.columns([1.2, 2])

with col_sidebar:
    st.header("1. Campaign Setup")
    
    platforms = st.multiselect(
        "Channels:",
        ["Instagram", "TikTok", "X (Twitter)"],
        default=["Instagram", "TikTok"]
    )
    
    campaign_fee = st.number_input("Client Budget ($)", value=125000, step=5000)
    st.divider()
    st.info("👇 Configure Quantity & Content below")

# --- DATA EDITOR CHO MIX ---
base_data = [
    {"Tier": "Nano (1k-10k)",     "Qty IG": 3, "IG Posts": 2, "IG Stories": 1, "Qty TikTok": 1, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Micro (10k-50k)",   "Qty IG": 1, "IG Posts": 2, "IG Stories": 1, "Qty TikTok": 1, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Mid (50k-150k)",    "Qty IG": 1, "IG Posts": 2, "IG Stories": 0, "Qty TikTok": 1, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Macro (150k-500k)", "Qty IG": 0, "IG Posts": 1, "IG Stories": 1, "Qty TikTok": 0, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
    {"Tier": "Mega (500k+)",      "Qty IG": 0, "IG Posts": 1, "IG Stories": 1, "Qty TikTok": 0, "TT Videos": 1, "Qty X": 0, "X Tweets": 0},
]
full_df = pd.DataFrame(base_data)

# Lọc cột hiển thị theo channel đã chọn
visible_cols = ["Tier"]
column_config_dynamic = {"Tier": st.column_config.TextColumn("Tier", disabled=True, width="medium")}

if "Instagram" in platforms:
    visible_cols.extend(["Qty IG", "IG Posts", "IG Stories"])
    column_config_dynamic.update({"Qty IG": st.column_config.NumberColumn("IG 👤"), "IG Posts": st.column_config.NumberColumn("Post/p"), "IG Stories": st.column_config.NumberColumn("Story/p")})

if "TikTok" in platforms:
    visible_cols.extend(["Qty TikTok", "TT Videos"])
    column_config_dynamic.update({"Qty TikTok": st.column_config.NumberColumn("TT 👤"), "TT Videos": st.column_config.NumberColumn("Vid/p")})

if "X (Twitter)" in platforms:
    visible_cols.extend(["Qty X", "X Tweets"])
    column_config_dynamic.update({"Qty X": st.column_config.NumberColumn("X 👤"), "X Tweets": st.column_config.NumberColumn("Tweet/p")})

edited_mix_df = st.data_editor(
    full_df[visible_cols],
    column_config=column_config_dynamic,
    hide_index=True,
    use_container_width=True,
    key="mix_editor"
)

# --- TÍNH TOÁN (DÙNG DYNAMIC_PRICING_DB) ---
total_creators, cogs_influencer, total_reach, breakdown = calculate_cost(edited_mix_df, DYNAMIC_PRICING_DB)

# Các chỉ số tài chính
cogs_boosting = campaign_fee * 0.15
internal_cost = (100 + (total_creators * 3)) * 100
total_cogs = cogs_influencer + cogs_boosting + internal_cost
margin = campaign_fee - total_cogs
margin_pct = (margin / campaign_fee * 100) if campaign_fee > 0 else 0
margin_color = "#2E7D32" if margin >= 0 else "#D32F2F"

# --- HIỂN THỊ KẾT QUẢ ---
with col_main:
    html_content = textwrap.dedent(f"""
        <div style="background-color: #FFF8E1; padding: 20px; border-radius: 10px; border: 1px solid #FFECB3;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin:0; color: #F57F17;">Proposal Analysis</h2>
                <div style="text-align: right;">
                    <span style="font-size: 2em; font-weight: bold; color: {margin_color}">${margin:,.0f}</span><br>
                    <span style="color: {margin_color}; font-weight: bold;">{margin_pct:.1f}% Margin</span>
                </div>
            </div>
            <hr>
            <div style="display: flex; justify-content: space-between;">
                <strong>TOTAL REVENUE</strong>
                <strong>${campaign_fee:,.0f}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; color: #D32F2F;">
                <span>Total Cost</span>
                <span>-${total_cogs:,.0f}</span>
            </div>
            
            <div style="background: white; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 0.9em;">
                <div style="display: flex; justify-content: space-between;">
                    <span>• Influencers Cost (Based on Rate Card)</span>
                    <strong>${cogs_influencer:,.0f}</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>• Boosting (15%)</span>
                    <strong>${cogs_boosting:,.0f}</strong>
                </div>
                 <div style="display: flex; justify-content: space-between;">
                    <span>• Internal Staff</span>
                    <strong>${internal_cost:,.0f}</strong>
                </div>
            </div>
        </div>
    """)
    
    clean_html = "\n".join([line.strip() for line in html_content.split("\n")])
    st.markdown(clean_html, unsafe_allow_html=True)
    
    st.write("")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Creators", total_creators)
    m2.metric("Total Reach", f"{int(total_reach):,}")
    cpm = (cogs_influencer/total_reach*1000) if total_reach > 0 else 0
    m3.metric("CPM (Influencer Only)", f"${cpm:.2f}")

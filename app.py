import streamlit as st
import pandas as pd
import numpy as np

import streamlit as st
import pandas as pd
import numpy as np

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Agency Resource Estimator", layout="wide")

st.title("🤖 Project Hours Estimator (Beta)")
st.markdown("---")

# --- PHẦN 1: KHAI BÁO HỆ SỐ MÔ HÌNH (THE BRAIN) ---
# Lưu ý: Vì t không thấy sheet 'result', t đang để số giả định (dummy).
# M cần thay số thực tế từ file Excel của m vào đây.
# Cấu trúc: Mỗi Role là một key, bên trong là các hệ số Beta tương ứng.

MODEL_COEFFICIENTS = {
    "Delivery Chief": {
        "Intercept": 1.5,
        "guaranteed_creators": 0.02,
        "duration_weeks": 0.05,
        "Client_Difficulty_Rating": 0.1,
        "vn_vetting_yes": 0.0,
        "Sector_Public": 0.2
    },
    "Acct Supervisor US": {
        "Intercept": 2.0,
        "guaranteed_creators": 0.05,
        "duration_weeks": 0.08,
        "Client_Difficulty_Rating": 0.15,
        "vn_vetting_yes": 0.1,
        "Sector_Public": 0.0
    },
    "Acct Manager US": {
        "Intercept": 3.2,
        "guaranteed_creators": 0.1,
        "duration_weeks": 0.12,
        "Client_Difficulty_Rating": 0.2,
        "vn_vetting_yes": 0.0,
        "Sector_Public": 0.1
    },
    "Assistant SA": {
        "Intercept": 3.0,
        "guaranteed_creators": 0.15,
        "duration_weeks": 0.1,
        "Client_Difficulty_Rating": 0.05,
        "vn_vetting_yes": 0.3, # Ví dụ: Vetting VN tốn nhiều giờ Assistant
        "Sector_Public": 0.0
    },
    "Tech Prod Head": {
        "Intercept": 0.5,
        "guaranteed_creators": 0.01,
        "duration_weeks": 0.02,
        "Client_Difficulty_Rating": 0.0,
        "vn_vetting_yes": 0.0,
        "Sector_Public": 0.0
    }
}

# --- PHẦN 2: SIDEBAR INPUTS (NHẬP LIỆU) ---
with st.sidebar:
    st.header("📝 Project Parameters")
    
    # Nhóm biến số lượng
    guaranteed_creators = st.number_input("Guaranteed Creators", value=5, min_value=0)
    contents_resid = st.number_input("Contents Resid (Ref B3)", value=0, min_value=0) # Biến này có trong công thức nhưng chưa rõ vai trò
    duration_weeks = st.number_input("Duration (Weeks)", value=14, min_value=1)
    
    st.markdown("---")
    # Nhóm biến độ khó
    client_difficulty = st.slider("Client Difficulty Rating", 1, 5, 3)
    influencer_mgmt_difficulty = st.slider("Influencer Mgmt Difficulty", 1, 5, 3)
    vetting_difficulty = st.slider("Vetting Difficulty", 1, 5, 1)
    
    st.markdown("---")
    # Nhóm biến phân loại (Categorical)
    sector = st.selectbox("Sector", ["General", "Public", "Tech", "Consumer"])
    vn_vetting = st.selectbox("VN Vetting?", ["No", "Yes"])

# --- PHẦN 3: ENGINE TÍNH TOÁN (LOGIC EXCEL) ---
def calculate_hours(role, coeffs):
    # Công thức: EXP(Intercept + B1*X1 + B2*X2 + ...)
    
    # 1. Bắt đầu với Intercept
    linear_y = coeffs.get("Intercept", 0)
    
    # 2. Cộng các biến số (Numeric Variables)
    linear_y += coeffs.get("guaranteed_creators", 0) * guaranteed_creators
    linear_y += coeffs.get("duration_weeks", 0) * duration_weeks
    linear_y += coeffs.get("Client_Difficulty_Rating", 0) * client_difficulty
    linear_y += coeffs.get("Influencer_Management_Difficulty_Rating", 0) * influencer_mgmt_difficulty
    
    # 3. Cộng biến Dummy (Categorical Variables)
    # Xử lý Sector (Ví dụ: Nếu Sector là Public thì cộng hệ số Sector_Public)
    sector_key = f"Sector_{sector}"
    if sector_key in coeffs:
        linear_y += coeffs[sector_key]
        
    # Xử lý VN Vetting (Yes/No)
    if vn_vetting == "Yes":
        linear_y += coeffs.get("vn_vetting_yes", 0)
        
    # 4. Trả về hàm Mũ (EXP) để ra số giờ thực tế
    return np.exp(linear_y)

# --- PHẦN 4: HIỂN THỊ KẾT QUẢ (OUTPUT) ---

# Tính toán cho tất cả các role
results = []
for role, coeffs in MODEL_COEFFICIENTS.items():
    hours = calculate_hours(role, coeffs)
    results.append({"Role": role, "Estimated Hours": round(hours, 1)})

# Tạo DataFrame
df_results = pd.DataFrame(results)
total_hours = df_results["Estimated Hours"].sum()

# Hiển thị Metrics tổng quan
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Total Staff Hours", value=f"{total_hours:,.1f} hrs")
with col2:
    # Giả sử rate trung bình là $100/hr để demo cost
    st.metric(label="Est. Internal Cost (Demo Rate)", value=f"${total_hours * 100:,.2f}")

# Hiển thị bảng chi tiết
st.subheader("📊 Breakdown by Role")
st.dataframe(
    df_results.style.background_gradient(cmap="Blues", subset=["Estimated Hours"]),
    use_container_width=True
)

# Hiển thị biểu đồ cho trực quan (ENTP thích nhìn Chart)
st.bar_chart(df_results.set_index("Role"))

# Debug: Show logic giải thích
with st.expander("Show Calculation Logic (For Validation)"):
    st.write("Model Formula used: Hours = EXP(Intercept + β * Inputs)")
    st.write("Current Coefficients being used:", MODEL_COEFFICIENTS)

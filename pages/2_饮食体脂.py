import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_conn
from datetime import date
import requests
from dotenv import load_dotenv
import math

load_dotenv()

NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")

st.set_page_config(page_title="饮食与体脂", page_icon="🥗")
st.title("🥗 饮食记录 & 体脂率")

conn = get_conn()
c = conn.cursor()

# ========== 饮食记录 ==========
st.subheader("📝 记录今日饮食")

food_date = st.date_input("日期", date.today(), key="food_date")
food_name = st.text_input("食物名称")
amount = st.number_input("份量（克）", min_value=1, value=100)

cal_source = st.radio("卡路里数据来源", ["手动输入", "自动查询（Nutritionix）"], horizontal=True)

calories = protein = carbs = fat = 0.0

if cal_source == "手动输入":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        calories = st.number_input("热量(kcal)", min_value=0.0, value=0.0, step=10.0)
    with col2:
        protein = st.number_input("蛋白质(g)", min_value=0.0, value=0.0, step=0.5)
    with col3:
        carbs = st.number_input("碳水(g)", min_value=0.0, value=0.0, step=0.5)
    with col4:
        fat = st.number_input("脂肪(g)", min_value=0.0, value=0.0, step=0.5)
else:
    if NUTRITIONIX_APP_ID and NUTRITIONIX_APP_KEY:
        query_btn = st.checkbox("点击查询 Nutritionix")
        if query_btn and food_name:
            try:
                url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
                headers = {
                    "x-app-id": NUTRITIONIX_APP_ID,
                    "x-app-key": NUTRITIONIX_APP_KEY,
                    "Content-Type": "application/json"
                }
                data = {"query": f"{amount}g {food_name}"}
                resp = requests.post(url, headers=headers, json=data)
                if resp.status_code == 200:
                    foods = resp.json()["foods"]
                    if foods:
                        food = foods[0]
                        calories = food.get("nf_calories", 0)
                        protein = food.get("nf_protein", 0)
                        carbs = food.get("nf_total_carbohydrate", 0)
                        fat = food.get("nf_total_fat", 0)
                        st.success(f"✅ 查询结果：{calories:.1f} kcal | 蛋白质 {protein:.1f}g | 碳水 {carbs:.1f}g | 脂肪 {fat:.1f}g")
                    else:
                        st.warning("未找到该食物")
                else:
                    st.error("API 请求失败")
            except Exception as e:
                st.error(f"查询出错：{e}")
    else:
        st.info("💡 未配置 Nutritionix API，请使用手动输入。")

if st.button("💾 保存饮食记录", type="primary"):
    if food_name:
        c.execute("INSERT INTO food_logs (date, food_name, amount_g, calories, protein, carbs, fat) VALUES (?,?,?,?,?,?,?)",
                  (food_date.strftime("%Y-%m-%d"), food_name, amount, calories, protein, carbs, fat))
        conn.commit()
        st.success(f"已记录：{food_name} {amount}g")
    else:
        st.warning("请输入食物名称")

st.divider()

# ========== 饮食历史 ==========
st.subheader("📅 饮食历史")
view_food_date = st.date_input("查看日期", date.today(), key="view_food")
c.execute("SELECT * FROM food_logs WHERE date=? ORDER BY id", (view_food_date.strftime("%Y-%m-%d"),))
foods = c.fetchall()

if foods:
    total_cal = sum(f["calories"] for f in foods)
    st.markdown(f"### 🥣 当日总热量：{total_cal:.1f} kcal")
    data = []
    for f in foods:
        data.append({
            "食物": f["food_name"],
            "份量(g)": f["amount_g"],
            "热量(kcal)": f["calories"],
            "蛋白质(g)": f["protein"],
            "碳水(g)": f["carbs"],
            "脂肪(g)": f["fat"]
        })
    st.dataframe(data, use_container_width=True)
else:
    st.info("这一天还没有饮食记录")

st.divider()

# ========== 身体指标 & 体脂率 ==========
st.subheader("📏 身体指标 & 体脂率计算")

height_cm = st.number_input("身高(cm) 用于体脂计算", min_value=100, max_value=250, value=173, step=1)

def calculate_body_fat(weight, neck, waist, hip=None, height=173):
    if hip and hip > 0:
        return 163.205 * math.log10(waist + hip - neck) - 97.684 * math.log10(height) - 78.387
    else:
        return 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height) + 36.76

with st.form("body_metrics_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        m_date = st.date_input("日期", date.today(), key="m_date")
        m_weight = st.number_input("体重(kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.1)
        m_neck = st.number_input("颈围(cm)", min_value=20.0, max_value=80.0, value=37.0, step=0.1)
    with col2:
        m_waist = st.number_input("腰围(cm)", min_value=50.0, max_value=200.0, value=80.0, step=0.1)
        m_hip = st.number_input("臀围(cm)（可选，女性填）", min_value=0.0, max_value=200.0, value=0.0, step=0.1)

    submitted = st.form_submit_button("计算并保存体脂率")
    if submitted:
        if m_neck > 0 and m_waist > 0:
            bf = calculate_body_fat(m_weight, m_neck, m_waist, m_hip if m_hip > 0 else None, height_cm)
            c.execute("INSERT INTO body_metrics (date, weight, neck, waist, hip, body_fat) VALUES (?,?,?,?,?,?)",
                      (m_date.strftime("%Y-%m-%d"), m_weight, m_neck, m_waist, m_hip if m_hip > 0 else None, bf))
            conn.commit()
            st.success(f"✅ 体脂率：{bf:.1f}%")
        else:
            st.error("请至少输入颈围和腰围")

# 历史趋势
st.subheader("📈 历史趋势")
c.execute("SELECT date, weight, body_fat FROM body_metrics ORDER BY date")
metrics = c.fetchall()
if metrics:
    dates = [m["date"] for m in metrics]
    weights = [m["weight"] for m in metrics]
    bfats = [m["body_fat"] for m in metrics]

    tab1, tab2 = st.tabs(["📉 体重变化", "📊 体脂率变化"])
    with tab1:
        st.line_chart({"体重(kg)": weights}, x=dates, x_label="日期", y_label="kg")
    with tab2:
        st.line_chart({"体脂率(%)": bfats}, x=dates, x_label="日期", y_label="%")
else:
    st.info("暂无身体指标数据，请添加数据以生成图表")

conn.close()
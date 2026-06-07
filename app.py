import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI 健身管理", page_icon="🏋️")

st.title("🏋️ AI 智能健身管理平台")
st.markdown("#### 选择左侧的功能模块开始使用")

with st.sidebar:
    st.header("AI 快速生成计划")
    weight = st.number_input("体重(kg)", 30, 200, 70, key="ai_weight")
    height = st.number_input("身高(cm)", 140, 220, 175, key="ai_height")
    goal = st.selectbox("目标", ["增肌", "减脂", "塑形"], key="ai_goal")
    days = st.slider("每周训练天数", 2, 7, 4, key="ai_days")

    if st.button("生成周计划"):
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        with st.spinner("AI 正在帮你定制计划..."):
            prompt = f"用户{weight}kg, {height}cm, 目标{goal}, 每周{days}天。生成一份周训练计划，返回纯文本，每天列出3-5个动作。"
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            plan = response.choices[0].message.content
            st.session_state.plan = plan
        st.success("计划已生成！")

if "plan" in st.session_state:
    with st.expander("📅 查看生成的周计划"):
        st.text(st.session_state.plan)
import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_conn
from datetime import date

st.set_page_config(page_title="拉伸动作库", page_icon="🧘")

st.title("🧘 拉伸动作库 & 视频链接")

conn = get_conn()
c = conn.cursor()

# ========== 添加拉伸视频 ==========
st.subheader("📌 添加新的拉伸视频")

with st.form("add_stretch", clear_on_submit=True):
    title = st.text_input("动作名称")
    description = st.text_area("动作描述（可选）")
    video_url = st.text_input("视频链接（支持抖音、B站等）")
    category = st.selectbox("分类", ["静态拉伸", "动态拉伸", "泡沫轴放松", "其他"])
    submit = st.form_submit_button("保存")

    if submit:
        if title and video_url:
            c.execute("INSERT INTO stretch_videos (title, description, video_url, category, date_added) VALUES (?,?,?,?,?)",
                      (title, description, video_url, category, date.today().strftime("%Y-%m-%d")))
            conn.commit()
            st.success(f"已保存：{title}")
        else:
            st.warning("动作名称和视频链接为必填项")

st.divider()

# ========== 浏览已存视频 ==========
st.subheader("📂 我的拉伸库")

c.execute("SELECT DISTINCT category FROM stretch_videos ORDER BY category")
cats = [row["category"] for row in c.fetchall()]
if cats:
    filter_cat = st.selectbox("筛选分类", ["全部"] + cats)
else:
    filter_cat = "全部"

if filter_cat == "全部":
    c.execute("SELECT * FROM stretch_videos ORDER BY date_added DESC")
else:
    c.execute("SELECT * FROM stretch_videos WHERE category=? ORDER BY date_added DESC", (filter_cat,))

videos = c.fetchall()

if videos:
    for v in videos:
        with st.expander(f"🧘 {v['title']}  ({v['category']})"):
            if v["description"]:
                st.write(v["description"])
            st.markdown(f"📎 **视频链接**：[点击观看]({v['video_url']})")
            st.caption(f"添加日期：{v['date_added']}")
else:
    st.info("还没有添加任何拉伸视频，去添加第一个吧！")

conn.close()
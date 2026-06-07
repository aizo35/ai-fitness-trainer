import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_conn
from datetime import date
from PIL import Image

st.set_page_config(page_title="照片存档", page_icon="📸")

st.title("📸 健身照片存档")

# 创建存储图片的文件夹
PHOTO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "photos")
os.makedirs(PHOTO_DIR, exist_ok=True)

conn = get_conn()
c = conn.cursor()

# ========== 上传照片 ==========
st.subheader("📤 上传新照片")

uploaded_files = st.file_uploader(
    "选择照片（可多选）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    category = st.selectbox("照片分类", ["体重照", "肌肉照", "其他"])
    note = st.text_input("备注（可选）")
    
    if st.button("📥 保存所有照片"):
        saved_count = 0
        for uploaded_file in uploaded_files:
            # 生成唯一文件名（时间戳+原文件名）
            file_ext = uploaded_file.name.split(".")[-1]
            save_name = f"{date.today().strftime('%Y%m%d')}_{uploaded_file.name}"
            save_path = os.path.join(PHOTO_DIR, save_name)
            
            # 保存图片到本地
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 数据库记录
            c.execute(
                "INSERT INTO photos (date, category, file_path, note) VALUES (?,?,?,?)",
                (date.today().strftime("%Y-%m-%d"), category, save_path, note)
            )
            saved_count += 1
        
        conn.commit()
        st.success(f"成功保存 {saved_count} 张照片！")

st.divider()

# ========== 浏览照片库 ==========
st.subheader("🖼️ 我的照片库")

# 筛选分类
c.execute("SELECT DISTINCT category FROM photos ORDER BY category")
cats = [row["category"] for row in c.fetchall()]
if cats:
    filter_cat = st.selectbox("筛选分类", ["全部"] + cats)
else:
    filter_cat = "全部"

# 按日期倒序显示
if filter_cat == "全部":
    c.execute("SELECT * FROM photos ORDER BY date DESC, id DESC")
else:
    c.execute("SELECT * FROM photos WHERE category=? ORDER BY date DESC, id DESC", (filter_cat,))

photos = c.fetchall()

if photos:
    # 使用网格布局展示照片
    cols_per_row = 3
    for i in range(0, len(photos), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(photos):
                photo = photos[idx]
                with cols[j]:
                    if os.path.exists(photo["file_path"]):
                        st.image(Image.open(photo["file_path"]), use_column_width=True)
                        st.caption(f"📅 {photo['date']}  |  🏷️ {photo['category']}")
                        if photo["note"]:
                            st.caption(f"📝 {photo['note']}")
                    else:
                        st.warning(f"图片文件不存在：{photo['file_path']}")
else:
    st.info("还没有照片，快去上传吧！")

conn.close()
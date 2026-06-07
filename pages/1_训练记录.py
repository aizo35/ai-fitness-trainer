import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_conn
from datetime import date

st.set_page_config(page_title="训练记录", page_icon="💪")

st.title("💪 训练记录")

conn = get_conn()
c = conn.cursor()

# 初始化临时列表
if "temp_workouts" not in st.session_state:
    st.session_state.temp_workouts = []

# ========== 添加训练记录 ==========
st.subheader("📝 记录今天的训练")
training_date = st.date_input("训练日期", date.today())

# 获取肌群
c.execute("SELECT id, name FROM body_parts ORDER BY id")
parts = c.fetchall()
part_names = [p["name"] for p in parts]
part_name_to_id = {p["name"]: p["id"] for p in parts}

# --- 肌群选择 ---
if "selected_part" not in st.session_state:
    st.session_state.selected_part = part_names[0]

selected_part = st.selectbox(
    "选择肌群",
    part_names,
    key="part_selector",
    on_change=lambda: setattr(st.session_state, "selected_exercise", None)
)
st.session_state.selected_part = selected_part

# --- 根据肌群加载动作 ---
c.execute("SELECT id, name FROM exercises WHERE body_part_id=? ORDER BY id",
          (part_name_to_id[selected_part],))
ex_list = c.fetchall()
ex_names = [e["name"] for e in ex_list]
ex_name_to_id = {e["name"]: e["id"] for e in ex_list}

if not ex_names:
    st.warning("该肌群还没有动作，请先在下方添加新动作。")
    selected_ex = None
else:
    if "selected_exercise" not in st.session_state or st.session_state.selected_exercise not in ex_names:
        st.session_state.selected_exercise = ex_names[0]

    selected_ex = st.selectbox(
        "选择动作",
        ex_names,
        key="exercise_selector"
    )
    st.session_state.selected_exercise = selected_ex

# --- 训练细节 ---
col1, col2, col3 = st.columns(3)
with col1:
    sets = st.number_input("组数", min_value=1, value=3)
with col2:
    reps = st.number_input("次数", min_value=0, value=10)
with col3:
    weight = st.number_input("重量(kg)", min_value=0.0, value=0.0, step=0.5)

notes = st.text_input("备注（可选）")

# --- 添加按钮 ---
if st.button("➕ 添加到本次训练列表"):
    if selected_part and selected_ex:
        st.session_state.temp_workouts.append({
            "part_id": part_name_to_id[selected_part],
            "part_name": selected_part,
            "exercise_id": ex_name_to_id[selected_ex],
            "exercise_name": selected_ex,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "notes": notes
        })
        st.success(f"已添加：{selected_part} - {selected_ex}")
    else:
        st.error("请先选择肌群和动作")

# --- 显示临时列表 ---
if st.session_state.temp_workouts:
    st.subheader("📋 本次训练列表")
    temp_data = []
    for idx, w in enumerate(st.session_state.temp_workouts):
        temp_data.append({
            "序号": idx + 1,
            "肌群": w["part_name"],
            "动作": w["exercise_name"],
            "组数": w["sets"],
            "次数": w["reps"],
            "重量(kg)": w["weight"],
            "备注": w["notes"]
        })
    st.dataframe(temp_data, use_container_width=True)

    col_clear, col_save = st.columns([1, 3])
    with col_clear:
        if st.button("清空列表"):
            st.session_state.temp_workouts = []
            st.rerun()
    with col_save:
        if st.button("💾 保存全部到数据库", type="primary"):
            if st.session_state.temp_workouts:
                for w in st.session_state.temp_workouts:
                    c.execute(
                        "INSERT INTO workout_logs (date, exercise_id, sets, reps, weight, notes) VALUES (?,?,?,?,?,?)",
                        (training_date.strftime("%Y-%m-%d"), w["exercise_id"], w["sets"], w["reps"], w["weight"], w["notes"])
                    )
                conn.commit()
                count = len(st.session_state.temp_workouts)
                st.session_state.temp_workouts = []
                st.success(f"已保存 {count} 条训练记录！")
                st.rerun()
            else:
                st.warning("列表为空，请先添加动作")

# --- 添加新动作 ---
with st.expander("➕ 添加新动作到动作库"):
    new_ex_name = st.text_input("动作名称")
    new_ex_part = st.selectbox("所属肌群", part_names, key="new_part")
    if st.button("确认添加"):
        if new_ex_name:
            part_id = part_name_to_id[new_ex_part]
            try:
                c.execute("INSERT INTO exercises (body_part_id, name) VALUES (?,?)", (part_id, new_ex_name))
                conn.commit()
                st.success(f"已添加动作：{new_ex_name}")
                st.rerun()
            except:
                st.error("添加失败，可能动作已存在")
        else:
            st.warning("请输入动作名称")

st.divider()

# ========== 训练历史 ==========
st.subheader("📅 训练历史")
view_date = st.date_input("选择日期查看", date.today(), key="view_date")

c.execute("""
    SELECT workout_logs.id, workout_logs.date, body_parts.name as part, exercises.name as exercise,
           workout_logs.sets, workout_logs.reps, workout_logs.weight, workout_logs.notes
    FROM workout_logs
    JOIN exercises ON workout_logs.exercise_id = exercises.id
    JOIN body_parts ON exercises.body_part_id = body_parts.id
    WHERE workout_logs.date = ?
    ORDER BY workout_logs.id
""", (view_date.strftime("%Y-%m-%d"),))

records = c.fetchall()

if records:
    data = []
    for r in records:
        data.append({
            "肌群": r["part"],
            "动作": r["exercise"],
            "组数": r["sets"],
            "次数": r["reps"],
            "重量(kg)": r["weight"],
            "备注": r["notes"]
        })
    st.dataframe(data, use_container_width=True)
else:
    st.info("这一天还没有训练记录")

conn.close()
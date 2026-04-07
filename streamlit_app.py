import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- TIL MANTIQI ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Русский"

if st.session_state.lang == "O'zbekcha":
    t_title, t_target, t_cons, t_add, t_solve, t_pdf = "📊 LP Yechuvchi", "🎯 Maqsad", "🚧 Cheklovlar", "+ Qo'shish", "🚀 Hisoblash", "📥 PDF"
    t_finish, t_gif = "✅ Tahrirlashni yakunlash", "🎞️ GIF saqlash"
else:
    t_title, t_target, t_cons, t_add, t_solve, t_pdf = "📊 Решатель ЛП", "🎯 Цель", "🚧 Ограничения", "+ Добавить", "🚀 Решить", "📥 PDF"
    t_finish, t_gif = "✅ Завершить редактирование", "🎞️ Сохранить GIF"

st.markdown(f"<h1 style='text-align: center;'>{t_title}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip: {obj_type} | X = {opt_x:.2f}, Y = {opt_y:.2f} | Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
if 'locked' not in st.session_state: st.session_state.locked = False

with st.sidebar:
    st.header(t_target)
    c1 = st.number_input("C1", value=5.3, key="main_c1", disabled=st.session_state.locked)
    c2 = st.number_input("C2", value=-7.1, key="main_c2", disabled=st.session_state.locked)
    obj_type = st.selectbox("Тип", ("max", "min"), key="main_type", disabled=st.session_state.locked)
    
    st.markdown("---")
    st.header(t_cons)
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}, {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0}]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        a = col1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        b = col2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        op = col3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        c = col4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        if col5.button("🗑️", key=f"del{i}", disabled=st.session_state.locked):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    if st.button(t_add, disabled=st.session_state.locked):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    if st.button(t_finish, use_container_width=True):
        st.session_state.locked = not st.session_state.locked
        st.rerun()
    
    solve_btn = st.button(t_solve, type="primary", use_container_width=True)
    st.session_state.lang = st.radio("🌐 Til", ("Русский", "O'zbekcha"), horizontal=True)

# --- ASOSIY QISM (GRAFIK VA O'NG TOMONDAGI NATIJALAR) ---
if solve_btn or st.session_state.locked:
    # (Matematik hisob-kitoblar qismi o'zgarishsiz qoldi)
    coeffs = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    # Interfeysni ikkiga bo'lish: Grafik (8 qism) va Natijalar (4 qism)
    col_graph, col_res = st.columns([8, 3])

    with col_graph:
        fig = go.Figure()
        # (Grafik chizish kodi: ODR, burchak nuqtalar va chiziqlar)
        # ... [Bu yerda sizning grafik kodingiz turadi] ...
        # (Ixchamlik uchun faqat layoutni yozdim)
        fig.update_layout(height=750, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_res:
        st.subheader("📝 " + ("Результаты" if st.session_state.lang == "Русский" else "Natijalar"))
        if res.success:
            st.info(f"**X:** {res.x[0]:.2f}\n\n**Y:** {res.x[1]:.2f}")
            st.success(f"**Z:** {c1*res.x[0] + c2*res.x[1]:.2f}")
            
            st.markdown("---")
            st.write("📤 **Export**")
            pdf_file = create_pdf(res.x[0], res.x[1], c1*res.x[0] + c2*res.x[1], obj_type)
            st.download_button(t_pdf, data=pdf_file, file_name="report.pdf", use_container_width=True)
            st.button(t_gif, use_container_width=True) # GIF tugmasi
        else:
            st.error("Yechim yo'q")

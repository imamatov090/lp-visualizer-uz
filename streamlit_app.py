import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- TILNI ANIQLASH VA XATONI TUZATISH ---
# O'zbek tilidagi "o'" harfi xatolik bermasligi uchun qo'sh qo'shtirnoqdan foydalanamiz
if "lang" not in st.session_state:
    st.session_state.lang = "Русский"

# Matnlar lug'ati (Rahbaringiz so'ragan terminlar bilan)
if st.session_state.lang == "O'zbekcha":
    t = {
        "title": "Chiziqli dasturlash — Yechuvchi",
        "target": "Maqsad funksiyasi",
        "cons": "Cheklovlar",
        "add": "+ Cheklov qo'shish",
        "solve": "🚀 Hisoblash",
        "res": "Natija",
        "pdf": "📥 PDF hisobot",
        "analiz": "🔍 Sezgirlik tahlili",
        "opt": "Optimum",
        "v_z": "VZ (Gradient)"
    }
else:
    t = {
        "title": "Линейное программирование — Решатель",
        "target": "Целевая функция",
        "cons": "Ограничения",
        "add": "+ Добавить ограничение",
        "solve": "🚀 Решить",
        "res": "Результат",
        "pdf": "📥 Скачать отчёт (PDF)",
        "analiz": "🔍 Анализ задачи",
        "opt": "Оптимум",
        "v_z": "VZ (Градиент)"
    }

st.markdown(f"<h1 style='text-align: center;'>{t['title']}</h1>", unsafe_allow_html=True)

# --- SIDEBAR: KIRITISH QISMI ---
with st.sidebar:
    st.header(t["target"])
    
    # Maqsad funksiyasi (ixcham ko'rinishda)
    c1_col, x_col, c2_col, y_col, type_col = st.columns([2, 1, 2, 1, 3])
    c_main1 = c1_col.number_input("C1", value=5.3, format="%.1f", key="c1", label_visibility="collapsed")
    x_col.markdown("<div style='margin-top:5px'>*x +</div>", unsafe_allow_html=True)
    c_main2 = c2_col.number_input("C2", value=-7.1, format="%.1f", key="c2", label_visibility="collapsed")
    y_col.markdown("<div style='margin-top:5px'>*y</div>", unsafe_allow_html=True)
    obj_type = type_col.selectbox("Type", ("max", "min"), label_visibility="collapsed")

    st.markdown("---")
    st.header(t["cons"])
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        # Rahbaringiz chizmasidagi kabi barcha elementlar bitta qatorda
        cl1, cl_x, cl2, cl_y, cl3, cl4, cl5 = st.columns([2, 1, 2, 1, 1.5, 2, 1])
        a = cl1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        cl_x.markdown("<div style='margin-top:5px'>*x+</div>", unsafe_allow_html=True)
        b = cl2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        cl_y.markdown("<div style='margin-top:5px'>*y</div>", unsafe_allow_html=True)
        op = cl3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        c = cl4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        if cl5.button("🗑️", key=f"del{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    
    # Tugmalarni o'ngga surish
    _, col_add = st.columns([1, 2])
    with col_add:
        if st.button(t["add"], use_container_width=True):
            st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
            st.rerun()

    st.markdown("---")
    solve_btn = st.button(t["solve"], type="primary", use_container_width=True)

    # --- TIL TANLASH (SIDEBAR PASTIDA) ---
    st.markdown("<br>" * 5, unsafe_allow_html=True)
    st.session_state.lang = st.radio("🌐 Til / Язык", ("Русский", "O'zbekcha"), horizontal=True)

# --- ASOSIY MANTIQ VA GRAFIK ---
if solve_btn:
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_main1 * opt_x + c_main2 * opt_y
        
        st.success(f"### {t['res']}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}")

        # Grafik yaratish
        fig = go.Figure()
        x_vals = np.linspace(-15, 15, 400)
        
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_vals) / c['b']
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=f"L{i+1}"))
        
        # Gradient vektori (Rahbaringiz so'ragan VZ)
        fig.add_annotation(x=opt_x + (c_main1/5), y=opt_y + (c_main2/5), ax=opt_x, ay=opt_y,
                           xref="x", yref="y", axref="x", ayref="y",
                           text=t["v_z"], showarrow=True, arrowhead=3, arrowcolor="red")

        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', 
                                 marker=dict(size=15, color='gold', symbol='star'), name=t["opt"]))

        fig.update_layout(height=700, plot_bgcolor='white', xaxis=dict(zeroline=True), yaxis=dict(zeroline=True))
        st.plotly_chart(fig, use_container_width=True)

        # Qoshimcha funksiyalar uchun tugmalar (O'ng tomonda)
        btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
        with btn_col2:
            st.button(t["analiz"], use_container_width=True)
        with btn_col3:
            st.button(t["pdf"], use_container_width=True)
    else:
        st.error("Yechim topilmadi.")

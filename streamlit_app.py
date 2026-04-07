import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- ENG QULAY TIL TANLASH USULI ---
with st.sidebar:
    lang = st.radio("Тилni tanlang / Выберите язык:", ("O'zbekcha", "Русский"), horizontal=True)

# Matnlar bazasi
if lang == "O'zbekcha":
    t_title = "Chiziqli dasturlash — Yechuvchi"
    t_target = "Maqsad funksiyasi"
    t_cons = "Cheklovlar"
    t_add = "+ Cheklov qo'shish"
    t_solve = "🚀 Hisoblash"
    t_res = "Natija"
    t_pdf = "📥 PDF hisobot"
    t_err = "Yechim topilmadi."
else:
    t_title = "Линейное программирование — Решатель"
    t_target = "Целевая функция"
    t_cons = "Ограничения"
    t_add = "+ Добавить ограничение"
    t_solve = "🚀 Решить"
    t_res = "Результат"
    t_pdf = "📥 Скачать PDF"
    t_err = "Решение не найдено."

# Sarlavha (Skrinshotingizdagi kabi markazda va rasm bilan)
st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 25px;">
        <span style="font-size: 40px;">📊</span>
        <h1 style="font-family: sans-serif; font-weight: 800; color: #31333F; font-size: 34px; margin: 0;">
            {t_title}
        </h1>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR KIRITISH QISMI ---
with st.sidebar:
    st.subheader(f"🎯 {t_target}")
    c_col1, _, c_col2, _, t_col = st.columns([2, 0.5, 2, 0.5, 2])
    c1 = c_col1.number_input("C1", value=5.3, key="c1", label_visibility="collapsed")
    c2 = c_col2.number_input("C2", value=-7.1, key="c2", label_visibility="collapsed")
    obj_type = t_col.selectbox("Type", ("max", "min"), label_visibility="collapsed")
    
    st.markdown("---")
    st.subheader(f"🚧 {t_cons}")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.2, 1.5, 0.6])
        a = col1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        b = col2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        op = col3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        c = col4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        if col5.button("🗑️", key=f"del{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    if st.button(t_add, use_container_width=True):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()
    
    st.markdown("---")
    solve_btn = st.button(t_solve, type="primary", use_container_width=True)

# --- NATIJA VA GRAFIK ---
if solve_btn:
    # Matematik yechim (linprog)
    coeffs = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c1 * opt_x + c2 * opt_y
        
        # Natija bloki (Markazda, yashil fonda)
        st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <div style="background-color: #e8f5e9; color: #2e7d32; padding: 15px 30px; border-radius: 8px; font-size: 22px; font-weight: bold;">
                    {t_res}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Grafik qismi
        fig = go.Figure()
        x_range = np.linspace(-20, 20, 400)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}"))
        
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', 
                                 marker=dict(size=15, color='gold', symbol='star', line=dict(width=1, color='black')), 
                                 name="Optimum"))
        
        fig.update_layout(height=650, margin=dict(t=10), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # PDF yuklash tugmasi
        st.download_button(t_pdf, data=b"Report Content", file_name="report.pdf")
    else:
        st.error(t_err)

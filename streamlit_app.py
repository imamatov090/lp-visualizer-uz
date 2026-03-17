import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# Sarlavha
st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)

# --- FUNKSIYALAR ---

def create_pdf(opt_x, opt_y, opt_val, obj_type, constraints):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Tip optimizatsii: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"Optimalnaya tochka: X = {opt_x:.2f}, Y = {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Znachenie tselevoy funksii: {opt_val:.2f}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt="Ogranicheniya:", ln=True)
    for i, c in enumerate(constraints):
        pdf.cell(200, 10, txt=f" {i+1}) {c['a']}x + {c['b']}y {c['op']} {c['c']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    c_col1, c_col2, c_col3 = st.columns([2, 2, 2])
    with c_col1: c1 = st.number_input("C1", value=5.3, step=0.1, format="%.1f", label_visibility="collapsed")
    with c_col2: c2 = st.number_input("C2", value=-7.1, step=0.1, format="%.1f", label_visibility="collapsed")
    with c_col3: obj_type = st.selectbox("max/min", ("max", "min"), label_visibility="collapsed")
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    new_constraints = []
    for i, cons in enumerate(st.session_state.constraints):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 2, 1])
        with col1: a = st.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with col2: b = st.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with col3: op = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        with col4: c = st.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with col5: 
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_constraints.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_constraints
    if st.button("+ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: solve = st.button("Решить", type="primary", use_container_width=True)
    with col_btn2: 
        if st.button("Очистить", use_container_width=True):
            st.session_state.constraints = []
            st.rerun()

# --- GRAFIK VA NATIJA ---
if solve and st.session_state.constraints:
    # Hisob-kitob (Simplex)
    obj = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    # Grafik chizish (Aynan rasmdagidek)
    fig = go.Figure()
    x_vals = np.linspace(-15, 15, 500)
    colors = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#8c564b']

    for i, c in enumerate(st.session_state.constraints):
        label = f"{c['a']:.2f} * x + {c['b']:.2f} * y {c['op']} {c['c']:.2f}"
        if abs(c['b']) > 1e-9:
            y_vals = (c['c'] - c['a'] * x_vals) / c['b']
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=label, line=dict(color=colors[i % len(colors)])))

    if res.success:
        opt_x, opt_y = res.x
        opt_val = c1 * opt_x + c2 * opt_y
        
        # Maqsad funksiyasi chizig'i (Dashed)
        y_obj = (opt_val - c1 * x_vals) / c2
        fig.add_trace(go.Scatter(x=x_vals, y=y_obj, mode='lines', name=f"Целевая прямая: {c1}*x + {c2}*y = {opt_val:.2f}", 
                                 line=dict(color='black', dash='dot')))
        
        # Optimum nuqta (Yulduzcha)
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', name="Оптимум",
                                 text=[f"Оптимум ({opt_x:.2f}; {opt_y:.2f})"], textposition="bottom center",
                                 marker=dict(color='gold', size=15, symbol='star', line=dict(color='black', width=1))))

        st.plotly_chart(fig, use_container_width=True)
        
        # Pastki tugma (PDF)
        pdf_data = create_pdf(opt_x, opt_y, opt_val, obj_type, st.session_state.constraints)
        st.download_button("Скачать отчёт (PDF)", data=pdf_data, file_name="otchet_lp.pdf", mime="application/pdf")
    else:
        st.error("Решение не найдено.")

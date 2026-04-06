import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- MUTLAQ MARKAZLASHTIRISH UCHUN CSS ---
st.markdown("""
    <style>
    /* Sarlavha va natijani sidebar bor-yo'qligidan qat'i nazar markazda saqlash */
    .absolute-center {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        text-align: center;
        margin-bottom: 20px;
    }
    .header-text {
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 700;
        color: #31333F;
        font-size: 36px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .result-box {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 15px 25px;
        border-radius: 10px;
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
        width: fit-content;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SARLAVHA ---
st.markdown("""
    <div class="absolute-center">
        <div class="header-text">
            <span>📊</span> Линейное программирование — Решатель
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    c1_col, x_col, c2_col, y_col, t_col = st.columns([2, 0.5, 2, 0.5, 2])
    c1 = c1_col.number_input("C1", value=5.3, key="c1", label_visibility="collapsed")
    x_col.markdown("x +")
    c2 = c2_col.number_input("C2", value=-7.1, key="c2", label_visibility="collapsed")
    y_col.markdown("y")
    obj_type = t_col.selectbox("Тип", ("max", "min"), label_visibility="collapsed")
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0}
        ]
    
    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1, 1.5, 0.5])
        a = col1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        b = col2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        op = col3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        c = col4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        if col5.button("🗑️", key=f"del{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    st.session_state.constraints = new_cons
    
    if st.button("+ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()
    
    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- YECHIM ---
if solve_btn:
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
        
        # NATIJA BLOKI (MARKAZDA)
        st.markdown(f"""
            <div class="absolute-center">
                <div class="result-box">
                    Результат: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # GRAFIK
        fig = go.Figure()
        x_range = np.linspace(-20, 20, 400)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}"))
        
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', marker=dict(size=15, color='gold', symbol='star'), name="Оптимум"))
        fig.update_layout(height=600, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Решение не найдено.")

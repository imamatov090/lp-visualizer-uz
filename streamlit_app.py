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

# PDF Funksiyasi
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"X = {opt_x:.2f}, Y = {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    col_c1, col_c2, col_type = st.columns([2, 2, 2])
    with col_c1: c1 = st.number_input("C1", value=5.3, step=0.1, label_visibility="collapsed")
    with col_c2: c2 = st.number_input("C2", value=-7.1, step=0.1, label_visibility="collapsed")
    with col_type: obj_type = st.selectbox("Type", ("max", "min"), label_visibility="collapsed")
    
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

    current_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        c1, c2, op, c3, dl = st.columns([2, 2, 1.5, 2, 1])
        with c1: a_v = st.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with c2: b_v = st.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with op: op_v = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        with c3: c_v = st.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with dl: 
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        current_cons.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    
    st.session_state.constraints = current_cons
    if st.button("+ Добавить"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- GRAFIK ---
if solve:
    # LP Solver
    obj_c = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj_c, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    fig = go.Figure()
    x_plot = np.linspace(-20, 20, 1000)

    # Chegaralar
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-9:
            y_p = (c['c'] - c['a'] * x_plot) / c['b']
            fig.add_trace(go.Scatter(x=x_plot, y=y_p, mode='lines', name=f"{c['a']}x + {c['b']}y {c['op']} {c['c']}"))

    if res.success:
        ox, oy = res.x
        val = c1 * ox + c2 * oy
        
        # Maqsad funksiyasi (Uzuk-uzuk chiziq)
        y_obj = (val - c1 * x_plot) / c2
        fig.add_trace(go.Scatter(x=x_plot, y=y_obj, mode='lines', name=f"Целевая прямая: {c1}x + {c2}y = {val:.2f}", 
                                 line=dict(color='black', dash='dash', width=1.5)))

        # Vektor VZ (Strelka)
        fig.add_annotation(x=ox+1, y=oy+(c2/c1 if c1!=0 else 1), ax=ox, ay=oy,
                           xref="x", yref="y", axref="x", ayref="y",
                           text="VZ", showarrow=True, arrowhead=2, arrowcolor="red", font=dict(color="red", size=14))

        # Optimum nuqta (Yulduz)
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', 
                                 text=[f"Оптимум ({ox:.2f}; {oy:.2f})"], 
                                 textposition="bottom center",
                                 marker=dict(color='gold', size=18, symbol='star', line=dict(color='black', width=1.5)),
                                 name="Оптимум"))

    # Kichikroq setka va fon sozlamalari
    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='rgba(200, 200, 200, 0.5)', gridwidth=0.5, dtick=2.5, range=[-15, 15], zerolinecolor='black'),
        yaxis=dict(showgrid=True, gridcolor='rgba(200, 200, 200, 0.5)', gridwidth=0.5, dtick=2.5, range=[-20, 20], zerolinecolor='black'),
        legend=dict(x=0.65, y=1, bgcolor='rgba(255, 255, 255, 0.8)', bordercolor='black', borderwidth=1),
        height=750
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # PDF Tugmasi
    st.download_button("📥 Скачать отчёт (PDF)", data=create_pdf(ox, oy, val, obj_type), file_name="lp_report.pdf")

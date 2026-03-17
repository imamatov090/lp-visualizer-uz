import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="LP Reshatel", layout="wide")

st.markdown("<h1 style='text-align: center;'>📊 Chiziqli dasturlash — Reshatel</h1>", unsafe_allow_html=True)

# --- PDF GENERATSIYASI (Xatosiz variant) ---
def create_report_pdf(opt_x, opt_y, opt_val, obj_type, constraints):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "LP MASALASI BO'YICHA HISOBOT", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Sana: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Turi: {obj_type}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Cheklovlar:", ln=True)
    pdf.set_font("Arial", size=11)
    for i, c in enumerate(constraints):
        pdf.cell(0, 8, f" L{i+1}: {c['a']}x + {c['b']}y {c['op']} {c['c']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "NATIJALAR:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"X* = {opt_x:.4f}", ln=True)
    pdf.cell(0, 8, f"Y* = {opt_y:.4f}", ln=True)
    pdf.cell(0, 8, f"Z* = {opt_val:.4f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header("🎯 Maqsad funksiyasi")
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1: c_val1 = st.number_input("C1", value=5.3, key="main_c1")
    with col2: c_val2 = st.number_input("C2", value=-7.1, key="main_c2")
    with col3: goal = st.selectbox("Turi", ("max", "min"), key="main_goal")
    
    st.header("🚧 Cheklovlar")
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    current_list = []
    for i, cons in enumerate(st.session_state.constraints):
        r1, r2, r3, r4, r5 = st.columns([2, 2, 1.5, 2, 1])
        with r1: a = st.number_input(f"a{i}", value=float(cons['a']), key=f"a_{i}", label_visibility="collapsed")
        with r2: b = st.number_input(f"b{i}", value=float(cons['b']), key=f"b_{i}", label_visibility="collapsed")
        with r3: op = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op_{i}", label_visibility="collapsed")
        with r4: c = st.number_input(f"c{i}", value=float(cons['c']), key=f"c_{i}", label_visibility="collapsed")
        with r5: 
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        current_list.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = current_list
    if st.button("+ Qo'shish"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    solve_btn = st.button("🚀 Yechish", type="primary", use_container_width=True)

# --- NATIJA ---
if solve_btn:
    obj_coeffs = [-c_val1 if goal == "max" else c_val1, -c_val2 if goal == "max" else c_val2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj_coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_z = c_val1 * opt_x + c_val2 * opt_y
        
        # Grafik
        fig = go.Figure()
        x_range = np.linspace(-15, 15, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}"))

        # Maqsad chizig'i (Uzuk-uzuk)
        y_goal = (opt_z - c_val1 * x_range) / c_val2
        fig.add_trace(go.Scatter(x=x_range, y=y_goal, mode='lines', name="Z chizig'i", line=dict(color='black', dash='dash')))
        
        # Optimum nuqta va Vektor
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name="Optimum"))
        fig.add_annotation(x=opt_x+2, y=opt_y+2, ax=opt_x, ay=opt_y, xref="x", yref="y", axref="x", ayref="y", text="VZ", showarrow=True, arrowhead=2, arrowcolor="red")

        fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2), yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2))
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"Natija: X={opt_x:.4f}, Y={opt_y:.4f}, Z={opt_z:.4f}")
        
        # PDF yuklash
        pdf_data = create_report_pdf(opt_x, opt_y, opt_z, goal, st.session_state.constraints)
        st.download_button("📥 PDF yuklash", data=pdf_data, file_name="report.pdf", mime="application/pdf")
    else:
        st.error("Yechim topilmadi.")

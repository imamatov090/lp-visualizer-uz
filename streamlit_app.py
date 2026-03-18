import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- PDF GENERATSIYASI (Xatosiz va barqaror) ---
def create_safe_pdf(opt_x, opt_y, opt_val, obj_type, constraints):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "LP MASALASI BO'YICHA HISOBOT", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Sana: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Optimizatsiya turi: {obj_type}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Chegaraviy shartlar:", ln=True)
    pdf.set_font("Arial", size=11)
    for i, c in enumerate(constraints):
        pdf.cell(0, 8, f" L{i+1}: {c['a']}*x + {c['b']}*y {c['op']} {c['c']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "YAKUNIY NATIJALAR:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Optimal nuqta: X* = {opt_x:.4f}, Y* = {opt_y:.4f}", ln=True)
    pdf.cell(0, 8, f"Maqsad funksiyasi qiymati: Z* = {opt_val:.4f}", ln=True)
    
    # Unicode xatosini oldini olish uchun (latin-1 da ishlaydi)
    return pdf.output(dest='S').encode('latin-1')

st.title("📊 Chiziqli dasturlash — Reshatel")

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header("🎯 Maqsad funksiyasi")
    # TypeError'ning oldini olish uchun noyob kalitlar ishlatildi 
    c1_in = st.number_input("C1", value=5.3, key="inp_c1")
    c2_in = st.number_input("C2", value=-7.1, key="inp_c2")
    type_in = st.selectbox("Turi", ("max", "min"), key="inp_type")
    
    st.header("🚧 Cheklovlar")
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    new_c_list = []
    for i, con in enumerate(st.session_state.constraints):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 2, 1])
        with col1: a = st.number_input(f"a{i}", value=float(con['a']), key=f"key_a{i}", label_visibility="collapsed")
        with col2: b = st.number_input(f"b{i}", value=float(con['b']), key=f"key_b{i}", label_visibility="collapsed")
        with col3: op = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(con['op']), key=f"key_o{i}", label_visibility="collapsed")
        with col4: c = st.number_input(f"c{i}", value=float(con['c']), key=f"key_c{i}", label_visibility="collapsed")
        with col5: 
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_c_list.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_c_list
    if st.button("+ Qo'shish"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    btn_solve = st.button("🚀 Yechish", type="primary", use_container_width=True)

# --- ASOSIY QISM ---
if btn_solve:
    c_list = [-c1_in if type_in == "max" else c1_in, -c2_in if type_in == "max" else c2_in]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(c_list, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        ox, oy = res.x
        oz = c1_in * ox + c2_in * oy
        
        # Grafik
        fig = go.Figure()
        xr = np.linspace(-15, 15, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                yr = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=yr, mode='lines', name=f"L{i+1}"))
        
        # Maqsad chizig'i va vektor
        y_z = (oz - c1_in * xr) / c2_in
        fig.add_trace(go.Scatter(x=xr, y=y_z, mode='lines', name="Z line", line=dict(color='black', dash='dash')))
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name="Optimum"))
        fig.add_annotation(x=ox+1.5, y=oy+1.5, ax=ox, ay=oy, xref="x", yref="y", axref="x", ayref="y", text="VZ", showarrow=True, arrowhead=2, arrowcolor="red")

        fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2), yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2))
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"Natija: X={ox:.4f}, Y={oy:.4f}, Z={oz:.4f}")
        
        # PDF tayyorlash [cite: 43]
        final_pdf = create_safe_pdf(ox, oy, oz, type_in, st.session_state.constraints)
        st.download_button("📥 Hisobotni yuklash (PDF)", data=final_pdf, file_name="lp_report.pdf", mime="application/pdf")
    else:
        st.error("Yechim topilmadi.")

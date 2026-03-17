import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="Chiziqli dasturlash - Yechuvchi", layout="wide")

st.markdown("<h1 style='text-align: center;'>📊 Chiziqli dasturlash (LP) — Reshatel</h1>", unsafe_allow_html=True)

# --- PDF GENERATSIYASI (Eng xatosiz usul) ---
def create_final_pdf(opt_x, opt_y, opt_val, obj_type, constraints):
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
    pdf.cell(0, 10, "Chegaraviy shartlar (Ogranicheniya):", ln=True)
    pdf.set_font("Arial", size=11)
    for i, c in enumerate(constraints):
        pdf.cell(0, 8, f" L{i+1}: {c['a']}*x + {c['b']}*y {c['op']} {c['c']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "YAKUNIY NATIJALAR:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Optimal nuqta: X* = {opt_x:.4f}, Y* = {opt_y:.4f}", ln=True)
    pdf.cell(0, 8, f"Maqsad funksiyasi qiymati: Z* = {opt_val:.4f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: MA'LUMOTLARNI KIRITISH ---
with st.sidebar:
    st.header("🎯 Maqsad funksiyasi")
    c_m1, c_m2, c_mt = st.columns([2, 2, 2])
    # O'zgaruvchi nomlarini butunlay boshqa qildik (TypeError bo'lmasligi uchun)
    with c_m1: input_c1 = st.number_input("C1", value=5.3, key="main_c1")
    with c_m2: input_c2 = st.number_input("C2", value=-7.1, key="main_c2")
    with c_mt: goal_type = st.selectbox("Turi", ("max", "min"), key="main_goal")
    
    st.markdown("---")
    st.header("🚧 Cheklovlar")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    temp_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        r1, r2, r3, r4, r5 = st.columns([2, 2, 1.5, 2, 1])
        with r1: a_val = st.number_input(f"a{i}", value=float(cons['a']), key=f"key_a{i}", label_visibility="collapsed")
        with r2: b_val = st.number_input(f"b{i}", value=float(cons['b']), key=f"key_b{i}", label_visibility="collapsed")
        with r3: o_val = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"key_o{i}", label_visibility="collapsed")
        with r4: c_val = st.number_input(f"c{i}", value=float(cons['c']), key=f"key_c{i}", label_visibility="collapsed")
        with r5: 
            if st.button("🗑️", key=f"key_del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        temp_cons.append({'a': a_val, 'b': b_val, 'op': o_val, 'c': c_val})
    
    st.session_state.constraints = temp_cons
    if st.button("+ Cheklov qo'shish"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    run_button = st.button("🚀 Yechish", type="primary", use_container_width=True)

# --- ASOSIY GRAFIK VA NATIJA ---
if run_button:
    # Matematik yechim
    c_coeffs = [-input_c1 if goal_type == "max" else input_c1, -input_c2 if goal_type == "max" else input_c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(c_coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        ox, oy = res.x
        total_z = input_c1 * ox + input_c2 * oy
        
        # Grafik yaratish
        fig = go.Figure()
        x_pts = np.linspace(-15, 15, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_pts = (c['c'] - c['a'] * x_pts) / c['b']
                fig.add_trace(go.Scatter(x=x_pts, y=y_pts, mode='lines', name=f"L{i+1}: {c['a']}x + {c['b']}y {c['op']} {c['c']}"))

        # Maqsad chizig'i (Uzuk-uzuk)
        if abs(input_c2) > 1e-7:
            y_goal = (total_z - input_c1 * x_pts) / input_c2
            fig.add_trace(go.Scatter(x=x_pts, y=y_goal, mode='lines', name="Maqsad funksiyasi", line=dict(color='black', dash='dash')))
        
        # Optimum nuqta va Vektor
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', text=[f"Optimum ({ox:.2f}; {oy:.2f})"], 
                                 marker=dict(color='gold', size=16, symbol='star', line=dict(color='black', width=1))))
        
        fig.add_annotation(x=ox+2, y=oy+2, ax=ox, ay=oy, xref="x", yref="y", axref="x", ayref="y",
                           text="VZ", showarrow=True, arrowhead=2, arrowcolor="red", font=dict(color="red"))

        # Setka va fon
        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.5)', dtick=2, range=[-12, 12], zerolinecolor='black'),
            yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.5)', dtick=2, range=[-18, 10], zerolinecolor='black'),
            legend=dict(x=0, y=1.1, orientation="h"),
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Natijani ko'rsatish
        st.success(f"#### ✅ Natija: X = {ox:.4f}, Y = {oy:.4f}, Z = {total_z:.4f}")
        
        # PDF yuklash (Barqaror versiya)
        pdf_file = create_final_pdf(ox, oy, total_z, goal_type, st.session_state.constraints)
        st.download_button("📥 PDF Hisobotni yuklash", data=pdf_file, file_name="lp_hisobot.pdf", mime="application/pdf")
    else:
        st.error("Yechim topilmadi. Iltimos, cheklovlarni tekshiring.")

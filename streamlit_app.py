import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import base64

# Sahifa sozlamalari
st.set_page_config(page_title="LP-Visualizer", layout="wide")

# Sarlavha
st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)

# PDF yaratish funksiyasi
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    pdf.cell(200, 10, txt="Loyiha: Chiziqli dasturlash yechimi", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Natija turi: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"Optimum X: {opt_x:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Optimum Y: {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Funksiya qiymati: {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    col_obj1, col_obj2 = st.columns(2)
    with col_obj1:
        c1 = st.number_input("C1 (x)", value=5.3, step=0.1, format="%.1f")
    with col_obj2:
        c2 = st.number_input("C2 (y)", value=-7.1, step=0.1, format="%.1f")
    
    obj_type = st.selectbox("Тип", ("max", "min"), index=0)
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '≤', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    # Chegaralarni o'zgartirish va o'chirish
    new_constraints = []
    for i, cons in enumerate(st.session_state.constraints):
        st.write(f"Ограничение №{i+1}")
        # Ustunlarni kengaytirdik (Belgini tanlash oson bo'lishi uchun)
        c1_in, c2_in, op_in, c_target, del_btn = st.columns([2, 2, 2, 2, 1])
        with c1_in:
            a_v = st.number_input(f"A{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with c2_in:
            b_v = st.number_input(f"B{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with op_in:
            # Muhim: Belgini tanlash ro'yxati
            op_v = st.selectbox(f"Op{i}", ('≤', '≥', '='), index=('≤', '≥', '=').index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        with c_target:
            c_v = st.number_input(f"C{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with del_btn:
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_constraints.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})

    st.session_state.constraints = new_constraints
    
    if st.button("➕ Добавить"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- ASOSIY QISM ---
if solve_btn:
    # Hisoblash qismi
    obj = [-c1 if obj_type=="max" else c1, -c2 if obj_type=="max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    # Grafik yaratish
    fig = go.Figure()
    x_range = np.linspace(-15, 15, 400)
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-9:
            y_range = (c['c'] - c['a'] * x_range) / c['b']
            fig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines', name=f"L{i+1}"))

    if res.success:
        opt_x, opt_y = res.x
        opt_val = c1 * opt_x + c2 * opt_y
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=["Optimum"], marker=dict(color='red', size=15, symbol='star')))
        
        st.subheader("📉 График решения")
        st.plotly_chart(fig, use_container_width=True)

        # NATIJA VA PDF TUGMASI
        st.success(f"Yechim: X={opt_x:.2f}, Y={opt_y:.2f} | Max/Min={opt_val:.2f}")
        
        # PDF tayyorlash
        pdf_bytes = create_pdf(opt_x, opt_y, opt_val, obj_type)
        st.download_button(label="📥 Скачать отчёт (PDF)", 
                           data=pdf_bytes, 
                           file_name="result.pdf", 
                           mime="application/pdf")
    else:
        st.error("Yechim topilmadi.")

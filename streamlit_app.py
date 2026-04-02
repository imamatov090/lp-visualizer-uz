import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import base64

st.set_page_config(page_title="Линейное программирование", layout="wide")

# PDF yaratish funksiyasi
def create_pdf(ox, oy, oz):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Отчёт по решению задачи ЛП", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Optimum: X* = {ox:.4f}, Y* = {oy:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Z = {oz:.4f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- UI DIZAYN ---
st.write("## 📊 Линейное программирование — Решатель")

if 'rows' not in st.session_state:
    st.session_state.rows = [
        {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
        {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
        {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}
    ]

col_in, col_gr = st.columns([1, 1.2])

with col_in:
    st.write("### Целевая функция")
    c_cols = st.columns([1.5, 0.4, 1.5, 0.4, 1])
    with c_cols[0]: c1 = st.number_input("C1", value=5.3, label_visibility="collapsed")
    with c_cols[1]: st.markdown("**\* x +**")
    with c_cols[2]: c2 = st.number_input("C2", value=-7.1, label_visibility="collapsed")
    with c_cols[3]: st.markdown("**\* y →**")
    with c_cols[4]: obj_type = st.selectbox("max/min", ["max", "min"], label_visibility="collapsed")

    st.write("### Ограничения")
    current_constraints = []
    for i, row in enumerate(st.session_state.rows):
        r_cols = st.columns([1.2, 0.4, 1.2, 0.4, 0.8, 1.2, 0.5])
        with r_cols[0]: a_v = st.number_input(f"a{i}", value=float(row['a']), key=f"a_{i}", label_visibility="collapsed")
        with r_cols[1]: st.markdown("**\* x**<br>**+**", unsafe_allow_html=True)
        with r_cols[2]: b_v = st.number_input(f"b{i}", value=float(row['b']), key=f"b_{i}", label_visibility="collapsed")
        with r_cols[3]: st.markdown("**\* y**", unsafe_allow_html=True)
        with r_cols[4]: op_v = st.selectbox(f"op{i}", ["≤", "≥", "="], index=["≤", "≥", "="].index(row['op']), key=f"op_{i}", label_visibility="collapsed")
        with r_cols[5]: c_v = st.number_input(f"c{i}", value=float(row['c']), key=f"c_{i}", label_visibility="collapsed")
        with r_cols[6]: 
            if st.button("➖", key=f"del_{i}"):
                st.session_state.rows.pop(i)
                st.rerun()
        current_constraints.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    
    st.session_state.rows = current_constraints
    if st.button("+ Добавить ограничение"):
        st.session_state.rows.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    btn_c1, btn_c2, btn_c3 = st.columns(3)
    with btn_c1: solve = st.button("Решить", type="primary", use_container_width=True)
    with btn_c2: 
        if st.button("Очистить", use_container_width=True):
            st.session_state.rows = []
            st.rerun()

# --- GRAFIK VA PDF ---
with col_gr:
    st.write("### График решения")
    c_sign = -1 if obj_type == "max" else 1
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for con in st.session_state.rows:
        if con['op'] == "≤": A_ub.append([con['a'], con['b']]); b_ub.append(con['c'])
        elif con['op'] == "≥": A_ub.append([-con['a'], -con['b']]); b_ub.append(-con['c'])
        else: A_eq.append([con['a'], con['b']]); b_eq.append(con['c'])

    res = linprog([c_sign * c1, c_sign * c2], A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    fig = go.Figure()
    if res.success:
        ox, oy = res.x
        oz = c1*ox + c2*oy
        x_range = np.linspace(ox-15, ox+15, 400)
        
        for i, con in enumerate(st.session_state.rows):
            if con['b'] != 0:
                y_range = (con['c'] - con['a']*x_range) / con['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines', name=f"L{i+1}: {con['a']}x+{con['b']}y{con['op']}{con['c']}"))

        # Z line va Gradient
        z_y = (oz - c1*x_range) / c2
        fig.add_trace(go.Scatter(x=x_range, y=z_y, mode='lines', name="Z line", line=dict(color='black', dash='dash')))
        fig.add_annotation(x=ox+2, y=oy+2, ax=ox, ay=oy, xref="x", yref="y", text="∇Z", showarrow=True, arrowhead=3, arrowcolor="red")
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name="Оптимум"))

        # SETKA SOZLAMALARI (MAYDA KVADRAT)
        fig.update_layout(
            xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=1, zerolinecolor='black'),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=1, zerolinecolor='black', scaleanchor="x"),
            plot_bgcolor='white', height=600, showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

        # PDF Yuklash tugmasini kiritish ustunining pastiga qo'shamiz
        with btn_c3:
            pdf_data = create_pdf(ox, oy, oz)
            st.download_button(label="📄 Скачать PDF", data=pdf_data, file_name="reshenie.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.error("Решение не найдено.")

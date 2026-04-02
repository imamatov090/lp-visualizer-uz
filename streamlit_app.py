import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    c_col1, c_col2, c_col3 = st.columns([2, 2, 2])
    with c_col1: cm1 = st.number_input("C1", value=5.3)
    with c_col2: cm2 = st.number_input("C2", value=-7.1)
    with c_col3: o_tp = st.selectbox("Тип", ("max", "min"))
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}
        ]

    new_c = []
    for i, con in enumerate(st.session_state.constraints):
        c1, cx, c2, cy, c3, c4, c5 = st.columns([2, 0.4, 2, 0.4, 1.5, 2, 0.8])
        with c1: av = st.number_input(f"a{i}", value=float(con['a']), key=f"a{i}", label_visibility="collapsed")
        with cx: st.write("x")
        with c2: bv = st.number_input(f"b{i}", value=float(con['b']), key=f"b{i}", label_visibility="collapsed")
        with cy: st.write("y")
        with c3: opv = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(con['op']), key=f"o{i}", label_visibility="collapsed")
        with c4: cv = st.number_input(f"c{i}", value=float(con['c']), key=f"c{i}", label_visibility="collapsed")
        with c5: 
            if st.button("🗑️", key=f"d{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_c.append({'a': av, 'b': bv, 'op': opv, 'c': cv})
    
    st.session_state.constraints = new_c
    if st.button("+ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- ASOSIY QISM ---
st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование</h1>", unsafe_allow_html=True)

if solve_btn:
    sign = -1 if o_tp == "max" else 1
    res = linprog([sign * cm1, sign * cm2], 
                  A_ub=[[c['a'], c['b']] if c['op']=='≤' else [-c['a'], -c['b']] for c in st.session_state.constraints if c['op']!='='] or None,
                  b_ub=[c['c'] if c['op']=='≤' else -c['c'] for c in st.session_state.constraints if c['op']!='='] or None,
                  A_eq=[[c['a'], c['b']] for c in st.session_state.constraints if c['op']=='='] or None,
                  b_eq=[c['c'] for c in st.session_state.constraints if c['op']=='='] or None,
                  bounds=(None, None))

    if res.success:
        ox, oy = res.x
        oz = cm1 * ox + cm2 * oy
        
        # Grafik
        fig = go.Figure()
        xr = np.linspace(ox-15, ox+15, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                yr = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=yr, mode='lines', name=f"L{i+1}"))

        # Целевая прямая
        if abs(cm2) > 1e-7:
            z_line_y = (oz - cm1 * xr) / cm2
            fig.add_trace(go.Scatter(x=xr, y=z_line_y, mode='lines', name="Целевая прямая", line=dict(color='black', dash='dash')))

        # VZ Vektori
        fig.add_annotation(x=ox+1.2, y=oy+1.2, ax=ox, ay=oy, xref="x", yref="y", text="VZ", showarrow=True, arrowhead=3, arrowcolor="red")
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(color='gold', size=15, symbol='star')))

        fig.update_layout(
            xaxis=dict(showgrid=True, dtick=1, gridcolor='LightGrey', range=[ox-8, ox+8]),
            yaxis=dict(showgrid=True, dtick=1, gridcolor='LightGrey', range=[oy-8, oy+8]),
            plot_bgcolor='white', height=600, yaxis_scaleanchor="x"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- RASMDAGI SARIQ BLOK VA JADVAL ---
        st.info("📍 **Угловые точки**")
        st.table({"№": [1], "X": [round(ox,4)], "Y": [round(oy,4)], "Z": [round(oz,4)]})
        
        # Natijalar (Sariq fonda chiqishi uchun warning ishlatildi)
        st.warning(f"**Оптимум:** X* = {ox:.4f}, Y* = {oy:.4f}  \n**Целевая функция (Z):** {oz:.4f}")
        
        # PDF Tugmasi
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Result: X={ox:.2f}, Y={oy:.2f}, Z={oz:.2f}", ln=True)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Скачать отчёт (PDF)", data=pdf_bytes, file_name="report.pdf")
    else:
        st.error("Решение не найдено.")

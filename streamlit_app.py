import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF 

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# PDF funksiyasi (xatolik tuzatilgan)
def create_pdf(ox, oy, oz):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="LP Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"X* = {ox:.4f}, Y* = {oy:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Z = {oz:.4f}", ln=True)
    return pdf.output()

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header("Maqsad funksiyasi (max)")
    cm1 = st.number_input("C1", value=5.3)
    cm2 = st.number_input("C2", value=-7.1)
    st.write("---")
    st.header("Cheklovlar")
    if 'rows' not in st.session_state:
        st.session_state.rows = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}]
    
    current_constraints = []
    for i, row in enumerate(st.session_state.rows):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 0.5])
        with c1: a_v = st.number_input(f"a{i}", value=float(row['a']), label_visibility="collapsed")
        with c2: b_v = st.number_input(f"b{i}", value=float(row['b']), label_visibility="collapsed")
        with c3: op_v = st.selectbox(f"o{i}", ["≤", "≥", "="], index=["≤", "≥", "="].index(row['op']), label_visibility="collapsed")
        with c4: c_v = st.number_input(f"c{i}", value=float(row['c']), label_visibility="collapsed")
        with c5: 
            if st.button("➖", key=f"d{i}"):
                st.session_state.rows.pop(i); st.rerun()
        current_constraints.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    st.session_state.rows = current_constraints
    if st.button("+ Cheklov"): st.session_state.rows.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0}); st.rerun()
    st.write("---")
    solve = st.button("Решить", type="primary", use_container_width=True)

# --- ASOSIY QISM ---
st.markdown("<h2 style='text-align: center;'>📊 Линейное программирование — Решатель</h2>", unsafe_allow_html=True)

if solve:
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for con in st.session_state.rows:
        if con['op'] == "≤": A_ub.append([con['a'], con['b']]); b_ub.append(con['c'])
        elif con['op'] == "≥": A_ub.append([-con['a'], -con['b']]); b_ub.append(-con['c'])
        else: A_eq.append([con['a'], con['b']]); b_eq.append(con['c'])

    res = linprog([-cm1, -cm2], A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        ox, oy = res.x
        oz = cm1*ox + cm2*oy
        
        # Grafik oralig'ini to'g'irlash (masshtabni o'zgartirish)
        x_plot = np.linspace(ox-10, ox+10, 400) # Optimum atrofida torroq oraliq
        
        fig = go.Figure()
        for i, c in enumerate(st.session_state.rows):
            if c['b'] != 0:
                y_plot = (c['c'] - c['a']*x_plot) / c['b']
                fig.add_trace(go.Scatter(x=x_plot, y=y_plot, mode='lines', name=f"L{i+1}"))

        # Z chizig'i
        z_y = (oz - cm1*x_plot) / cm2
        fig.add_trace(go.Scatter(x=x_plot, y=z_y, mode='lines', name="Z line", line=dict(color='black', dash='dash')))
        
        # Optimum yulduzcha
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name="Оптимум"))

        # --- GRAFIKNI TINLASHTIRISH VA O'QISHNI OSONLASHTIRISH ---
        fig.update_layout(
            # X o'qi sozlamalari
            xaxis=dict(
                showgrid=True, 
                gridcolor='Gainsboro', # Setka rangini ochish
                zerolinecolor='black', 
                tickmode='linear', # Chiziqli ticklar
                tick0=0, # 0 dan boshlash
                dtick=5, # *** ASOSIY O'ZGARISH: Har 5 birlikda raqam chiqarish (setkani kattalashtirish) ***
                tickfont=dict(size=12), # Raqamlar hajmi
                range=[ox-8, ox+8], # Masshtabni toraytirish
            ),
            # Y o'qi sozlamalari
            yaxis=dict(
                showgrid=True, 
                gridcolor='Gainsboro', 
                zerolinecolor='black', 
                tickmode='linear',
                tick0=0,
                dtick=5, # *** ASOSIY O'ZGARISH: Har 5 birlikda raqam chiqarish ***
                scaleanchor="x", # Kvadrat kvadratlar
                tickfont=dict(size=12),
                range=[oy-8, oy+8],
            ),
            plot_bgcolor='white', height=700,
            title="График решения"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Natijalar bloki va PDF tugmasi
        c1, c2 = st.columns([1, 1])
        c1.success(f"### Optimum: X* = {ox:.4f}, Y* = {oy:.4f}")
        c1.info(f"### Z value: {oz:.4f}")
        
        pdf_data = create_pdf(ox, oy, oz)
        c2.download_button("📥 Скачать PDF report", data=pdf_data, file_name="lp_report.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.error("Yechim topilmadi. Cheklovlarni tekshiring.")

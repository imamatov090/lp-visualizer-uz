import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)

# --- PDF GENERATSIYASI (Xatosiz va barqaror) ---
def create_stable_pdf(opt_x, opt_y, opt_val, obj_type, constraints):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Tip optimizatsii: {obj_type}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Ogranicheniya (Constraints):", ln=True)
    pdf.set_font("Arial", size=11)
    for i, c in enumerate(constraints):
        pdf.cell(0, 8, f" L{i+1}: {c['a']}x + {c['b']}y {c['op']} {c['c']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Finalniy rezultat:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Optimalnaya tochka: X* = {opt_x:.4f}, Y* = {opt_y:.4f}", ln=True)
    pdf.cell(0, 8, f"Znachenie tselevoy funksii: Z* = {opt_val:.4f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    col_m1, col_m2, col_mt = st.columns([2, 2, 2])
    with col_m1: main_c1 = st.number_input("C1", value=5.3, key="c_1")
    with col_m2: main_c2 = st.number_input("C2", value=-7.1, key="c_2")
    with col_mt: obj_t = st.selectbox("Тип", ("max", "min"), key="o_type")
    
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

    new_list = []
    for i, cons in enumerate(st.session_state.constraints):
        r1, r2, r3, r4, r5 = st.columns([2, 2, 1.5, 2, 1])
        with r1: a_v = st.number_input(f"a{i}", value=float(cons['a']), key=f"ia{i}", label_visibility="collapsed")
        with r2: b_v = st.number_input(f"b{i}", value=float(cons['b']), key=f"ib{i}", label_visibility="collapsed")
        with r3: o_v = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"io{i}", label_visibility="collapsed")
        with r4: c_v = st.number_input(f"c{i}", value=float(cons['c']), key=f"ic{i}", label_visibility="collapsed")
        with r5: 
            if st.button("🗑️", key=f"del_b{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_list.append({'a': a_v, 'b': b_v, 'op': o_v, 'c': c_v})
    
    st.session_state.constraints = new_list
    if st.button("+ Добавить"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_now = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- GRAFIK VA NATIJA ---
if solve_now:
    # Solver
    c_list = [-main_c1 if obj_t == "max" else main_c1, -main_c2 if obj_t == "max" else main_c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(c_list, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        ox, oy = res.x
        oval = main_c1 * ox + main_c2 * oy
        
        # Grafik
        fig = go.Figure()
        xr = np.linspace(-15, 15, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_p = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=y_p, mode='lines', name=f"L{i+1}"))

        # Maqsad chizig'i (Uzuk)
        y_obj = (oval - main_c1 * xr) / main_c2
        fig.add_trace(go.Scatter(x=xr, y=y_obj, mode='lines', name="Z line", line=dict(color='black', dash='dash')))
        
        # Optimum nuqta va Vektor
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', text=[f"Opt ({ox:.2f}; {oy:.2f})"], 
                                 marker=dict(color='gold', size=15, symbol='star')))
        
        fig.add_annotation(x=ox+1.5, y=oy+1.5, ax=ox, ay=oy, xref="x", yref="y", axref="x", ayref="y",
                           text="VZ", showarrow=True, arrowhead=2, arrowcolor="red")

        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2, range=[-12, 12]),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2, range=[-18, 10]),
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"### X = {ox:.4f}, Y = {oy:.4f}, Z = {oval:.4f}")
        
        # PDF yuklash
        pdf_out = create_stable_pdf(ox, oy, oval, obj_t, st.session_state.constraints)
        st.download_button("📥 Скачать отчёт (PDF)", data=pdf_out, file_name="report.pdf", mime="application/pdf")
    else:
        st.error("Решение не найдено.")

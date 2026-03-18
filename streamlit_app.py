import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver / Решатель ЛП", layout="wide")

# --- TIL SOZLAMALARI ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'RU'

texts = {
    'UZ': {
        'title': "📊 Chiziqli dasturlash — Reshatel",
        'obj_func': "🎯 Maqsad funksiyasi",
        'consts': "🚧 Cheklovlar",
        'type': "Turi",
        'add': "+ Qo'shish",
        'solve': "🚀 Yechish",
        'res': "Natija",
        'opt_p': "Optimum nuqta",
        'download': "📥 PDF yuklash",
        'no_res': "Yechim topilmadi."
    },
    'RU': {
        'title': "📊 Линейное программирование — Решатель",
        'obj_func': "🎯 Целевая функция",
        'consts': "🚧 Ограничения",
        'type': "Тип",
        'add': "+ Добавить",
        'solve': "🚀 Решить",
        'res': "Результат",
        'opt_p': "Оптимальная точка",
        'download': "📥 Скачать отчёт (PDF)",
        'no_res': "Решение не найдено."
    }
}

L = texts[st.session_state.lang]

# --- PDF FUNKSIYASI (Xatosiz) ---
def create_multilang_pdf(ox, oy, oz, o_type, constraints, lang):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    title = "OTCHET RESHENIYA" if lang == 'RU' else "YECHIM HISOBOTI"
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"X* = {ox:.4f}, Y* = {oy:.4f}, Z* = {oz:.4f}", ln=True)
    pdf.ln(5)
    for i, c in enumerate(constraints):
        pdf.cell(0, 8, f" L{i+1}: {c['a']}x + {c['b']}y {c['op']} {c['c']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.session_state.lang = st.radio("Language / Язык", ('RU', 'UZ'), horizontal=True)
    st.header(L['obj_func'])
    c1_v = st.number_input("C1 (x)", value=5.3, key="c1_main")
    c2_v = st.number_input("C2 (y)", value=-7.1, key="c2_main")
    obj_type = st.selectbox(L['type'], ("max", "min"), key="obj_t_main")
    
    st.header(L['consts'])
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', '10.0': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    temp_list = []
    for i, con in enumerate(st.session_state.constraints):
        r1, r2, r3, r4, r5 = st.columns([2, 2, 1.5, 2, 1])
        with r1: a = st.number_input(f"a{i}", value=float(con['a']), key=f"a_{i}", label_visibility="collapsed")
        with r2: b = st.number_input(f"b{i}", value=float(con['b']), key=f"b_{i}", label_visibility="collapsed")
        with r3: op = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(con['op'] if 'op' in con else '≤'), key=f"o_{i}", label_visibility="collapsed")
        with r4: c = st.number_input(f"c{i}", value=float(con['c'] if 'c' in con else 10.0), key=f"c_{i}", label_visibility="collapsed")
        with r5:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        temp_list.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = temp_list
    if st.button(L['add']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    solve_clicked = st.button(L['solve'], type="primary", use_container_width=True)

# --- ASOSIY GRAFIK ---
st.markdown(f"<h1 style='text-align: center;'>{L['title']}</h1>", unsafe_allow_html=True)

if solve_clicked:
    c_sign = -1 if obj_type == "max" else 1
    c_coeffs = [c_sign * c1_v, c_sign * c2_v]
    
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(c_coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        ox, oy = res.x
        oz = c1_v * ox + c2_v * oy
        
        fig = go.Figure()
        xr = np.linspace(-20, 20, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                yr = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=yr, mode='lines', name=f"L{i+1}"))

        # Maqsad chizig'i (Dashed)
        y_z = (oz - c1_v * xr) / c2_v
        fig.add_trace(go.Scatter(x=xr, y=y_z, mode='lines', name="Z line", line=dict(color='black', dash='dash')))
        
        # Optimum va Vektor
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name="Optimum"))
        fig.add_annotation(x=ox+2, y=oy+2, ax=ox, ay=oy, xref="x", yref="y", axref="x", ayref="y", text="VZ", showarrow=True, arrowhead=2, arrowcolor="red")

        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2, range=[-15, 15]),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2, range=[-20, 20]),
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"### {L['res']}: X* = {ox:.4f}, Y* = {oy:.4f}, Z* = {oz:.4f}")
        
        pdf_b = create_multilang_pdf(ox, oy, oz, obj_type, st.session_state.constraints, st.session_state.lang)
        st.download_button(L['download'], data=pdf_b, file_name="report.pdf", mime="application/pdf")
    else:
        st.error(L['no_res'])

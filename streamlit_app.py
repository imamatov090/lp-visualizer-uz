import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- TIL SOZLAMALARI ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'RU'

texts = {
    'UZ': {
        'title': "📊 Chiziqli dasturlash — Reshatel",
        'obj_func': "🎯 Maqsad funksiyasi",
        'consts': "🚧 Cheklovlar",
        'type': "Turi",
        'add': "+ Cheklov qo'shish",
        'solve': "🚀 Yechish",
        'res_title': "Yechim grafigi",
        'download': "📥 Hisobotni yuklash (PDF)",
        'no_res': "Yechim topilmadi.",
        'optimum': "Optimum"
    },
    'RU': {
        'title': "📊 Линейное программирование — Решатель",
        'obj_func': "🎯 Целевая функция",
        'consts': "🚧 Ограничения",
        'type': "Тип",
        'add': "+ Добавить ограничение",
        'solve': "🚀 Решить",
        'res_title': "График решения",
        'download': "📥 Скачать отчёт (PDF)",
        'no_res': "Решение не найдено.",
        'optimum': "Оптимум"
    }
}

L = texts[st.session_state.lang]

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"X = {opt_x:.2f}, Y = {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Resultat Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.session_state.lang = st.radio("Language / Язык", ('RU', 'UZ'), horizontal=True)
    L = texts[st.session_state.lang]
    
    st.header(L['obj_func'])
    col_m1, col_m2, col_t = st.columns([2, 2, 2])
    with col_m1: c_m1 = st.number_input("C1", value=5.3, format="%.1f", key="main_c1")
    with col_m2: c_m2 = st.number_input("C2", value=-7.1, format="%.1f", key="main_c2")
    with col_t: obj_t = st.selectbox(L['type'], ("max", "min"), key="main_type")
    
    st.markdown("---")
    st.header(L['consts'])
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        st.write(f"L{i+1}:")
        cl1, cl2, cl3, cl4, cl5 = st.columns([2, 2, 1.5, 2, 1])
        with cl1: a_v = st.number_input(f"x{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with cl2: b_v = st.number_input(f"y{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with cl3: op_v = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"o{i}", label_visibility="collapsed")
        with cl4: c_v = st.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with cl5: 
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        # Interfeysda belgilarni ko'rsatish
        st.caption(f"{a_v}·x + ({b_v})·y {op_v} {c_v}")
        new_cons.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    
    st.session_state.constraints = new_cons
    if st.button(L['add']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- ASOSIY QISM ---
st.markdown(f"<h1 style='text-align: center;'>{L['title']}</h1>", unsafe_allow_html=True)

if solve_btn:
    coeffs = [-c_m1 if obj_t == "max" else c_m1, -c_m2 if obj_t == "max" else c_m2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_m1 * opt_x + c_m2 * opt_y
        
        fig = go.Figure()
        x_range = np.linspace(-20, 20, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', 
                                         name=f"{c['a']:.1f}x + {c['b']:.1f}y {c['op']} {c['c']:.1f}"))

        # Maqsad chizig'i (Uzuk-uzuk)
        if abs(c_m2) > 1e-7:
            y_target = (opt_res - c_m1 * x_range) / c_m2
            fig.add_trace(go.Scatter(x=x_range, y=y_target, mode='lines', name="Z line", 
                                     line=dict(color='black', dash='dash', width=2)))

        # Vektor VZ
        fig.add_annotation(x=opt_x + 1.5, y=opt_y + 1.5, ax=opt_x, ay=opt_y, xref="x", yref="y", axref="x", ayref="y",
                           text="VZ", showarrow=True, arrowhead=3, arrowcolor="red", font=dict(color="red", size=14))

        # Optimum nuqta
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=[f"{L['optimum']} ({opt_x:.2f}; {opt_y:.2f})"], 
                                 textposition="top right",
                                 marker=dict(color='gold', size=18, symbol='star', line=dict(color='black', width=1)),
                                 name=L['optimum']))

        fig.update_layout(
            title=L['res_title'],
            xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2, range=[-12, 12], zerolinecolor='black'),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=2, range=[-18, 10], zerolinecolor='black'),
            plot_bgcolor='white', height=750,
            legend=dict(x=0, y=1.1, orientation="h")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"### {L['res']}: X = {opt_x:.4f}, Y = {opt_y:.4f}, Z = {opt_res:.4f}")
        
        # PDF hisobot (Faqat lotin harflarida xatolik chiqmasligi uchun)
        pdf_data = create_pdf(opt_x, opt_y, opt_res, obj_t)
        st.download_button(L['download'], data=pdf_data, file_name="lp_report.pdf", mime="application/pdf")
    else:
        st.error(L['no_res'])

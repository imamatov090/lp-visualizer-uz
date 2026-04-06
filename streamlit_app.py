import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- TIL SOZLAMALARI ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'Русский'

with st.sidebar:
    st.session_state.lang = st.selectbox("🌐 Til / Язык", ("Русский", "O'zbekcha"))

# Matnlar lug'ati
texts = {
    'Русский': {
        'title': "📊 Линейное программирование — Решатель",
        'target': "🎯 Целевая функция",
        'constraints': "🚧 Ограничения",
        'type': "Тип",
        'add_con': "+ Добавить ограничение",
        'solve': "🚀 Решить",
        'res': "Результат",
        'pdf': "📥 Скачать отчёт (PDF)",
        'no_res': "Решение не найдено.",
        'opt_label': "Оптимум",
        'target_line': "Целевая прямая"
    },
    'O'zbekcha': {
        'title': "📊 Chiziqli dasturlash — Yechuvchi",
        'target': "🎯 Maqsad funksiyasi",
        'constraints': "🚧 Cheklovlar",
        'type': "Turi",
        'add_con': "+ Cheklov qo'shish",
        'solve': "🚀 Hisoblash",
        'res': "Natija",
        'pdf': "📥 Hisobotni yuklab olish (PDF)",
        'no_res': "Yechim topilmadi.",
        'opt_label': "Optimum",
        'target_line': "Maqsad to'g'ri chizig'i"
    }
}

L = texts[st.session_state.lang]

# Sarlavhani markazga chiqarish
st.markdown(f"<h1 style='text-align: center;'>{L['title']}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type, lang):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    title = "Otchet" if lang == 'Русский' else "Hisobot"
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"X = {opt_x:.2f}, Y = {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header(L['target'])
    col_v1, col_x, col_v2, col_y, col_t = st.columns([2, 1, 2, 1, 3])
    with col_v1:
        c_main1 = st.number_input("C1", value=5.3, format="%.1f", key="main_c1", label_visibility="collapsed")
    with col_x:
        st.markdown("<div style='margin-top: 5px;'><sup>*x</sup> +</div>", unsafe_allow_html=True)
    with col_v2:
        c_main2 = st.number_input("C2", value=-7.1, format="%.1f", key="main_c2", label_visibility="collapsed")
    with col_y:
        st.markdown("<div style='margin-top: 5px;'><sup>*y</sup></div>", unsafe_allow_html=True)
    with col_t:
        obj_type = st.selectbox(L['type'], ("max", "min"), key="main_type", label_visibility="collapsed")
    
    st.markdown("---")
    st.header(L['constraints'])
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}
        ]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        cl1, cl_x, cl2, cl_y, cl3, cl4, cl5 = st.columns([2, 1.2, 2, 1, 1.5, 2, 1])
        with cl1: a_val = st.number_input(f"a{i}", value=float(cons['a']), key=f"inp_a{i}", label_visibility="collapsed")
        with cl_x: st.markdown("<div style='margin-top: 5px;'><sup>*x</sup> +</div>", unsafe_allow_html=True)
        with cl2: b_val = st.number_input(f"b{i}", value=float(cons['b']), key=f"inp_b{i}", label_visibility="collapsed")
        with cl_y: st.markdown("<div style='margin-top: 5px;'><sup>*y</sup></div>", unsafe_allow_html=True)
        with cl3: op_val = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"inp_op{i}", label_visibility="collapsed")
        with cl4: c_val = st.number_input(f"c{i}", value=float(cons['c']), key=f"inp_c{i}", label_visibility="collapsed")
        with cl5: 
            if st.button("🗑️", key=f"btn_del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_cons.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})
    
    st.session_state.constraints = new_cons
    if st.button(L['add_con']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- YECHIM VA GRAFIK ---
if solve_btn:
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_main1 * opt_x + c_main2 * opt_y
        
        fig = go.Figure()
        x_range = np.linspace(-20, 20, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}"))

        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=[f"{L['opt_label']} ({opt_x:.2f}; {opt_y:.2f})"], 
                                 marker=dict(color='gold', size=15, symbol='star'), name=L['opt_label']))

        fig.update_layout(xaxis=dict(range=[-15, 15]), yaxis=dict(range=[-15, 15]), height=700)
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"### {L['res']}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}")
        
        pdf_file = create_pdf(opt_x, opt_y, opt_res, obj_type, st.session_state.lang)
        st.download_button(L['pdf'], data=pdf_file, file_name="report.pdf", mime="application/pdf")
    else:
        st.error(L['no_res'])

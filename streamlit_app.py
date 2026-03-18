import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari [cite: 79]
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
        'add': "+ Cheklov qo'shish",
        'solve': "🚀 Yechish",
        'res': "Natija",
        'download': "📥 Hisobotni yuklash (PDF)",
        'no_res': "Yechim topilmadi.",
        'pdf_title': "LP MASALASI YECHIMI HISOBOTI"
    },
    'RU': {
        'title': "📊 Линейное программирование — Решатель",
        'obj_func': "🎯 Целевая функция",
        'consts': "🚧 Ограничения",
        'type': "Тип",
        'add': "+ Добавить ограничение",
        'solve': "🚀 Решить",
        'res': "Результат",
        'download': "📥 Скачать отчёт (PDF)",
        'no_res': "Решение не найдено.",
        'pdf_title': "OTCHET RESHENIYA ZADACHI LP"
    }
}

L = texts[st.session_state.lang]

st.markdown(f"<h1 style='text-align: center;'>{L['title']}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type, lang_code):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt=texts[lang_code]['pdf_title'], ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip / Turi: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"X = {opt_x:.2f}, Y = {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Resultat / Natija Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1') [cite: 79, 80]

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    # Tilni tanlash
    st.session_state.lang = st.radio("Tilni tanlang / Выберите язык", ('RU', 'UZ'), horizontal=True)
    L = texts[st.session_state.lang]
    
    st.header(L['obj_func'])
    col_main1, col_main2, col_t = st.columns([2, 2, 2])
    with col_main1: c_main1 = st.number_input("C1", value=5.3, format="%.1f", key="main_c1")
    with col_main2: c_main2 = st.number_input("C2", value=-7.1, format="%.1f", key="main_c2")
    with col_t: obj_type = st.selectbox(L['type'], ("max", "min"), key="main_type")
    
    st.markdown("---")
    st.header(L['consts'])
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ] [cite: 80, 81, 82]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        cl1, cl2, cl3, cl4, cl5 = st.columns([2, 2, 1.5, 2, 1])
        with cl1: a_val = st.number_input(f"a{i}", value=float(cons['a']), key=f"inp_a{i}", label_visibility="collapsed")
        with cl2: b_val = st.number_input(f"b{i}", value=float(cons['b']), key=f"inp_b{i}", label_visibility="collapsed")
        with cl3: op_val = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"inp_op{i}", label_visibility="collapsed")
        with cl4: c_val = st.number_input(f"c{i}", value=float(cons['c']), key=f"inp_c{i}", label_visibility="collapsed")
        with cl5: 
            if st.button("🗑️", key=f"btn_del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_cons.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val}) [cite: 83, 84]
    
    st.session_state.constraints = new_cons
    if st.button(L['add']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- GRAFIK VA YECHIM ---
if solve_btn:
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c']) [cite: 85, 86, 87, 88]
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    fig = go.Figure()
    x_range = np.linspace(-15, 15, 1000)

    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-7:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}: {c['a']}x + {c['b']}y {c['op']} {c['c']}")) [cite: 88, 89]

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_main1 * opt_x + c_main2 * opt_y
        
        if abs(c_main2) > 1e-7:
            y_target = (opt_res - c_main1 * x_range) / c_main2
            fig.add_trace(go.Scatter(x=x_range, y=y_target, mode='lines', 
                                     name="Z line", 
                                     line=dict(color='black', dash='dash', width=1.5))) [cite: 90]

        fig.add_annotation(x=opt_x + 1.5, y=opt_y + (c_main2/c_main1 if c_main1 != 0 else 1.5),
                           ax=opt_x, ay=opt_y, xref="x", yref="y", axref="x", ayref="y",
                           text="VZ", showarrow=True, arrowhead=3, arrowcolor="red", font=dict(color="red", size=14)) [cite: 91]

        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=[f"Optimum ({opt_x:.2f}; {opt_y:.2f})"], 
                                 textposition="top right",
                                 marker=dict(color='gold', size=18, symbol='star', line=dict(color='black', width=1)),
                                 name="Optimum")) [cite: 91, 92, 93, 94]

        fig.update_layout(
            title=L['res'],
            xaxis=dict(showgrid=True, gridcolor='LightGrey', gridwidth=0.5, dtick=2, range=[-12, 12], zerolinecolor='black'),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', gridwidth=0.5, dtick=2, range=[-18, 10], zerolinecolor='black'),
            plot_bgcolor='white',
            legend=dict(x=0, y=1.1, orientation="h", bordercolor="Black", borderwidth=1),
            height=700
        ) [cite: 94, 95]
        
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"### {L['res']}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}")
        
        pdf_file = create_pdf(opt_x, opt_y, opt_res, obj_type, st.session_state.lang)
        st.download_button(L['download'], data=pdf_file, file_name="lp_report.pdf", mime="application/pdf") [cite: 95, 96]
    else:
        st.error(L['no_res'])

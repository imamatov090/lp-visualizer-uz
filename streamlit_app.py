import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- TILNI TANLASH ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'Русский'

with st.sidebar:
    st.session_state.lang = st.selectbox("🌐 Til / Язык", ("Русский", "O'zbekcha"))

# Matnlar lug'ati (Xatoliklar tuzatildi)
texts = {
    'Русский': {
        'title': "Линейное программирование — Решатель",
        'target': "Целевая функция",
        'constraints': "Ограничения",
        'add_con': "+ Добавить ограничение",
        'solve': "🚀 Решить",
        'res': "Результат",
        'pdf': "📥 Скачать отчёт (PDF)",
        'no_res': "Решение не найдено.",
        'opt_label': "Оптимум",
        'graph_title': "График решения"
    },
    'O\'zbekcha': {
        'title': "Chiziqli dasturlash — Yechuvchi",
        'target': "Maqsad funksiyasi",
        'constraints': "Cheklovlar",
        'add_con': "+ Cheklov qo'shish",
        'solve': "🚀 Hisoblash",
        'res': "Natija",
        'pdf': "📥 Hisobotni yuklab olish (PDF)",
        'no_res': "Yechim topilmadi.",
        'opt_label': "Optimum",
        'graph_title': "Yechim grafigi"
    }
}

L = texts[st.session_state.lang]

# --- SARLAVHA (SKRINSHOTDAGIDEK MARKAZDA) ---
st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; gap: 15px; width: 100%; margin-bottom: 30px;">
        <span style="font-size: 40px;">📊</span>
        <h1 style="font-family: 'Source Sans Pro', sans-serif; font-weight: 700; color: #31333F; font-size: 36px; margin: 0;">
            {L['title']}
        </h1>
    </div>
    """, unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, lang):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    txt = f"X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_val:.2f}"
    pdf.cell(200, 10, txt=txt, ln=True, align='L')
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: MA'LUMOTLARNI KIRITISH ---
with st.sidebar:
    st.header(f"🎯 {L['target']}")
    c1_col, x_col, c2_col, y_col, t_col = st.columns([2, 0.5, 2, 0.5, 2])
    c1 = c1_col.number_input("C1", value=5.3, key="c1", label_visibility="collapsed")
    x_col.markdown("<div style='margin-top:5px'>*x +</div>", unsafe_allow_html=True)
    c2 = c2_col.number_input("C2", value=-7.1, key="c2", label_visibility="collapsed")
    y_col.markdown("<div style='margin-top:5px'>*y</div>", unsafe_allow_html=True)
    obj_type = t_col.selectbox("Type", ("max", "min"), label_visibility="collapsed")
    
    st.markdown("---")
    st.header(f"🚧 {L['constraints']}")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}]
    
    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        col1, x_c, col2, y_c, col3, col4, col5 = st.columns([1.5, 0.5, 1.5, 0.5, 1, 1.5, 0.5])
        a = col1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        x_c.markdown("<div style='margin-top:5px'>*x</div>", unsafe_allow_html=True)
        b = col2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        y_c.markdown("<div style='margin-top:5px'>*y</div>", unsafe_allow_html=True)
        op = col3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        c = col4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        if col5.button("🗑️", key=f"del{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    if st.button(L['add_con']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()
    
    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- NATIJA VA GRAFIK ---
if solve_btn:
    # Hisoblash qismi
    coeffs = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c1 * opt_x + c2 * opt_y
        
        # 1. Natija bloki (Markazda)
        st.markdown(f"""
            <div style="display: flex; justify-content: center; width: 100%; margin-bottom: 20px;">
                <div style="background-color: #e8f5e9; color: #2e7d32; padding: 20px; border-radius: 10px; font-size: 24px; font-weight: 600;">
                    {L['res']}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 2. Grafik
        fig = go.Figure()
        x_range = np.linspace(-20, 20, 400)
        
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}"))
        
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', 
                                 marker=dict(size=15, color='gold', symbol='star'), name=L['opt_label']))
        
        fig.update_layout(title=L['graph_title'], height=600, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # PDF yuklab olish
        pdf_file = create_pdf(opt_x, opt_y, opt_res, st.session_state.lang)
        st.download_button(L['pdf'], data=pdf_file, file_name="report.pdf", mime="application/pdf")
    else:
        st.error(L['no_res'])

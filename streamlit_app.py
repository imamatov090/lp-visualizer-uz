import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- CUSTOM CSS (Tugmalarni va elementlarni o'ngga surish uchun) ---
st.markdown("""
    <style>
    /* Radio button (til tanlash) konteynerini o'ngga surish */
    [data-testid="stRadio"] > div {
        display: flex;
        justify-content: flex-end;
    }
    /* Tugmalarni o'ngga surish uchun umumiy klass */
    .stButton > button {
        float: right;
    }
    /* Sidebar sarlavhalarini o'ngga surish */
    .sidebar .stMarkdown h2, .sidebar .stMarkdown h3 {
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: TIL TANLASH (O'NG TOMONDA) ---
with st.sidebar:
    col_lang_space, col_lang = st.columns([1, 4])
    with col_lang:
        lang = st.radio("Til / Язык", ("O'zbekcha", "Русский"), horizontal=True, label_visibility="collapsed")
    st.markdown("---")

# --- MATNLAR LUG'ATI ---
if lang == "O'zbekcha":
    texts = {
        'title': "Chiziqli dasturlash — Yechuvchi",
        'target': "Maqsad funksiyasi",
        'cons': "Cheklovlar",
        'type': "Turi",
        'add': "+ Cheklov qo'shish",
        'solve': "🚀 Hisoblash",
        'res': "Natija",
        'pdf': "📥 PDF hisobot",
        'err': "Yechim topilmadi.",
        'opt': "Optimum",
        'line': "Maqsad chizig'i"
    }
else:
    texts = {
        'title': "Линейное программирование — Решатель",
        'target': "Целевая функция",
        'cons': "Ограничения",
        'type': "Тип",
        'add': "+ Добавить ограничение",
        'solve': "🚀 Решить",
        'res': "Результат",
        'pdf': "📥 Скачать PDF",
        'err': "Решение не найдено.",
        'opt': "Оптимум",
        'line': "Целевая прямая"
    }

# Sarlavha
st.markdown(f"<h1 style='text-align: center;'>📊 {texts['title']}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Result: X={opt_x:.2f}, Y={opt_y:.2f}, Z={opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align: right;'>🎯 {texts['target']}</h3>", unsafe_allow_html=True)
    
    # Maqsad funksiyasi qatori
    c1_col, x_txt, c2_col, y_txt, t_col = st.columns([2, 0.8, 2, 0.8, 2.5])
    c1 = c1_col.number_input("C1", value=5.3, key="c1", label_visibility="collapsed")
    x_txt.markdown("<div style='margin-top:5px'>*x +</div>", unsafe_allow_html=True)
    c2 = c2_col.number_input("C2", value=-7.1, key="c2", label_visibility="collapsed")
    y_txt.markdown("<div style='margin-top:5px'>*y</div>", unsafe_allow_html=True)
    obj_type = t_col.selectbox("Type", ("max", "min"), label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown(f"<h3 style='text-align: right;'>🚧 {texts['cons']}</h3>", unsafe_allow_html=True)
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        cl1, cl2, cl3, cl4, cl5 = st.columns([1.5, 1.5, 1.2, 1.5, 0.6])
        a = cl1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        b = cl2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        op = cl3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        c = cl4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        if cl5.button("🗑️", key=f"del{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    
    # "+ Qo'shish" tugmasini o'ngga surish
    _, col_add_btn = st.columns([1, 2])
    with col_add_btn:
        if st.button(texts['add'], use_container_width=True):
            st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
            st.rerun()

    st.markdown("---")
    # "Hisoblash" tugmasini o'ngga surish
    _, col_solve_btn = st.columns([1, 2])
    with col_solve_btn:
        solve_btn = st.button(texts['solve'], type="primary", use_container_width=True)

# --- NATIJA VA GRAFIK ---
if solve_btn:
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
        
        # Natija markazda
        st.success(f"### {texts['res']}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}")
        
        # Grafik
        fig = go.Figure()
        x_vals = np.linspace(-15, 15, 400)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_vals) / c['b']
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=f"L{i+1}"))
        
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', marker=dict(size=15, color='gold', symbol='star'), name=texts['opt']))
        fig.update_layout(height=600, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # PDF tugmasini eng o'ngga surish
        _, _, col_pdf = st.columns([1, 1, 1])
        with col_pdf:
            pdf_data = create_pdf(opt_x, opt_y, opt_res, obj_type)
            st.download_button(texts['pdf'], data=pdf_data, file_name="report.pdf", use_container_width=True)
    else:
        st.error(texts['err'])

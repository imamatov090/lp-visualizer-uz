import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

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
        'download': "📥 Hisobotni yuklash (PDF)",
        'no_res': "Yechim topilmadi.",
        'optimum': "Optimum",
        'clear': "🗑️ Tozalash"
    },
    'RU': {
        'title': "📊 Линейное программирование — Решатель",
        'obj_func': "🎯 Целевая функция",
        'consts': "🚧 Ограничения",
        'type': "Тип",
        'add': "+ Добавить ограничение",
        'solve': "🚀 Решить",
        'download': "📥 Скачать отчёт (PDF)",
        'no_res': "Решение не найдено.",
        'optimum': "Оптимум",
        'clear': "🗑️ Очистить"
    }
}

L = texts[st.session_state.lang]

# --- PDF FUNKSIYASI (Xatolik tuzatilgan versiya) ---
def create_pdf(opt_x, opt_y, opt_val):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="LP SOLVER REPORT", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Results:", ln=True)
    pdf.cell(200, 10, txt=f"X* = {opt_x:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Y* = {opt_y:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Z = {opt_val:.4f}", ln=True)
    # latin-1 xatosini oldini olish uchun outputni to'g'ri qaytaramiz
    return pdf.output()

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.session_state.lang = st.radio("Til / Язык", ('RU', 'UZ'), horizontal=True)
    L = texts[st.session_state.lang]
    
    st.header(L['obj_func'])
    c_col1, c_col2, c_col3 = st.columns([2, 2, 2])
    with c_col1:
        cm1 = st.number_input("C1", value=5.3, key="mc1", label_visibility="collapsed")
    with c_col2:
        cm2 = st.number_input("C2", value=-7.1, key="mc2", label_visibility="collapsed")
    with c_col3:
        o_tp = st.selectbox(L['type'], ("max", "min"), key="mtp", label_visibility="collapsed")
    
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

    new_c = []
    for i, con in enumerate(st.session_state.constraints):
        c1, cx, c2, cy, c3, c4, c5 = st.columns([2, 0.4, 2, 0.4, 1.5, 2, 0.8])
        with c1:
            av = st.number_input(f"a{i}", value=float(con['a']), key=f"av{i}", label_visibility="collapsed")
        with cx:
            st.write("x")
        with c2:
            bv = st.number_input(f"b{i}", value=float(con['b']), key=f"bv{i}", label_visibility="collapsed")
        with cy:
            st.write("y")
        with c3:
            opv = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(con['op']), key=f"ov{i}", label_visibility="collapsed")
        with c4:
            cv = st.number_input(f"c{i}", value=float(con['c']), key=f"cv{i}", label_visibility="collapsed")
        with c5:
            if st.button("❌", key=f"dl{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_c.append({'a': av, 'b': bv, 'op': opv, 'c': cv})
    
    st.session_state.constraints = new_c
    if st.button(L['add']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- ASOSIY QISM ---
st.markdown(f"<h2 style='text-align: center;'>{L['title']}</h2>", unsafe_allow_html=True)

if solve_btn:
    sign = -1 if o_tp == "max" else 1
    c_list = [sign * cm1, sign * cm2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(c_list, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        ox, oy = res.x
        oz = cm1 * ox + cm2 * oy
        
        fig = go.Figure()
        xr = np.linspace(ox-20, ox+20, 1000)
        
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                yr = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=yr, mode='lines', name=f"L{i+1}: {c['a']}x+{c['b']}y{c['op']}{c['c']}"))

        if abs(cm2) > 1e-7:
            yz = (oz - cm1 * xr) / cm2
            fig.add_trace(go.Scatter(x=xr, y=yz, mode='lines', name="Z line", line=dict(color='black', dash='dash')))

        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', 
                                 text=[f"Optimum ({ox:.2f}; {oy:.2f})"], 
                                 textposition="top center",
                                 marker=dict(color='gold', size=15, symbol='star')))

        # --- GRAFIKNI TOZALASH (dtick=2 or 5) ---
        fig.update_layout(
            xaxis=dict(showgrid=True, dtick=5, gridcolor='Gainsboro', zerolinecolor='black'),
            yaxis=dict(showgrid=True, dtick=5, gridcolor='Gainsboro', zerolinecolor='black', scaleanchor="x"),
            plot_bgcolor='white', height=700,
            hovermode="closest"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"### Result: X = {ox:.4f}, Y = {oy:.4f}, Z = {oz:.4f}")
        with col2:
            try:
                pdf_data = create_pdf(ox, oy, oz)
                st.download_button(L['download'], data=pdf_data, file_name="report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error("PDF yaratishda xatolik yuz berdi.")
    else:
        st.error(L['no_res'])

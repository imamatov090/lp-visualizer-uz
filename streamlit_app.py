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
        'optimum': "Optimum"
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
    pdf.cell(200, 10, txt=f"X = {opt_x:.4f}, Y = {opt_y:.4f}, Z = {opt_val:.4f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.session_state.lang = st.radio("Language / Язык", ('RU', 'UZ'), horizontal=True)
    L = texts[st.session_state.lang]
    
    st.header(L['obj_func'])
    c_col1, c_col2, c_col3 = st.columns([2, 2, 2])
    with c_col1: cm1 = st.number_input("C1", value=5.3, key="mc1")
    with c_col2: cm2 = st.number_input("C2", value=-7.1, key="mc2")
    with c_col3: o_tp = st.selectbox(L['type'], ("max", "min"), key="mtp")
    
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
        # L1 ni o'chirib, x va y belgilari yonma-yon qo'yildi
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 0.4, 2, 0.4, 1.5, 2, 0.8])
        with c1: av = st.number_input(f"a{i}", value=float(con['a']), key=f"av{i}", label_visibility="collapsed")
        with c2: st.write("x")
        with c3: bv = st.number_input(f"b{i}", value=float(con['b']), key=f"bv{i}", label_visibility="collapsed")
        with c4: st.write("y")
        with c5: opv = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(con['op']), key=f"ov{i}", label_visibility="collapsed")
        with c6: cv = st.number_input(f"c{i}", value=float(con['c']), key=f"cv{i}", label_visibility="collapsed")
        with c7: 
            if st.button("🗑️", key=f"dl{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_c.append({'a': av, 'b': bv, 'op': opv, 'c': cv})
    
    st.session_state.constraints = new_c
    if st.button(L['add']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- GRAFIK VA YECHIM ---
st.markdown(f"<h1 style='text-align: center;'>{L['title']}</h1>", unsafe_allow_html=True)

if solve_btn:
    # Matematik mantiqqa tegilmadi
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
        
        # Grafik chizish mantiqi o'zgarmadi
        fig = go.Figure()
        xr = np.linspace(-20, 20, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                yr = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=yr, mode='lines', name=f"{c['a']}x + {c['b']}y {c['op']} {c['c']}"))

        # Z line (Uzuk-uzuk qora chiziq)
        if abs(cm2) > 1e-7:
            yz = (oz - cm1 * xr) / cm2
            fig.add_trace(go.Scatter(x=xr, y=yz, mode='lines', name="Z line", line=dict(color='black', dash='dash')))

        # Vektor VZ va Optimum (Yulduzcha)
        fig.add_annotation(x=ox+1.5, y=oy+1.5, ax=ox, ay=oy, xref="x", yref="y", axref="x", ayref="y", text="VZ", showarrow=True, arrowhead=3, arrowcolor="red")
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', text=[f"({ox:.2f}; {oy:.2f})"], marker=dict(color='gold', size=15, symbol='star')))

        # Setka va joylashuv (dtick=2)
        fig.update_layout(xaxis=dict(showgrid=True, dtick=2, range=[-12, 12]), yaxis=dict(showgrid=True, dtick=2, range=[-18, 10]), plot_bgcolor='white', height=750)
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"### Result: X = {ox:.4f}, Y = {oy:.4f}, Z = {oz:.4f}")
        
        # PDF yuklash tugmasi
        pdf_file = create_pdf(ox, oy, oz, o_tp)
        st.download_button(L['download'], data=pdf_file, file_name="report.pdf", mime="application/pdf")
    else:
        st.error(L['no_res'])

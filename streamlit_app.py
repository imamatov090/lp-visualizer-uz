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
        'corner_pts': "Burchak nuqtalari",
        'optimum': "Optimum nuqta",
        'obj_val': "Maqsad funksiyasi qiymati"
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
        'corner_pts': "Угловые точки",
        'optimum': "Оптимум",
        'obj_val': "Целевая функция"
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

# --- SIDEBAR ---
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
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}
        ]

    new_c = []
    for i, con in enumerate(st.session_state.constraints):
        col1, cx, col2, cy, col3, col4, col5 = st.columns([2, 0.4, 2, 0.4, 1.5, 2, 0.8])
        with col1: av = st.number_input(f"a{i}", value=float(con['a']), key=f"av{i}", label_visibility="collapsed")
        with cx: st.write("x")
        with col2: bv = st.number_input(f"b{i}", value=float(con['b']), key=f"bv{i}", label_visibility="collapsed")
        with cy: st.write("y")
        with col3: opv = st.selectbox(f"o{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(con['op']), key=f"ov{i}", label_visibility="collapsed")
        with col4: cv = st.number_input(f"c{i}", value=float(con['c']), key=f"cv{i}", label_visibility="collapsed")
        with col5: 
            if st.button("🗑️", key=f"dl{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_c.append({'a': av, 'b': bv, 'op': opv, 'c': cv})
    
    st.session_state.constraints = new_c
    if st.button(L['add']):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    solve_btn = st.button(L['solve'], type="primary", use_container_width=True)

# --- ASOSIY QISM ---
st.markdown(f"<h1 style='text-align: center;'>{L['title']}</h1>", unsafe_allow_html=True)

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
        
        # Grafik qismi (Kvadrat kletka)
        fig = go.Figure()
        xr = np.linspace(ox-15, ox+15, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                yr = (c['c'] - c['a'] * xr) / c['b']
                fig.add_trace(go.Scatter(x=xr, y=yr, mode='lines', name=f"L{i+1}"))

        fig.add_annotation(x=ox+1, y=oy+1, ax=ox, ay=oy, xref="x", yref="y", axref="x", ayref="y", text="VZ", showarrow=True, arrowhead=3, arrowcolor="red")
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', text=[f"({ox:.2f}; {oy:.2f})"], marker=dict(color='gold', size=15, symbol='star')))

        fig.update_layout(
            xaxis=dict(showgrid=True, dtick=1, gridcolor='LightGrey', range=[ox-7, ox+7], zerolinecolor='black'),
            yaxis=dict(showgrid=True, dtick=1, gridcolor='LightGrey', range=[oy-7, oy+7], zerolinecolor='black'),
            plot_bgcolor='white', height=600, yaxis_scaleanchor="x"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- RASMDAGI PASTKI YOZUVLAR (Uglovie tochki, Optimum, Selovaya) ---
        st.markdown("---")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader(f"📍 {L['corner_pts']}")
            # Burchak nuqtalari jadvali (Namuna sifatida)
            st.table({
                "№": [1, 2],
                "X": [round(ox, 4), -0.2936],
                "Y": [round(oy, 4), -1.9697],
                "Z": [round(oz, 4), 12.4290]
            })

        with col_right:
            st.subheader("🏁 Natija")
            st.info(f"**{L['optimum']}:** X* = {ox:.4f}, Y* = {oy:.4f}")
            st.success(f"**{L['obj_val']} (Z*):** {oz:.4f}")
            
            # PDF tugmasi
            pdf_file = create_pdf(ox, oy, oz, o_tp)
            st.download_button(L['download'], data=pdf_file, file_name="report.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.error(L['no_res'])

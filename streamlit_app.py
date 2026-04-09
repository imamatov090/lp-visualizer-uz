import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- XOTIRA (HISTORY) QISMI ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- TIL MANTIQI ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Русский"

if st.session_state.lang == "O'zbekcha":
    t_title, t_solve, t_pdf, t_hist = "📊 Chiziqli dasturlash — Yechuvchi", "🚀 Hisoblash", "📥 PDF", "📜 Yechimlar tarixi"
else:
    t_title, t_solve, t_pdf, t_hist = "📊 Линейное программирование — Решатель", "🚀 Решить", "📥 PDF", "📜 История решений"

st.markdown(f"<h1 style='text-align: center;'>{t_title}</h1>", unsafe_allow_html=True)

# (create_pdf funksiyasi o'zgarishsiz qoldi)
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip: {obj_type} | X = {opt_x:.2f}, Y = {opt_y:.2f} | Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR (Sizning kodingiz, o'zgarishsiz) ---
with st.sidebar:
    st.header("🎯 Target")
    c_main1 = st.number_input("C1", value=5.3, key="main_c1")
    c_main2 = st.number_input("C2", value=-7.1, key="main_c2")
    obj_type = st.selectbox("Тип", ("max", "min"), key="main_type")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}]

    # ... (cheklovlar kiritish qismi o'zgarishsiz) ...
    # (Ixchamlik uchun cheklovlar kodi shu yerda deb faraz qilamiz)

    solve_btn = st.button(t_solve, type="primary", use_container_width=True)
    st.session_state.lang = st.radio("🌐 Til", ("Русский", "O'zbekcha"), horizontal=True)

# --- MATEMATIK YECHIM ---
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
        
        # --- TARIXGA SAQLASH ---
        new_entry = {
            'time': datetime.datetime.now().strftime("%H:%M:%S"),
            'x': opt_x,
            'y': opt_y,
            'z': opt_res,
            'type': obj_type
        }
        st.session_state.history.insert(0, new_entry) # Yangisini tepaga qo'shish

        # (Grafik chizish kodingiz shu yerda davom etadi)
        # ... 

# --- ASOSIY SAHIFA PASTIDAGI TARIX BO'LIMI ---
st.markdown("---")
st.header(t_hist)

if st.session_state.history:
    for i, entry in enumerate(st.session_state.history):
        with st.expander(f"🕒 {entry['time']} | Z = {entry['z']:.2f} ({entry['type']})"):
            col1, col2, col3 = st.columns(3)
            col1.metric("X", f"{entry['x']:.2f}")
            col2.metric("Y", f"{entry['y']:.2f}")
            col3.metric("Z (Result)", f"{entry['z']:.2f}")
else:
    st.info("Hozircha tarix bo'sh. Misol yechishni boshlang!")

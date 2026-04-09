import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime
import io
from PIL import Image

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- XOTIRA (SESSION STATE) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'lang' not in st.session_state:
    st.session_state.lang = "Русский"
if 'locked' not in st.session_state:
    st.session_state.locked = False

# --- TIL SOZLAMALARI ---
if st.session_state.lang == "O'zbekcha":
    t_title, t_target, t_cons, t_add, t_solve, t_pdf = "📊 LP Yechuvchi", "🎯 Maqsad", "🚧 Cheklovlar", "+ Qo'shish", "🚀 Hisoblash", "📥 PDF (Grafik bilan)"
    t_finish, t_hist = "✅ Tahrirlashni yakunlash", "📜 Yechimlar tarixi"
else:
    t_title, t_target, t_cons, t_add, t_solve, t_pdf = "📊 Решатель ЛП", "🎯 Цель", "🚧 Ограничения", "+ Добавить", "🚀 Решить", "📥 PDF (с графиком)"
    t_finish, t_hist = "✅ Завершить редактирование", "📜 История решений"

st.markdown(f"<h1 style='text-align: center;'>{t_title}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI (GRAFIK BILAN) ---
def create_pdf(opt_x, opt_y, opt_val, obj_type, fig_image=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Sarlavha
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    
    # Natijalar
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"Optimalnuu tochka: X = {opt_x:.2f}, Y = {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Resultat (Z) = {opt_val:.2f}", ln=True)
    pdf.ln(5)
    
    # Grafikni qo'shish
    if fig_image:
        img_buf = io.BytesIO()
        fig_image.save(img_buf, format='PNG')
        img_buf.seek(0)
        pdf.image(img_buf, x=10, y=None, w=190) # Grafikni varoq kengligi bo'yicha joylashtirish
        
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR (O'zgarishsiz) ---
with st.sidebar:
    st.header(t_target)
    c_main1 = st.number_input("C1", value=5.3, key="main_c1", disabled=st.session_state.locked)
    c_main2 = st.number_input("C2", value=-7.1, key="main_c2", disabled=st.session_state.locked)
    obj_type = st.selectbox("Тип", ("max", "min"), key="main_type", disabled=st.session_state.locked)
    
    st.markdown("---")
    st.header(t_cons)
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}, {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0}]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        cl1, cl2, cl3, cl4, cl5 = st.columns([2, 2, 1.5, 2, 1])
        a_v = cl1.number_input(f"a{i}", value=float(cons['a']), key=f"inp_a{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        b_v = cl2.number_input(f"b{i}", value=float(cons['b']), key=f"inp_b{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        op_v = cl3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"inp_op{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        c_v = cl4.number_input(f"c{i}", value=float(cons['c']), key=f"inp_c{i}", disabled=st.session_state.locked, label_visibility="collapsed")
        if cl5.button("🗑️", key=f"btn_del{i}", disabled=st.session_state.locked):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    
    st.session_state.constraints = new_cons
    if st.button(t_add, disabled=st.session_state.locked):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    if st.button(t_finish, use_container_width=True):
        st.session_state.locked = not st.session_state.locked
        st.rerun()
    
    solve_btn = st.button(t_solve, type="primary", use_container_width=True)
    st.session_state.lang = st.radio("🌐 Til", ("Русский", "O'zbekcha"), horizontal=True)

# --- MATEMATIK YECHIM ---
if solve_btn or st.session_state.locked:
    # ... (linprog hisob-kitoblari o'zgarishsiz) ...
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    col_left, col_right = st.columns([7, 3])

    with col_left:
        fig = go.Figure()
        # ... (Grafik chizish mantiqi: ODR, nuqtalar, liniyalar - o'zgarishsiz) ...
        # (Bu yerda oldingi koddagi barcha grafik chizish amallari bajariladi)
        fig.update_layout(height=600, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # Grafikni rasmga aylantirish (PDF uchun)
        try:
            img_bytes = fig.to_image(format="png", width=800, height=500)
            fig_image = Image.open(io.BytesIO(img_bytes))
        except:
            fig_image = None # Agar kaleido o'rnatilmagan bo'lsa

    with col_right:
        st.subheader("📝 Natijalar")
        if res.success:
            opt_x, opt_y = res.x
            opt_res = c_main1 * opt_x + c_main2 * opt_y
            st.metric("X", f"{opt_x:.2f}")
            st.metric("Y", f"{opt_y:.2f}")
            st.success(f"**Z = {opt_res:.2f}**")
            
            # PDF Yuklash tugmasi (Grafik bilan)
            pdf_data = create_pdf(opt_x, opt_y, opt_res, obj_type, fig_image)
            st.download_button(t_pdf, data=pdf_data, file_name=f"report_{datetime.datetime.now().strftime('%H%M')}.pdf", use_container_width=True)
            
            if solve_btn:
                st.session_state.history.insert(0, {'time': datetime.datetime.now().strftime("%H:%M:%S"), 'x': opt_x, 'y': opt_y, 'z': opt_res, 'type': obj_type})
        else:
            st.error("Yechim topilmadi")

# --- TARIX (O'zgarishsiz) ---
st.markdown("---")
st.header(t_hist)
for h in st.session_state.history:
    st.write(f"🕒 `{h['time']}` | **Z: {h['z']:.2f}** | X: {h['x']:.2f}, Y: {h['y']:.2f} ({h['type']})")

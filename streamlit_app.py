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

st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)

# --- PDF GENERATSIYASI (GRAFIK BILAN) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Otchet resheniya zadachi LP', 0, 1, 'C')
        self.ln(5)

def create_complex_pdf(opt_x, opt_y, opt_val, obj_type, constraints, fig_image):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 1. Umumiy ma'lumotlar
    pdf.cell(0, 10, f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Tip optimizatsii: {obj_type}", ln=True)
    pdf.ln(5)
    
    # 2. Tenglamalar (Constraints) [cite: 2, 3, 4]
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Ogranicheniya:", ln=True)
    pdf.set_font("Arial", size=11)
    for i, c in enumerate(constraints):
        pdf.cell(0, 8, f" {i+1}) {c['a']}*x + {c['b']}*y {c['op']} {c['c']}", ln=True)
    pdf.ln(5)
    
    # 3. Grafikni joylashtirish [cite: 14]
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Grafik resheniya:", ln=True)
    # Rasmni vaqtinchalik xotiradan PDF-ga yuklash
    img_buf = io.BytesIO()
    fig_image.save(img_buf, format='PNG')
    img_buf.seek(0)
    pdf.image(img_buf, x=10, y=None, w=180)
    pdf.ln(5)
    
    # 4. Natijalar 
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Finalniy rezultat:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Optimalnaya tochka: X* = {opt_x:.4f}, Y* = {opt_y:.4f}", ln=True)
    pdf.cell(0, 8, f"Znachenie tselevoy funksii: Z* = {opt_val:.4f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: MA'LUMOT KIRITISH ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    c_col1, c_col2, c_col3 = st.columns([2, 2, 2])
    with c_col1: c1 = st.number_input("C1", value=5.3, format="%.1f")
    with c_col2: c2 = st.number_input("C2", value=-7.1, format="%.1f")
    with c_col3: obj_type = st.selectbox("max/min", ("max", "min"))
    
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
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 2, 1])
        with col1: a = st.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with col2: b = st.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with col3: op = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        with col4: c = st.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with col5: 
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    if st.button("+ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    solve = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- ASOSIY QISM ---
if solve:
    obj = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    if res.success:
        opt_x, opt_y = res.x
        opt_val = c1 * opt_x + c2 * opt_y
        
        # Grafik yaratish
        fig = go.Figure()
        x_vals = np.linspace(-20, 20, 1000)
        for i, c in enumerate(st.session_state.constraints):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_vals) / c['b']
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=f"L{i+1}"))

        # Maqsad chizig'i va optimum [cite: 16, 21]
        y_obj = (opt_val - c1 * x_vals) / c2
        fig.add_trace(go.Scatter(x=x_vals, y=y_obj, mode='lines', name="Z line", line=dict(color='black', dash='dash')))
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name="Optimum"))

        fig.update_layout(
            xaxis=dict(showgrid=True, gridcolor='LightGrey', range=[-15, 15]),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', range=[-20, 20]),
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Grafikni rasmga aylantirish (PDF uchun)
        img_bytes = fig.to_image(format="png", width=800, height=500)
        fig_image = Image.open(io.BytesIO(img_bytes))
        
        # PDF generatsiya va yuklash 
        pdf_data = create_complex_pdf(opt_x, opt_y, opt_val, obj_type, st.session_state.constraints, fig_image)
        st.download_button("📥 Скачать полный отчёт (PDF)", data=pdf_data, file_name="lp_full_report.pdf", mime="application/pdf")
        
        st.success(f"Yechim: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_val:.2f} ")
    else:
        st.error("Yechim topilmadi.")

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

st.set_page_config(page_title="Решатель ЛП", layout="wide")

st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI (Soddalashtirilgan versiya) ---
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="LP Solver Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Optimization type: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"Optimal X = {opt_x:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Optimal Y = {opt_y:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Result Z = {opt_val:.4f}", ln=True)
    # latin-1 xatoligini oldini olish uchun faqat ASCII matn
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- SIDEBAR: KIRITISH ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    col_main1, col_main2, col_t = st.columns([2, 2, 2])
    with col_main1: c_main1 = st.number_input("C1", value=5.3, format="%.2f", key="main_c1")
    with col_main2: c_main2 = st.number_input("C2", value=-7.1, format="%.2f", key="main_c2")
    with col_t: obj_type = st.selectbox("Тип", ("max", "min"), key="main_type")
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    
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
        cl1, cl2, cl3, cl4, cl5 = st.columns([2, 2, 1.5, 2, 1])
        with cl1: a_val = st.number_input(f"a{i}", value=float(cons['a']), key=f"inp_a{i}", label_visibility="collapsed")
        with cl2: b_val = st.number_input(f"b{i}", value=float(cons['b']), key=f"inp_b{i}", label_visibility="collapsed")
        with cl3: op_val = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"inp_op{i}", label_visibility="collapsed")
        with cl4: c_val = st.number_input(f"c{i}", value=float(cons['c']), key=f"inp_c{i}", label_visibility="collapsed")
        with cl5: 
            if st.button("🗑️", key=f"btn_del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_cons.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})
    
    st.session_state.constraints = new_cons
    if st.button("+ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- GRAFIK VA YECHIM ---
if solve_btn:
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    fig = go.Figure()
    # Masshtabni kengaytirdik
    x_range = np.linspace(-50, 50, 2000)

    # Cheklovlar chiziqlari (Belgilar bilan formatlash)
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-7:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            # Bu yerda matematik belgilar qo'shildi
            leg_name = f"{c['a']:.2f} * x + {c['b']:.2f} * y {c['op']} {c['c']:.2f}"
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=leg_name))

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_main1 * opt_x + c_main2 * opt_y
        
        # Maqsad funksiyasi (Z chizig'i)
        if abs(c_main2) > 1e-7:
            y_target = (opt_res - c_main1 * x_range) / c_main2
            fig.add_trace(go.Scatter(x=x_range, y=y_target, mode='lines', 
                                     name=f"Z line: {c_main1:.2f} * x + {c_main2:.2f} * y = {opt_res:.2f}", 
                                     line=dict(color='black', dash='dash', width=2)))

        # Vektor VZ (Gradiyent)
        fig.add_annotation(x=opt_x + (c_main1 * 2), y=opt_y + (c_main2 * 2),
                           ax=opt_x, ay=opt_y, xref="x", yref="y", axref="x", ayref="y",
                           text="VZ", showarrow=True, arrowhead=3, arrowcolor="red", font=dict(color="red", size=14))

        # Optimum nuqta
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=[f"({opt_x:.2f}; {opt_y:.2f})"], 
                                 textposition="top right",
                                 marker=dict(color='gold', size=15, symbol='star', line=dict(color='black', width=1)),
                                 name="Оптимум"))

        # Grafik ko'rinishini sozlash
        fig.update_layout(
            xaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=5, zerolinecolor='black'),
            yaxis=dict(showgrid=True, gridcolor='LightGrey', dtick=5, zerolinecolor='black'),
            plot_bgcolor='white',
            legend=dict(x=1.02, y=1, orientation="v", bordercolor="Black", borderwidth=1),
            height=750,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Natijalar
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.success(f"### Результат:\nX* = {opt_x:.4f}\nY* = {opt_y:.4f}\nZ* = {opt_res:.4f}")
        with col_res2:
            pdf_file = create_pdf(opt_x, opt_y, opt_res, obj_type)
            st.download_button("📥 Скачать отчёт (PDF)", data=pdf_file, file_name="lp_report.pdf", mime="application/pdf")
    else:
        st.error("Решение не найдено. Попробуйте изменить ограничения.")
        st.plotly_chart(fig, use_container_width=True)

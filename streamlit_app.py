import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime
import pandas as pd

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- XOTIRA ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- TIL MANTIQI ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Русский"

if st.session_state.lang == "O'zbekcha":
    t_title = "📊 Chiziqli dasturlash — Yechuvchi"
    t_target = "🎯 Maqsad funksiyasi"
    t_cons = "🚧 Cheklovlar"
    t_add = "+ Cheklov qo'shish"
    t_solve = "🚀 Hisoblash"
    t_pdf = "📥 PDF hisobotni yuklash (Barcha tarix)"
    t_hist = "📜 Yechimlar tarixi"
    t_analysis = "🔍 Masala tahlili va Sezgirlik"
    t_edit_done = "✅ Tahrirlashni yakunlash"
else:
    t_title = "📊 Линейное программирование — Решатель"
    t_target = "🎯 Целевая функция"
    t_cons = "🚧 Ограничения"
    t_add = "+ Добавить ограничение"
    t_solve = "🚀 Решить"
    t_pdf = "📥 Скачать отчёт PDF (Вся история)"
    t_hist = "📜 История решений"
    t_analysis = "🔍 Анализ задачи и Чувствительность"
    t_edit_done = "✅ Завершить редактирование"

st.markdown(f"<h1 style='text-align: center;'>{t_title}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(history):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for i, item in enumerate(history):
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(200, 10, txt=f"Reshenie zadachi No{len(history)-i}", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Vremya: {item['time']}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt="1. Selevaya funksiya:", ln=True)
        pdf.set_font("Arial", size=12)
        target_txt = f"F(X) = {item.get('c1', 0)}*x + ({item.get('c2', 0)})*y -> {item['type']}"
        pdf.cell(200, 10, txt=target_txt, ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt="2. Ogranicheniya:", ln=True)
        pdf.set_font("Arial", size=12)
        if 'constraints_text' in item:
            for cons in item['constraints_text']:
                safe_text = cons.replace('≤', '<=').replace('≥', '>=')
                pdf.cell(200, 8, txt=f"   {safe_text}", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt="3. Resultat:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 8, txt=f"Optimalnaya tochka: X = {item['x']:.2f}, Y = {item['y']:.2f}", ln=True)
        pdf.cell(200, 8, txt=f"Z* = {item['z']:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH QISMI ---
with st.sidebar:
    st.header(t_target)
    col_v1, col_x, col_v2, col_y, col_t = st.columns([2, 1, 2, 1, 3])
    with col_v1: c_main1 = st.number_input("C1", value=5.3, key="main_c1", label_visibility="collapsed")
    with col_x: st.markdown("<div style='padding-top: 10px; font-weight: bold;'>*x +</div>", unsafe_allow_html=True)
    with col_v2: c_main2 = st.number_input("C2", value=-7.1, key="main_c2", label_visibility="collapsed")
    with col_y: st.markdown("<div style='padding-top: 10px; font-weight: bold;'>*y</div>", unsafe_allow_html=True)
    with col_t: obj_type = st.selectbox("Тип", ("max", "min"), key="main_type", label_visibility="collapsed")
    
    st.markdown("---")
    st.header(t_cons)
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '≤', 'c': 3.0}]
    
    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        cl1, cl_x, cl2, cl_y, cl3, cl4, cl5 = st.columns([2, 1.2, 2, 1, 1.5, 2, 1])
        with cl1: a_val = st.number_input(f"a{i}", value=float(cons['a']), key=f"inp_a{i}", label_visibility="collapsed")
        with cl_x: st.markdown("<div style='padding-top: 10px; font-weight: bold;'>*x +</div>", unsafe_allow_html=True)
        with cl2: b_val = st.number_input(f"b{i}", value=float(cons['b']), key=f"inp_b{i}", label_visibility="collapsed")
        with cl_y: st.markdown("<div style='padding-top: 10px; font-weight: bold;'>*y</div>", unsafe_allow_html=True)
        with cl3: op_val = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"inp_op{i}", label_visibility="collapsed")
        with cl4: c_val = st.number_input(f"c{i}", value=float(cons['c']), key=f"inp_c{i}", label_visibility="collapsed")
        with cl5: 
            if st.button("🗑️", key=f"btn_del{i}"):
                st.session_state.constraints.pop(i); st.rerun()
        new_cons.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})
    
    st.session_state.constraints = new_cons
    if st.button(t_add): 
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0}); st.rerun()
    
    st.markdown("---")
    edit_done = st.checkbox(t_edit_done, value=False)
    solve_btn = False
    if edit_done:
        solve_btn = st.button(t_solve, type="primary", use_container_width=True)
    
    st.session_state.lang = st.radio("🌐 Til / Язык", ("Русский", "O'zbekcha"), horizontal=True)

# --- ASOSIY GRAFIK VA YECHIM ---
if solve_btn:
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    constraints_text = []
    for i, c in enumerate(st.session_state.constraints):
        constraints_text.append(f"L{i+1}: {c['a']}*x + {c['b']}*y {c['op']} {c['c']}")
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None), method='highs')
    
    fig = go.Figure()
    limit = 16
    x_range = np.linspace(-limit*2, limit*2, 1000)

    # ODR va Burchak nuqtalar
    corner_points = []
    for i in range(len(st.session_state.constraints)):
        for j in range(i + 1, len(st.session_state.constraints)):
            try:
                A_mat = np.array([[st.session_state.constraints[i]['a'], st.session_state.constraints[i]['b']], [st.session_state.constraints[j]['a'], st.session_state.constraints[j]['b']]])
                B_mat = np.array([st.session_state.constraints[i]['c'], st.session_state.constraints[j]['c']])
                p = np.linalg.solve(A_mat, B_mat)
                valid = True
                for check in st.session_state.constraints:
                    val = check['a']*p[0] + check['b']*p[1]
                    if check['op'] == '≤' and val > check['c'] + 1e-5: valid = False
                    elif check['op'] == '≥' and val < check['c'] - 1e-5: valid = False
                    elif check['op'] == '=' and abs(val - check['c']) > 1e-5: valid = False
                if valid: corner_points.append(p)
            except: continue

    if corner_points:
        pts = np.array(corner_points)
        center = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
        pts = pts[np.argsort(angles)]
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0, 102, 204, 0.15)', line=dict(color='rgba(255,255,255,0)'), name="ОДР"))
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name="Угловые точки"))
        fig.add_trace(go.Scatter(x=[center[0]], y=[center[1]], mode='markers', marker=dict(color='blue', size=8), name="Внутр. точка"))

    # Cheklov chiziqlari
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-7:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            full_name = f"L{i+1}: {c['a']}*x+ {c['b']}*y {c['op']} {c['c']}"
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', line=dict(color=colors[i % len(colors)], width=2), name=full_name))
            
    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_main1 * opt_x + c_main2 * opt_y
        st.session_state.history.insert(0, {'time': datetime.datetime.now().strftime("%H:%M:%S"), 'c1': c_main1, 'c2': c_main2, 'type': obj_type, 'constraints_text': constraints_text, 'x': opt_x, 'y': opt_y, 'z': opt_res, 'success': True, 'res_obj': res})

        # Grafikdagi vizual elementlar
        if abs(c_main2) > 1e-7:
            y_target = (opt_res - c_main1 * x_range) / c_main2
            fig.add_trace(go.Scatter(x=x_range, y=y_target, mode='lines', line=dict(color='black', dash='dash', width=2), name=f"Целевая прямая (Z={opt_res:.2f})"))
        
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', text=["Оптимум"], textposition="top right", marker=dict(color='gold', size=14, symbol='star'), name="Оптимум"))

    # Grafik layout
    fig.update_layout(xaxis=dict(range=[-limit, limit], showgrid=False, visible=False), yaxis=dict(range=[-limit, limit], showgrid=False, visible=False), plot_bgcolor='white', legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    # --- YANGI QO'SHILGAN BO'LIMLAR ---
    tab1, tab2 = st.tabs([t_analysis, t_hist])

    with tab1:
        st.subheader(t_analysis)
        if res.success:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.write("**Оптимальные значения:**")
                st.info(f"X* = {opt_x:.4f}\nY* = {opt_y:.4f}\nZ* = {opt_res:.4f}")
            with col_a2:
                st.write("**Теневые цены (Shadow Prices):**")
                shadow_prices = res.get('marginals', {}).get('upper', [])
                if len(shadow_prices) > 0:
                    st.success(f"Влияние ограничений: {shadow_prices}")
                else:
                    st.write("Информация недоступна для данного метода.")

    with tab2:
        st.subheader(t_hist)
        if st.session_state.history:
            for h in st.session_state.history:
                with st.expander(f"Z={h['z']:.2f} ({h['time']})"):
                    st.write(f"**Точка:** ({h['x']:.2f}, {h['y']:.2f})")
                    st.write(f"**Тип:** {h['type']}")
                    for ct in h['constraints_text']: st.write(ct)
            
            pdf_data = create_pdf(st.session_state.history)
            st.download_button(t_pdf, data=pdf_data, file_name="history.pdf", mime="application/pdf")
```

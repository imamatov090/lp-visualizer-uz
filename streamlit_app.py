import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime
import pandas as pd

# Sahifa sozlamalari (O'zgarishsiz)
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- XOTIRA (O'zgarishsiz) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- TIL MANTIQI (O'zgarishsiz) ---
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

# --- PDF FUNKSIYASI (O'zgarishsiz) ---
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
        target_txt = f"F(X) = {item.get('c1', 0)}x1 + ({item.get('c2', 0)})x2 -> {item['type']}"
        pdf.cell(200, 10, txt=target_txt, ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt="2. Ogranicheniya:", ln=True)
        pdf.set_font("Arial", size=12)
        if 'constraints_text' in item:
            for cons in item['constraints_text']:
                safe_text = cons.replace('≤', '<=').replace('≥', '>=')
                pdf.cell(200, 8, txt=f"   {safe_text}", ln=True)
        pdf.cell(200, 8, txt="   x1 >= 0, x2 >= 0", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt="3. Resultat:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 8, txt=f"Optimalnaya tochka: X1 = {item['x']:.2f}, X2 = {item['y']:.2f}", ln=True)
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 8, txt=f"Z* = {item['z']:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR (O'zgarishsiz) ---
with st.sidebar:
    st.header(t_target)
    col_v1, col_x, col_v2, col_y, col_t = st.columns([2, 1, 2, 1, 3])
    with col_v1: c_main1 = st.number_input("C1", value=5.3, format="%.1f", key="main_c1", label_visibility="collapsed")
    with col_x: st.markdown("<div style='margin-top: 5px;'><sup>*x</sup> +</div>", unsafe_allow_html=True)
    with col_v2: c_main2 = st.number_input("C2", value=-7.1, format="%.1f", key="main_c2", label_visibility="collapsed")
    with col_y: st.markdown("<div style='margin-top: 5px;'><sup>*y</sup></div>", unsafe_allow_html=True)
    with col_t: obj_type = st.selectbox("Тип", ("max", "min"), key="main_type", label_visibility="collapsed")
    st.markdown("---")
    st.header(t_cons)
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0}, {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0}, {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}, {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0}, {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}]
    
    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        cl1, cl_x, cl2, cl_y, cl3, cl4, cl5 = st.columns([2, 1.2, 2, 1, 1.5, 2, 1])
        with cl1: a_val = st.number_input(f"a{i}", value=float(cons['a']), key=f"inp_a{i}", label_visibility="collapsed")
        with cl_x: st.markdown("<div style='margin-top: 5px;'><sup>*x</sup> +</div>", unsafe_allow_html=True)
        with cl2: b_val = st.number_input(f"b{i}", value=float(cons['b']), key=f"inp_b{i}", label_visibility="collapsed")
        with cl_y: st.markdown("<div style='margin-top: 5px;'><sup>*y</sup></div>", unsafe_allow_html=True)
        with cl3: op_val = st.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"inp_op{i}", label_visibility="collapsed")
        with cl4: c_val = st.number_input(f"c{i}", value=float(cons['c']), key=f"inp_c{i}", label_visibility="collapsed")
        with cl5: 
            if st.button("🗑️", key=f"btn_del{i}"):
                st.session_state.constraints.pop(i); st.rerun()
        new_cons.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})
    
    st.session_state.constraints = new_cons
    if st.button(t_add): st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0}); st.rerun()
    st.markdown("---")
    
    edit_done = st.checkbox(t_edit_done, value=False)
    solve_btn = False
    if edit_done:
        solve_btn = st.button(t_solve, type="primary", use_container_width=True)
    
    st.session_state.lang = st.radio("🌐 Til / Язык", ("Русский", "O'zbekcha"), horizontal=True)
# --- ГРАФИК И РЕШЕНИЕ (ОДР, Угловые точки, L1, L2... и другие обозначения) ---
if solve_btn:
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None), method='highs')
    
    fig = go.Figure()
    limit = 16
    x_range = np.linspace(-limit*2, limit*2, 1000)

    # 1. ОДР
    corner_points = []
    lines = st.session_state.constraints
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            try:
                A = np.array([[lines[i]['a'], lines[i]['b']], [lines[j]['a'], lines[j]['b']]])
                B = np.array([lines[i]['c'], lines[j]['c']])
                p = np.linalg.solve(A, B)
                valid = True
                for check in lines:
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
        # 2. Угловые точки
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=7), name="Угловые точки"))
        # 3. Внутр. точка
        fig.add_trace(go.Scatter(x=[center[0]], y=[center[1]], mode='markers', marker=dict(color='blue', size=8), name="Внутр. точка"))

    # 4. Ограничения L1, L2...
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-7:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', line=dict(color=colors[i % len(colors)], width=2), name=f"L{i+1}"))
            
            # Подпись L1, L2 прямо на линии
            lx = -limit + 3 + i*2
            ly = (c['c'] - c['a'] * lx) / c['b']
            if -limit < ly < limit:
                fig.add_annotation(x=lx, y=ly, text=f"L{i+1}", showarrow=False, font=dict(color=colors[i % len(colors)], size=12, family="Arial Bold"), bgcolor="white")

    if res.success:
        opt_x, opt_y = res.x
        opt_res = c_main1 * opt_x + c_main2 * opt_y
        
        # 5. Линия уровня (проходящая через центр для наглядности)
        if corner_points and abs(c_main2) > 1e-7:
            z_mid = c_main1 * center[0] + c_main2 * center[1]
            y_mid = (z_mid - c_main1 * x_range) / c_main2
            fig.add_trace(go.Scatter(x=x_range, y=y_mid, mode='lines', line=dict(color='green', dash='dot', width=1.5), name="Линия уровня"))

        # 6. Целевая прямая (Оптимальная)
        if abs(c_main2) > 1e-7:
            y_target = (opt_res - c_main1 * x_range) / c_main2
            fig.add_trace(go.Scatter(x=x_range, y=y_target, mode='lines', line=dict(color='black', dash='dash', width=2), name="Целевая прямая"))

        # 7. Оптимум
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', text=["Оптимум"], textposition="top right", 
                                 marker=dict(color='gold', size=14, symbol='star', line=dict(color='black', width=1)), name="Оптимум"))

        # Вектор VZ
        norm = np.sqrt(c_main1**2 + c_main2**2)
        if norm > 0:
            scale = 4
            vx, vy = (c_main1/norm)*scale, (c_main2/norm)*scale
            if obj_type == "min": vx, vy = -vx, -vy
            fig.add_annotation(x=opt_x + vx, y=opt_y + vy, ax=opt_x, ay=opt_y, xref="x", yref="y", axref="x", ayref="y",
                               text="VZ", showarrow=True, arrowhead=3, arrowcolor="red", font=dict(color="red", size=14))

    # Оси со стрелками, тиками и нулем
    fig.add_annotation(x=limit, y=0, ax=-limit, ay=0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=2)
    fig.add_annotation(x=0, y=limit, ax=0, ay=-limit, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=2)

    for i in range(-limit+1, limit):
        fig.add_shape(type="line", x0=i, y0=-0.2, x1=i, y1=0.2, line=dict(color="black", width=1)) # Тики X
        fig.add_shape(type="line", x0=-0.2, y0=i, x1=0.2, y1=i, line=dict(color="black", width=1)) # Тики Y
        if i != 0 and i % 2 == 0:
            fig.add_annotation(x=i, y=-0.8, text=str(i), showarrow=False, font=dict(size=10))
            fig.add_annotation(x=-0.8, y=i, text=str(i), showarrow=False, font=dict(size=10))

    fig.add_annotation(x=-0.6, y=-0.6, text="0", showarrow=False, font=dict(size=12, family="Arial Black"))
    fig.add_annotation(x=limit, y=0.8, text="X", showarrow=False, font=dict(size=16))
    fig.add_annotation(x=0.8, y=limit, text="Y", showarrow=False, font=dict(size=16))

    fig.update_layout(
        xaxis=dict(showgrid=False, visible=False, range=[-limit, limit+1]),
        yaxis=dict(showgrid=False, visible=False, range=[-limit, limit+1]),
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center", bordercolor="Black", borderwidth=1),
        height=800, margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

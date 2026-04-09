import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import datetime

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
    t_title, t_target, t_cons, t_add, t_solve, t_pdf = "📊 LP Yechuvchi", "🎯 Maqsad", "🚧 Cheklovlar", "+ Qo'shish", "🚀 Hisoblash", "📥 PDF"
    t_finish, t_hist = "✅ Tahrirlashni yakunlash", "📜 Yechimlar tarixi"
else:
    t_title, t_target, t_cons, t_add, t_solve, t_pdf = "📊 Решатель ЛП", "🎯 Цель", "🚧 Ограничения", "+ Добавить", "🚀 Решить", "📥 PDF"
    t_finish, t_hist = "✅ Завершить редактирование", "📜 История решений"

st.markdown(f"<h1 style='text-align: center;'>{t_title}</h1>", unsafe_allow_html=True)

# --- PDF FUNKSIYASI ---
def create_pdf(opt_x, opt_y, opt_val, obj_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip: {obj_type} | X = {opt_x:.2f}, Y = {opt_y:.2f} | Z = {opt_val:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR ---
with st.sidebar:
    st.header(t_target)
    c_main1 = st.number_input("C1", value=5.3, key="main_c1", disabled=st.session_state.locked)
    c_main2 = st.number_input("C2", value=-7.1, key="main_c2", disabled=st.session_state.locked)
    obj_type = st.selectbox("Тип", ("max", "min"), key="main_type", disabled=st.session_state.locked)
    
    st.markdown("---")
    st.header(t_cons)
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}
        ]

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

# --- MATEMATIK YECHIM VA GRAFIK ---
if solve_btn or st.session_state.locked:
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
        x_range = np.linspace(-20, 20, 1000)
        corner_points = []
        
        # Burchak nuqtalarini topish
        lines = st.session_state.constraints
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                try:
                    A_mat = np.array([[lines[i]['a'], lines[i]['b']], [lines[j]['a'], lines[j]['b']]])
                    B_mat = np.array([lines[i]['c'], lines[j]['c']])
                    p = np.linalg.solve(A_mat, B_mat)
                    valid = True
                    for check in lines:
                        v = check['a']*p[0] + check['b']*p[1]
                        if check['op'] == '≤' and v > check['c'] + 1e-5: valid = False
                        elif check['op'] == '≥' and v < check['c'] - 1e-5: valid = False
                        elif check['op'] == '=' and abs(v - check['c']) > 1e-5: valid = False
                    if valid: corner_points.append(p)
                except: continue

        if corner_points:
            pts = np.array(corner_points)
            center = np.mean(pts, axis=0)
            angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
            pts = pts[np.argsort(angles)]
            fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0, 100, 255, 0.2)', line=dict(color='rgba(255,255,255,0)'), name="ОДР"))
            fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name="Угловые точки"))
            
            # ШАГ 2 & 3: Ichki nuqta va daraja chizig'i
            inner_z = c_main1 * center[0] + c_main2 * center[1]
            fig.add_trace(go.Scatter(x=[center[0]], y=[center[1]], mode='markers', marker=dict(color='blue', size=10), name="Внутр. точка"))
            if abs(c_main2) > 1e-7:
                y_inner = (inner_z - c_main1 * x_range) / c_main2
                fig.add_trace(go.Scatter(x=x_range, y=y_inner, mode='lines', line=dict(color='blue', dash='dot'), name="Линия уровня"))

        for i, c in enumerate(lines):
            if abs(c['b']) > 1e-7:
                y_vals = (c['c'] - c['a'] * x_range) / c['b']
                fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}"))

        if res.success:
            opt_x, opt_y = res.x
            opt_res = c_main1 * opt_x + c_main2 * opt_y
            if abs(c_main2) > 1e-7:
                y_target = (opt_res - c_main1 * x_range) / c_main2
                fig.add_trace(go.Scatter(x=x_range, y=y_target, mode='lines', line=dict(color='black', dash='dash', width=2), name="Z optimum"))
            
            fig.add_annotation(x=opt_x+1, y=opt_y+1, ax=opt_x, ay=opt_y, text="VZ", showarrow=True, arrowhead=3, arrowcolor="red")
            
            # Tarixga qo'shish
            if solve_btn:
                st.session_state.history.insert(0, {'time': datetime.datetime.now().strftime("%H:%M:%S"), 'x': opt_x, 'y': opt_y, 'z': opt_res, 'type': obj_type})

        fig.update_layout(height=700, xaxis=dict(range=[-15, 15]), yaxis=dict(range=[-15, 15]), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("📝 Natijalar" if st.session_state.lang == "O'zbekcha" else "📝 Результаты")
        if res.success:
            st.metric("X", f"{opt_x:.2f}")
            st.metric("Y", f"{opt_y:.2f}")
            st.success(f"**Z = {opt_res:.2f}**")
            
            pdf_data = create_pdf(opt_x, opt_y, opt_res, obj_type)
            st.download_button(t_pdf, data=pdf_data, file_name="otchet.pdf", use_container_width=True)
        else:
            st.error("Yechim topilmadi")

# --- TARIX ---
st.markdown("---")
st.header(t_hist)
for h in st.session_state.history:
    st.write(f"🕒 `{h['time']}` | **Z: {h['z']:.2f}** | X: {h['x']:.2f}, Y: {h['y']:.2f} ({h['type']})")

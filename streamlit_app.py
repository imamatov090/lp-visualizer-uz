import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# --- TIL LUG'ATI ---
if "lang" not in st.session_state:
    st.session_state.lang = "Русский"

texts = {
    "Русский": {
        "title": "📊 Линейное программирование — Решатель",
        "target": "🎯 Целевая функция",
        "cons": "🚧 Ограничения",
        "solve": "🚀 Решить",
        "points": "Угловые точки",
        "opt": "Оптимум",
        "vz": "VZ (Градиент)",
        "odr": "ОДР",
        "res": "Результат",
        "pdf": "📥 Скачать отчёт (PDF)"
    },
    "O'zbekcha": {
        "title": "📊 Chiziqli dasturlash — Yechuvchi",
        "target": "🎯 Maqsad funksiyasi",
        "cons": "🚧 Cheklovlar",
        "solve": "🚀 Hisoblash",
        "points": "Burchak nuqtalari",
        "opt": "Optimum",
        "vz": "VZ (Gradient)",
        "odr": "ODR",
        "res": "Natija",
        "pdf": "📥 PDF hisobotni yuklash"
    }
}

t = texts[st.session_state.lang]
st.markdown(f"<h1 style='text-align: center;'>{t['title']}</h1>", unsafe_allow_html=True)

# --- SIDEBAR: MA'LUMOTLARNI KIRITISH ---
with st.sidebar:
    st.header(t["target"])
    c1_col, x_col, c2_col, y_col, type_col = st.columns([2, 1, 2, 1, 3])
    c_main1 = c1_col.number_input("C1", value=5.3, format="%.2f", key="c1", label_visibility="collapsed")
    x_col.markdown("<div style='margin-top:5px'>*x +</div>", unsafe_allow_html=True)
    c_main2 = c2_col.number_input("C2", value=-7.1, format="%.2f", key="c2", label_visibility="collapsed")
    y_col.markdown("<div style='margin-top:5px'>*y</div>", unsafe_allow_html=True)
    obj_type = type_col.selectbox("Type", ("max", "min"), label_visibility="collapsed")

    st.markdown("---")
    st.header(t["cons"])
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
        cl1, cl_x, cl2, cl_y, cl3, cl4, cl5 = st.columns([2, 0.8, 2, 0.8, 1.5, 2, 0.8])
        a = cl1.number_input(f"a{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        cl_x.write("*x+")
        b = cl2.number_input(f"b{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        cl_y.write("*y")
        op = cl3.selectbox(f"op{i}", ("≤", "≥", "="), index=("≤", "≥", "=").index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        c = cl4.number_input(f"c{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        if cl5.button("🗑️", key=f"del{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    solve_btn = st.button(t["solve"], type="primary", use_container_width=True)
    
    st.markdown("<br>"*5, unsafe_allow_html=True)
    st.session_state.lang = st.radio("🌐 Til / Язык", ("Русский", "O'zbekcha"), horizontal=True)

# --- ASOSIY MANTIQ ---
if solve_btn:
    # 1. Burchak nuqtalarini topish
    corner_points = []
    for i in range(len(st.session_state.constraints)):
        for j in range(i + 1, len(st.session_state.constraints)):
            c1, c2 = st.session_state.constraints[i], st.session_state.constraints[j]
            try:
                A_mat = np.array([[c1['a'], c1['b']], [c2['a'], c2['b']]])
                B_mat = np.array([c1['c'], c2['c']])
                p = np.linalg.solve(A_mat, B_mat)
                
                # Nuqta barcha cheklovlarga mosligini tekshirish
                is_valid = True
                for check in st.session_state.constraints:
                    val = check['a']*p[0] + check['b']*p[1]
                    if check['op'] == '≤' and val > check['c'] + 1e-5: is_valid = False
                    elif check['op'] == '≥' and val < check['c'] - 1e-5: is_valid = False
                    elif check['op'] == '=' and abs(val - check['c']) > 1e-5: is_valid = False
                if is_valid: corner_points.append(p)
            except: continue

    # 2. Simplex yechim
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
        st.success(f"### {t['res']}: X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_res:.2f}")

        fig = go.Figure()
        
        # ODRni bo'yash
        if corner_points:
            pts = np.array(corner_points)
            center = np.mean(pts, axis=0)
            angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
            pts = pts[np.argsort(angles)]
            fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0,100,255,0.2)', line=dict(color='blue', width=0), name=t["odr"]))
            # Uglovie tochki (Qizil nuqtalar)
            fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name=t["points"]))

        # Maqsad funksiyasi chizig'i va VZ
        fig.add_annotation(x=opt_x + c_main1/3, y=opt_y + c_main2/3, ax=opt_x, ay=opt_y, xref="x", yref="y", text=t["vz"], showarrow=True, arrowhead=3, arrowcolor="red")
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', marker=dict(size=15, color='gold', symbol='star'), name=t["opt"]))

        # Setka va masshtab (Kichikroq setka dtick=1)
        fig.update_layout(
            xaxis=dict(gridcolor='lightgrey', dtick=1, zerolinecolor='black', range=[-15, 15]),
            yaxis=dict(gridcolor='lightgrey', dtick=1, zerolinecolor='black', range=[-15, 15]),
            plot_bgcolor='white', height=750, showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Yechim topilmadi.")

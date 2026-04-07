import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- TILNI ANIQLASH (Xatosiz variant) ---
if "lang" not in st.session_state:
    st.session_state.lang = "Русский"

texts = {
    "Русский": {
        "title": "Линейное программирование — Решатель",
        "target": "Целевая функция",
        "cons": "Ограничения",
        "solve": "🚀 Решить",
        "odr": "ОДР (Область)",
        "points": "Угловые точки",
        "opt": "Оптимум",
        "vz": "Градиент (VZ)"
    },
    "O'zbekcha": {
        "title": "Chiziqli dasturlash — Yechuvchi",
        "target": "Maqsad funksiyasi",
        "cons": "Cheklovlar",
        "solve": "🚀 Hisoblash",
        "odr": "ODR sohasi",
        "points": "Burchak nuqtalari",
        "opt": "Optimum",
        "vz": "Gradient (VZ)"
    }
}

t = texts[st.session_state.lang]

# --- SIDEBAR ---
with st.sidebar:
    st.header(t["target"])
    # Maqsad funksiyasi koeffitsientlari
    c1 = st.number_input("C1 (x)", value=5.3, step=0.1, key="main_c1")
    c2 = st.number_input("C2 (y)", value=-7.1, step=0.1, key="main_c2")
    obj = st.selectbox("Тип", ["max", "min"], key="obj_type")

    st.markdown("---")
    st.header(t["cons"])
    if 'constraints' not in st.session_state:
        # Boshlang'ich cheklovlar
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        # Unikal keylar orqali DuplicateElementKey xatosi bartaraf etildi
        cols = st.columns([2, 2, 1.5, 2, 1])
        a = cols[0].number_input(f"a", value=float(cons['a']), key=f"a_{i}", label_visibility="collapsed")
        b = cols[1].number_input(f"b", value=float(cons['b']), key=f"b_{i}", label_visibility="collapsed")
        op = cols[2].selectbox(f"op", ["≤", "≥", "="], index=["≤", "≥", "=").index(cons['op']), key=f"op_{i}", label_visibility="collapsed")
        c = cols[3].number_input(f"c", value=float(cons['c']), key=f"c_{i}", label_visibility="collapsed")
        if cols[4].button("🗑️", key=f"del_{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    if st.button("+"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    st.session_state.lang = st.radio("Language", ["Русский", "O'zbekcha"], horizontal=True)

# --- MATEMATIK HISOB-KITOB VA GRAFIK ---
st.title(t["title"])
solve = st.button(t["solve"], type="primary", use_container_width=True)

if solve:
    # 1. Burchak nuqtalarini saralash algoritmi (Rahbar chizmasi bo'yicha)
    corner_points = []
    lines = st.session_state.constraints
    
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            try:
                A = np.array([[lines[i]['a'], lines[i]['b']], [lines[j]['a'], lines[j]['b']]])
                B = np.array([lines[i]['c'], lines[j]['c']])
                p = np.linalg.solve(A, B)
                
                # "Yaxshi" nuqtalarni (ODR ichidagilarni) tekshirish
                valid = True
                for c in lines:
                    val = c['a']*p[0] + c['b']*p[1]
                    if c['op'] == '≤' and val > c['c'] + 1e-5: valid = False
                    elif c['op'] == '≥' and val < c['c'] - 1e-5: valid = False
                    elif c['op'] == '=' and abs(val - c['c']) > 1e-5: valid = False
                if valid: corner_points.append(p)
            except: continue

    # 2. Simplex usulida yechish
    c_sign = -1 if obj == "max" else 1
    res = linprog([c1*c_sign, c2*c_sign], 
                  A_ub=[[l['a'], l['b']] if l['op']=='≤' else [-l['a'], -l['b']] for l in lines if l['op']!='='] or None,
                  b_ub=[l['c'] if l['op']=='≤' else -l['c'] for l in lines if l['op']!='='] or None,
                  A_eq=[[l['a'], l['b']] for l in lines if l['op']=='=='] or None,
                  b_eq=[l['c'] for l in lines if l['op']=='=='] or None,
                  bounds=(None, None))

    fig = go.Figure()
    
    # 3. ODRni bo'yash (Poligon)
    if corner_points:
        pts = np.array(corner_points)
        # Nuqtalarni soat yo'nalishi bo'yicha tartiblash
        center = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
        pts = pts[np.argsort(angles)]
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0,200,0,0.2)', 
                                 line=dict(color='green'), name=t["odr"]))
        # Burchak nuqtalarini qizil bilan ko'rsatish
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name=t["points"]))

    if res.success:
        opt_x, opt_y = res.x
        z_val = c1*opt_x + c2*opt_y
        st.success(f"**{t['res']}**: X={opt_x:.2f}, Y={opt_y:.2f}, Z={z_val:.2f}")

        # Optimum va VZ (Gradient)
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers', marker=dict(size=15, symbol='star', color='gold'), name=t["opt"]))
        fig.add_annotation(x=opt_x + c1/5, y=opt_y + c2/5, ax=opt_x, ay=opt_y, xref="x", yref="y", axref="x", ayref="y", 
                           showarrow=True, arrowhead=3, arrowcolor="red", text=t["vz"])

    # Grafik sozlamalari (Mayda setka)
    fig.update_layout(xaxis=dict(dtick=1, gridcolor='lightgrey', range=[-15, 15]), 
                      yaxis=dict(dtick=1, gridcolor='lightgrey', range=[-15, 15]), 
                      plot_bgcolor='white', height=800)
    st.plotly_chart(fig, use_container_width=True)

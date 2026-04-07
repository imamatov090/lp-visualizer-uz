import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- TILNI ANIQLASH (Xatosiz lug'at tizimi) ---
if "lang" not in st.session_state:
    st.session_state.lang = "Русский"

# Tutuq belgisi muammosini hal qilish uchun qo'sh qo'shtirnoq ishlatildi
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
        "points": "Burchak nuqalari",
        "opt": "Optimum",
        "vz": "Gradient (VZ)"
    }
}

t = texts[st.session_state.lang]

# --- SIDEBAR ---
with st.sidebar:
    st.header(t["target"])
    c1 = st.number_input("C1 (x)", value=5.3, step=0.1, key="main_c1")
    c2 = st.number_input("C2 (y)", value=-7.1, step=0.1, key="main_c2")
    obj = st.selectbox("Тип", ["max", "min"], key="obj_type")

    st.markdown("---")
    st.header(t["cons"])
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0}
        ]

    new_cons = []
    for i, cons in enumerate(st.session_state.constraints):
        # Unikal keylar DuplicateElementKey xatosini oldini oladi
        cols = st.columns([2, 2, 1.5, 2, 1])
        a = cols[0].number_input(f"a", value=float(cons['a']), key=f"a_inp_{i}", label_visibility="collapsed")
        b = cols[1].number_input(f"b", value=float(cons['b']), key=f"b_inp_{i}", label_visibility="collapsed")
        op = cols[2].selectbox(f"op", ["≤", "≥", "="], index=["≤", "≥", "="].index(cons['op']), key=f"op_inp_{i}", label_visibility="collapsed")
        c = cols[3].number_input(f"c", value=float(cons['c']), key=f"c_inp_{i}", label_visibility="collapsed")
        if cols[4].button("🗑️", key=f"del_btn_{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a, 'b': b, 'op': op, 'c': c})
    
    st.session_state.constraints = new_cons
    if st.button("+"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    st.session_state.lang = st.radio("Language", ["Русский", "O'zbekcha"], horizontal=True)

# --- MATEMATIK YECHIM ---
st.title(t["title"])
if st.button(t["solve"], type="primary", use_container_width=True):
    lines = st.session_state.constraints
    
    # Burchak nuqtalarini saralash (Rahbar chizmasi bo'yicha)
    corner_points = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            try:
                A = np.array([[lines[i]['a'], lines[i]['b']], [lines[j]['a'], lines[j]['b']]])
                B = np.array([lines[i]['c'], lines[j]['c']])
                p = np.linalg.solve(A, B)
                
                # "Yaxshi" nuqtalarni tekshirish
                valid = True
                for c in lines:
                    val = c['a']*p[0] + c['b']*p[1]
                    if c['op'] == '≤' and val > c['c'] + 1e-5: valid = False
                    elif c['op'] == '≥' and val < c['c'] - 1e-5: valid = False
                    elif c['op'] == '=' and abs(val - c['c']) > 1e-5: valid = False
                if valid: corner_points.append(p)
            except: continue

    # Simplex yechim
    c_sign = -1 if obj == "max" else 1
    res = linprog([c1*c_sign, c2*c_sign], 
                  A_ub=[[l['a'], l['b']] if l['op']=='≤' else [-l['a'], -l['b']] for l in lines if l['op']!='='] or None,
                  b_ub=[l['c'] if l['op']=='≤' else -l['c'] for l in lines if l['op']!='='] or None,
                  A_eq=[[l['a'], l['b']] for l in lines if l['op']=='='] or None,
                  b_eq=[l['c'] for l in lines if l['op']=='='] or None,
                  bounds=(None, None))

    fig = go.Figure()
    
    # ODRni bo'yash
    if corner_points:
        pts = np.array(corner_points)
        center = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
        pts = pts[np.argsort(angles)]
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0,200,0,0.2)', name=t["odr"]))
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name=t["points"]))

    if res.success:
        ox, oy = res.x
        st.success(f"**{t['opt']}**: X={ox:.2f}, Y={oy:.2f}, Z={c1*ox + c2*oy:.2f}")
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(size=15, symbol='star', color='gold'), name=t["opt"]))
        fig.add_annotation(x=ox + c1/5, y=oy + c2/5, ax=ox, ay=oy, xref="x", yref="y", showarrow=True, arrowhead=3, arrowcolor="red", text=t["vz"])

    fig.update_layout(xaxis=dict(dtick=1, gridcolor='lightgrey', range=[-15, 15]), 
                      yaxis=dict(dtick=1, gridcolor='lightgrey', range=[-15, 15]), 
                      plot_bgcolor='white', height=800)
    st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog

# Sahifa sozlamalari
st.set_page_config(page_title="LP Solver", layout="wide")

# --- TILNI ANIQLASH (Xatosiz lug'at) ---
if "lang" not in st.session_state:
    st.session_state.lang = "Русский"

# O'zbekcha so'zidagi apostrof muammo bo'lmasligi uchun qo'sh tirnoq ishlatildi
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
    # Har bir input uchun unikal 'key' berildi
    c1 = st.number_input("C1 (x)", value=5.3, step=0.1, key="main_c1_input")
    c2 = st.number_input("C2 (y)", value=-7.1, step=0.1, key="main_c2_input")
    obj = st.selectbox("Тип", ["max", "min"], key="obj_type_select")

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
        # Indeks orqali unikal keylar yaratildi (DuplicateKey xatosini oldini oladi)
        cols = st.columns([2, 2, 1.5, 2, 1])
        a_val = cols[0].number_input(f"a_{i}", value=float(cons['a']), key=f"a_in_{i}", label_visibility="collapsed")
        b_val = cols[1].number_input(f"b_{i}", value=float(cons['b']), key=f"b_in_{i}", label_visibility="collapsed")
        op_val = cols[2].selectbox(f"op_{i}", ["≤", "≥", "="], index=["≤", "≥", "="].index(cons['op']), key=f"op_in_{i}", label_visibility="collapsed")
        c_val = cols[3].number_input(f"c_{i}", value=float(cons['c']), key=f"c_in_{i}", label_visibility="collapsed")
        
        if cols[4].button("🗑️", key=f"del_btn_{i}"):
            st.session_state.constraints.pop(i)
            st.rerun()
        new_cons.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})
    
    st.session_state.constraints = new_cons
    if st.button("+", key="add_new_const_btn"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    st.session_state.lang = st.radio("Language", ["Русский", "O'zbekcha"], horizontal=True, key="lang_toggle")

# --- ASOSIY GRAFIK VA HISOBLASH ---
st.title(t["title"])
if st.button(t["solve"], type="primary", use_container_width=True, key="final_solve_btn"):
    lines = st.session_state.constraints
    
    # 1. Burchak nuqtalarini topish (Intersections)
    corner_points = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            try:
                A_mat = np.array([[lines[i]['a'], lines[i]['b']], [lines[j]['a'], lines[j]['b']]])
                B_mat = np.array([lines[i]['c'], lines[j]['c']])
                p = np.linalg.solve(A_mat, B_mat)
                
                # ODR shartlariga mosligini tekshirish
                valid = True
                for check in lines:
                    val = check['a']*p[0] + check['b']*p[1]
                    if check['op'] == '≤' and val > check['c'] + 1e-5: valid = False
                    elif check['op'] == '≥' and val < check['c'] - 1e-5: valid = False
                    elif check['op'] == '=' and abs(val - check['c']) > 1e-5: valid = False
                if valid: corner_points.append(p)
            except: continue

    # 2. Simplex solver (scipy)
    c_sign = -1 if obj == "max" else 1
    res = linprog([c1*c_sign, c2*c_sign], 
                  A_ub=[[l['a'], l['b']] if l['op']=='≤' else [-l['a'], -l['b']] for l in lines if l['op']!='='] or None,
                  b_ub=[l['c'] if l['op']=='≤' else -l['c'] for l in lines if l['op']!='='] or None,
                  A_eq=[[l['a'], l['b']] for l in lines if l['op']=='='] or None,
                  b_eq=[l['c'] for l in lines if l['op']=='='] or None,
                  bounds=(None, None))

    fig = go.Figure()
    
    # 3. ODRni poligon qilib bo'yash
    if corner_points:
        pts = np.array(corner_points)
        # Nuqtalarni markazga nisbatan burchak bo'yicha tartiblash (Poligon hosil qilish uchun)
        center = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
        pts = pts[np.argsort(angles)]
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0,255,0,0.2)', 
                                 line=dict(color='green'), name=t["odr"]))
        # Burchak nuqtalarini qizil markerlar bilan ko'rsatish
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name=t["points"]))

    if res.success:
        ox, oy = res.x
        st.success(f"**{t['opt']}**: X={ox:.2f}, Y={oy:.2f}, Z={c1*ox + c2*oy:.2f}")
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers', marker=dict(size=15, symbol='star', color='gold'), name=t["opt"]))
        # Gradient vektori (VZ)
        fig.add_annotation(x=ox + c1/5, y=oy + c2/5, ax=ox, ay=oy, xref="x", yref="y", showarrow=True, arrowhead=3, arrowcolor="red", text=t["vz"])

    fig.update_layout(xaxis=dict(dtick=1, gridcolor='lightgrey', range=[-15, 15]), 
                      yaxis=dict(dtick=1, gridcolor='lightgrey', range=[-15, 15]), 
                      plot_bgcolor='white', height=800)
    st.plotly_chart(fig, use_container_width=True)

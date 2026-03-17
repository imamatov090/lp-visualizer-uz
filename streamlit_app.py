import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog

# Sahifa sarlavhasi va sozlamalari
st.set_page_config(page_title="LP-Visualizer UZ", layout="wide")

# Sarlavha (Rasmdagi kabi)
st.markdown("<h1 style='text-align: center; color: #333;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- CHAP TOMON: INPUTLAR ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    col_obj1, col_obj2 = st.columns(2)
    with col_obj1:
        c1 = st.number_input("C1 (x)", value=5.3, step=0.1, format="%.1f")
    with col_obj2:
        c2 = st.number_input("C2 (y)", value=-7.1, step=0.1, format="%.1f")
    
    obj_type = st.selectbox("Тип", ("max", "min"), index=0)
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    
    # Rasmdagi standart qiymatlar
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '≤', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    def add_constraint():
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})

    def remove_constraint(index):
        st.session_state.constraints.pop(index)

    current_constraints = []
    for i, cons in enumerate(st.session_state.constraints):
        st.write(f"Ограничение №{i+1}")
        c1_in, c2_in, op_in, c_target = st.columns([3, 3, 2, 3])
        with c1_in:
            a_val = st.number_input(f"A{i}", value=cons['a'], key=f"a{i}", format="%.1f", label_visibility="collapsed")
        with c2_in:
            b_val = st.number_input(f"B{i}", value=cons['b'], key=f"b{i}", format="%.1f", label_visibility="collapsed")
        with op_in:
            op_val = st.selectbox(f"Op{i}", ('≤', '≥', '='), index=('≤', '≥', '=').index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        with c_target:
            c_val = st.number_input(f"C{i}", value=cons['c'], key=f"c{i}", format="%.1f", label_visibility="collapsed")
        
        st.button(f"🗑️ Удалить {i+1}", key=f"del{i}", on_click=remove_constraint, args=(i,))
        current_constraints.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})

    st.session_state.constraints = current_constraints
    st.button("➕ Добавить ограничение", on_click=add_constraint)
    
    st.markdown("---")
    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- ALGORITM: HISOB-KITOB ---

def find_intersections(constraints):
    points = []
    lines = []
    for c in constraints:
        lines.append({'a': c['a'], 'b': c['b'], 'c': c['c']})
    
    # O'qlarni qo'shish (x=0, y=0)
    lines.append({'a': 1, 'b': 0, 'c': 0})
    lines.append({'a': 0, 'b': 1, 'c': 0})

    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            l1, l2 = lines[i], lines[j]
            det = l1['a'] * l2['b'] - l1['b'] * l2['a']
            if abs(det) > 1e-9:
                x = (l1['c'] * l2['b'] - l1['b'] * l2['c']) / det
                y = (l1['a'] * l2['c'] - l1['c'] * l2['a']) / det
                
                # ODR shartiga tekshirish
                feasible = True
                for c in constraints:
                    val = c['a'] * x + c['b'] * y
                    if c['op'] == '≤' and val > c['c'] + 1e-5: feasible = False
                    elif c['op'] == '≥' and val < c['c'] - 1e-5: feasible = False
                    elif c['op'] == '=' and abs(val - c['c']) > 1e-5: feasible = False
                
                if feasible: points.append((x, y))
    
    # Unikal nuqtalar
    unique = []
    for p in points:
        if not any(np.allclose(p, u, atol=1e-4) for u in unique): unique.append(p)
    return unique

# --- O'NG TOMON: GRAFIK ---
if solve_btn:
    st.subheader("График решения")
    corners = find_intersections(st.session_state.constraints)
    
    fig = go.Figure()
    x_range = np.linspace(-15, 15, 400)

    # 1. Chegara chiziqlarini chizish
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-9:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"L{i+1}", line=dict(width=2)))
        else:
            x_v = c['c'] / c['a']
            fig.add_trace(go.Scatter(x=[x_v, x_v], y=[-20, 25], mode='lines', name=f"L{i+1}", line=dict(width=2)))

    # 2. ODRni bo'yash
    if len(corners) >= 3:
        cx, cy = np.mean(corners, axis=0)
        corners.sort(key=lambda p: np.atan2(p[1]-cy, p[0]-cx))
        fig.add_trace(go.Scatter(x=[p[0] for p in corners], y=[p[1] for p in corners], fill="toself", fillcolor='rgba(0, 255, 0, 0.2)', line=dict(color='green'), name='ОДР'))

    # 3. Ichki nuqta va Daraja chizig'i (Algoritm bo'yicha)
    if len(corners) >= 2:
        # Algoritm Step 1: O'rta arifmetik
        ix = (corners[0][0] + corners[1][0]) / 2
        iy = (corners[0][1] + corners[1][1]) / 2
        fig.add_trace(go.Scatter(x=[ix], y=[iy], mode='markers', marker=dict(color='red', size=10), name='Внутренняя точка'))
        
        # Step 2: Daraja chizig'i (Level line)
        C_val = c1 * ix + c2 * iy
        if abs(c2) > 1e-9:
            y_level = (C_val - c1 * x_range) / c2
            fig.add_trace(go.Scatter(x=x_range, y=y_level, mode='lines', line=dict(color='black', dash='dash'), name='Линия уровня'))

    # 4. Optimum nuqta (Scipy bilan)
    obj = [-c1 if obj_type=="max" else c1, -c2 if obj_type=="max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None)
    
    if res.success:
        fig.add_trace(go.Scatter(x=[res.x[0]], y=[res.x[1]], mode='markers+text', text=["Оптимум"], marker=dict(color='gold', size=15, symbol='star'), name='Оптимум'))
        st.success(f"Оптимум найден: x={res.x[0]:.2f}, y={res.x[1]:.2f}")

    fig.update_layout(xaxis=dict(range=[-15, 15]), yaxis=dict(range=[-20, 25]), height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Введите данные и нажмите '🚀 Решить'")

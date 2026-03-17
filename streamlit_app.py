import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
import pandas as pd
from io import BytesIO

# Sahifa sozlamalari
st.set_page_config(page_title="LP-Visualizer UZ", layout="wide")

# Sarlavha
st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR (Kiritish bo'limi) ---
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
    
    # Standart chegaralar
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '<=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '<=', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '>=', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '<=', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '<=', 'c': 9.0}
        ]

    def add_constraint():
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '<=', 'c': 10.0})

    def remove_constraint(index):
        st.session_state.constraints.pop(index)

    current_constraints = []
    for i, cons in enumerate(st.session_state.constraints):
        st.write(f"Ограничение №{i+1}")
        c1_in, c2_in, op_in, c_target, del_col = st.columns([3, 3, 2, 3, 1])
        with c1_in:
            a_val = st.number_input(f"A{i}", value=cons['a'], key=f"a{i}", label_visibility="collapsed")
        with c2_in:
            b_val = st.number_input(f"B{i}", value=cons['b'], key=f"b{i}", label_visibility="collapsed")
        with op_in:
            # Belgilarni tanlashni to'g'irladik
            op_val = st.selectbox(f"Op{i}", ('<=', '>=', '='), 
                                  index=('<=', '>=', '=').index(cons['op']), 
                                  key=f"op{i}", label_visibility="collapsed")
        with c_target:
            c_val = st.number_input(f"C{i}", value=cons['c'], key=f"c{i}", label_visibility="collapsed")
        with del_col:
            # "Удалить" so'zi olib tashlandi, faqat ikona
            st.button("🗑️", key=f"del{i}", on_click=remove_constraint, args=(i,))
        
        current_constraints.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})

    st.button("➕ Добавить", on_click=add_constraint)
    st.markdown("---")
    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)

# --- FUNKSIYALAR ---
def find_intersections(constraints):
    points = []
    lines = [{'a': c['a'], 'b': c['b'], 'c': c['c']} for c in constraints]
    lines.extend([{'a': 1, 'b': 0, 'c': 0}, {'a': 0, 'b': 1, 'c': 0}]) # x=0, y=0

    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            l1, l2 = lines[i], lines[j]
            det = l1['a'] * l2['b'] - l1['b'] * l2['a']
            if abs(det) > 1e-9:
                x = (l1['c'] * l2['b'] - l1['b'] * l2['c']) / det
                y = (l1['a'] * l2['c'] - l1['c'] * l2['a']) / det
                feasible = True
                for c in constraints:
                    val = c['a'] * x + c['b'] * y
                    if c['op'] == '<=' and val > c['c'] + 1e-5: feasible = False
                    elif c['op'] == '>=' and val < c['c'] - 1e-5: feasible = False
                    elif c['op'] == '=' and abs(val - c['c']) > 1e-5: feasible = False
                if feasible and x >= -1e-5 and y >= -1e-5: points.append((x, y))
    
    unique = []
    for p in points:
        if not any(np.allclose(p, u, atol=1e-4) for u in unique): unique.append(p)
    return unique

# --- NATIJA VA GRAFIK ---
if solve_btn:
    st.subheader("График решения")
    corners = find_intersections(current_constraints)
    
    fig = go.Figure()
    x_plot = np.linspace(-5, 15, 400)

    # Chiziqlar
    for i, c in enumerate(current_constraints):
        if abs(c['b']) > 1e-9:
            y_plot = (c['c'] - c['a'] * x_plot) / c['b']
            fig.add_trace(go.Scatter(x=x_plot, y=y_plot, mode='lines', name=f"L{i+1}"))
        else:
            x_v = c['c'] / c['a']
            fig.add_trace(go.Scatter(x=[x_v, x_v], y=[-10, 20], mode='lines', name=f"L{i+1}"))

    # ODRni bo'yash
    if len(corners) >= 3:
        cx, cy = np.mean(corners, axis=0)
        corners.sort(key=lambda p: np.atan2(p[1]-cy, p[0]-cx))
        fig.add_trace(go.Scatter(x=[p[0] for p in corners], y=[p[1] for p in corners], 
                                 fill="toself", fillcolor='rgba(0, 255, 0, 0.2)', name='ОДР'))

    # Optimum hisoblash
    obj = [-c1 if obj_type=="max" else c1, -c2 if obj_type=="max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in current_constraints:
        if c['op'] == '<=': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '>=': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(0, None))
    
    if res.success:
        opt_x, opt_y = res.x
        opt_val = c1 * opt_x + c2 * opt_y
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=[f"Opt ({opt_x:.2f}, {opt_y:.2f})"], 
                                 marker=dict(color='gold', size=12, symbol='star'), name='Оптимум'))
        
        st.success(f"Yechim topildi: x={opt_x:.2f}, y={opt_y:.2f} | f(x,y)={opt_val:.2f}")

        # --- CSV/Excel hisobot (PDF o'rniga eng oson yo'li) ---
        report_data = {
            "Parametr": ["Optimum X", "Optimum Y", "Funksiya qiymati", "Turi"],
            "Qiymat": [opt_x, opt_y, opt_val, obj_type]
        }
        df = pd.DataFrame(report_data)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать результат (CSV)", data=csv, file_name="result.csv", mime="text/csv")
    
    fig.update_layout(xaxis=dict(range=[-2, 12]), yaxis=dict(range=[-2, 12]))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ma'lumotlarni kiriting va 'Решить' tugmasini bosing.")

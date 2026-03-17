import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
import pandas as pd

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# Sarlavha
st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR (KIRITISH) ---
with st.sidebar:
    st.header("🎯 Целевая функция")
    c_col1, c_col2, c_col3 = st.columns([2, 2, 2])
    with c_col1: c1 = st.number_input("C1", value=5.3, step=0.1, format="%.1f")
    with c_col2: c2 = st.number_input("C2", value=-7.1, step=0.1, format="%.1f")
    with c_col3: obj_type = st.selectbox("Тип", ("max", "min"))
    
    st.markdown("---")
    st.header("🚧 Ограничения")
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '<=', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '>=', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '<=', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '<=', 'c': 9.0}
        ]

    new_constraints = []
    for i, cons in enumerate(st.session_state.constraints):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        with col1: a_v = st.number_input(f"A{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with col2: b_v = st.number_input(f"B{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with col3: op_v = st.selectbox(f"Op{i}", ("<=", ">=", "="), index=("<=", ">=", "=").index(cons['op'] if cons['op'] in ["<=", ">=", "="] else "<="), key=f"op{i}", label_visibility="collapsed")
        with col4: c_v = st.number_input(f"C{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with col5: 
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_constraints.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    
    st.session_state.constraints = new_constraints
    if st.button("+ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '<=', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    col_b1, col_b2 = st.columns(2)
    with col_b1: solve = st.button("Решить", type="primary", use_container_width=True)
    with col_b2: 
        if st.button("Очистить", use_container_width=True):
            st.session_state.constraints = []
            st.rerun()

# --- GRAFIK VA NATIJA ---
if solve and st.session_state.constraints:
    # Hisoblash
    obj = [-c1 if obj_type == "max" else c1, -c2 if obj_type == "max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '<=': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '>=': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    fig = go.Figure()
    x_range = np.linspace(-20, 20, 1000)
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']

    for i, c in enumerate(st.session_state.constraints):
        label = f"{c['a']}*x + {c['b']}*y {c['op']} {c['c']}"
        if abs(c['b']) > 1e-9:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=label, line=dict(color=colors[i % len(colors)])))

    if res.success:
        opt_x, opt_y = res.x
        opt_val = c1 * opt_x + c2 * opt_y
        
        # Maqsad funksiyasi (Level Line)
        if abs(c2) > 1e-9:
            y_obj = (opt_val - c1 * x_range) / c2
            fig.add_trace(go.Scatter(x=x_range, y=y_obj, mode='lines', name="Целевая прямая", line=dict(color='black', dash='dash')))

        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=[f"Оптимум ({opt_x:.2f}, {opt_y:.2f})"], 
                                 marker=dict(color='gold', size=15, symbol='star'), name="Оптимум"))

        st.plotly_chart(fig, use_container_width=True)
        
        # Natija jadvali
        st.success(f"**Оптимальное решение найдено!**")
        st.write(f"X = {opt_x:.2f}, Y = {opt_y:.2f}, Z = {opt_val:.2f}")

        # PDF o'rniga Excel/CSV (xatolik bermaydi va aniq ishlaydi)
        df_res = pd.DataFrame({
            "Параметр": ["X", "Y", "Z (Result)", "Type"],
            "Значение": [round(opt_x, 4), round(opt_y, 4), round(opt_val, 4), obj_type]
        })
        csv = df_res.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать результат (CSV)", data=csv, file_name="result.csv", mime="text/csv")
    else:
        st.error("Решение не найдено.")

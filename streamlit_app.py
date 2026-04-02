import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

st.set_page_config(page_title="Линейное программирование", layout="wide")

# --- Sarlavha ---
st.markdown("<h2 style='text-align: center;'>📊 Линейное программирование — Решатель</h2>", unsafe_allow_html=True)

# Session state initialization
if 'rows' not in st.session_state:
    st.session_state.rows = [
        {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
        {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
        {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
        {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
        {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
    ]

# Asosiy konteyner: Chap tomonda kiritish, o'ngda grafik
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.write("### Целевая функция")
    c_cols = st.columns([1, 0.5, 1, 0.5, 0.2, 1])
    with c_cols[0]: c1 = st.number_input("C1", value=5.3, label_visibility="collapsed")
    with c_cols[1]: st.markdown("**\* x +**")
    with c_cols[2]: c2 = st.number_input("C2", value=-7.1, label_visibility="collapsed")
    with c_cols[3]: st.markdown("**\* y →**")
    with c_cols[5]: obj_type = st.selectbox("Type", ["max", "min"], label_visibility="collapsed")

    st.write("### Ограничения")
    
    current_constraints = []
    for i, row in enumerate(st.session_state.rows):
        r_cols = st.columns([1, 0.3, 1, 0.3, 0.8, 1, 0.5])
        with r_cols[0]: a_val = st.number_input(f"a{i}", value=float(row['a']), key=f"a_{i}", label_visibility="collapsed")
        with r_cols[1]: st.markdown("**\* x**<br>**+**", unsafe_allow_html=True)
        with r_cols[2]: b_val = st.number_input(f"b{i}", value=float(row['b']), key=f"b_{i}", label_visibility="collapsed")
        with r_cols[3]: st.markdown("**\* y**", unsafe_allow_html=True)
        with r_cols[4]: op_val = st.selectbox(f"op{i}", ["≤", "≥", "="], index=["≤", "≥", "="].index(row['op']), key=f"op_{i}", label_visibility="collapsed")
        with r_cols[5]: c_val = st.number_input(f"c{i}", value=float(row['c']), key=f"c_{i}", label_visibility="collapsed")
        with r_cols[6]: 
            if st.button("➖", key=f"del_{i}"):
                st.session_state.rows.pop(i)
                st.rerun()
        current_constraints.append({'a': a_val, 'b': b_val, 'op': op_val, 'c': c_val})

    st.session_state.rows = current_constraints

    if st.button("+ Добавить ограничение"):
        st.session_state.rows.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    btn_cols = st.columns([1, 1, 1.5])
    with btn_cols[0]: solve = st.button("Решить", type="primary", use_container_width=True)
    with btn_cols[1]: 
        if st.button("Очистить", use_container_width=True):
            st.session_state.rows = []
            st.rerun()
    with btn_cols[2]: st.button("Скачать отчёт (PDF)", use_container_width=True)

# --- Hisoblash va Grafik ---
with col_right:
    st.write("### График решения")
    if solve:
        # Linprog uchun ma'lumotlarni tayyorlash
        c_sign = -1 if obj_type == "max" else 1
        obj = [c_sign * c1, c_sign * c2]
        
        A_ub, b_ub, A_eq, b_eq = [], [], [], []
        for con in st.session_state.rows:
            if con['op'] == "≤":
                A_ub.append([con['a'], con['b']]); b_ub.append(con['c'])
            elif con['op'] == "≥":
                A_ub.append([-con['a'], -con['b']]); b_ub.append(-con['c'])
            else:
                A_eq.append([con['a'], con['b']]); b_eq.append(con['c'])

        res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

        fig = go.Figure()

        if res.success:
            ox, oy = res.x
            oz = c1*ox + c2*oy
            
            x_vals = np.linspace(ox-15, ox+15, 400)
            for i, con in enumerate(st.session_state.rows):
                if con['b'] != 0:
                    y_vals = (con['c'] - con['a']*x_vals) / con['b']
                    name = f"{con['a']:.2f}*x + {con['b']:.2f}*y {con['op']} {con['c']:.2f}"
                    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=name))

            # VZ Vektori va Nuqta
            fig.add_annotation(x=ox+2, y=oy+2, ax=ox, ay=oy, xref="x", yref="y", text="∇Z", showarrow=True, arrowhead=3, arrowcolor="red", font=dict(color="red"))
            fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', text=[f"Оптимум ({ox:.2f}; {oy:.2f})"], 
                                     marker=dict(color='gold', size=12, symbol='star'), name="Оптимум"))
            
            # Celeva pryamaya
            z_line_y = (oz - c1*x_vals) / c2
            fig.add_trace(go.Scatter(x=x_vals, y=z_line_y, mode='lines', name=f"Целевая прямая: {c1}*x + {c2}*y = {oz:.2f}", line=dict(color='black', dash='dot')))

        fig.update_layout(
            xaxis=dict(gridcolor='lightgrey', zerolinecolor='black'),
            yaxis=dict(gridcolor='lightgrey', zerolinecolor='black', scaleanchor="x"),
            plot_bgcolor='white', height=600, showlegend=True,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.6)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ma'lumotlarni kiriting va 'Решить' tugmasini bosing.")

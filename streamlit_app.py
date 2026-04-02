import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog

st.set_page_config(page_title="Линейное программирование", layout="wide")

# --- Interfeys qismi ---
st.write("## 📊 Линейное программирование — Решатель")

if 'rows' not in st.session_state:
    st.session_state.rows = [
        {'a': 3.2, 'b': -2.0, 'op': '=', 'c': 3.0},
        {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
        {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
        {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
        {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
    ]

col_in, col_gr = st.columns([1, 1.2])

with col_in:
    st.write("### Целевая функция")
    c_cols = st.columns([1.5, 0.4, 1.5, 0.4, 1])
    with c_cols[0]: c1 = st.number_input("C1", value=5.3, label_visibility="collapsed")
    with c_cols[1]: st.markdown("**\* x +**")
    with c_cols[2]: c2 = st.number_input("C2", value=-7.1, label_visibility="collapsed")
    with c_cols[3]: st.markdown("**\* y →**")
    with c_cols[4]: obj_type = st.selectbox("max/min", ["max", "min"], label_visibility="collapsed")

    st.write("### Ограничения")
    current_constraints = []
    for i, row in enumerate(st.session_state.rows):
        r_cols = st.columns([1.2, 0.4, 1.2, 0.4, 0.8, 1.2, 0.5])
        with r_cols[0]: a_v = st.number_input(f"a{i}", value=float(row['a']), key=f"a_{i}", label_visibility="collapsed")
        with r_cols[1]: st.markdown("**\* x**<br>**+**", unsafe_allow_html=True)
        with r_cols[2]: b_v = st.number_input(f"b{i}", value=float(row['b']), key=f"b_{i}", label_visibility="collapsed")
        with r_cols[3]: st.markdown("**\* y**", unsafe_allow_html=True)
        with r_cols[4]: op_v = st.selectbox(f"op{i}", ["≤", "≥", "="], index=["≤", "≥", "="].index(row['op']), key=f"op_{i}", label_visibility="collapsed")
        with r_cols[5]: c_v = st.number_input(f"c{i}", value=float(row['c']), key=f"c_{i}", label_visibility="collapsed")
        with r_cols[6]: 
            if st.button("➖", key=f"del_{i}"):
                st.session_state.rows.pop(i)
                st.rerun()
        current_constraints.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})
    
    st.session_state.rows = current_constraints
    if st.button("+ Добавить ограничение"):
        st.session_state.rows.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

# --- Grafik qismi ---
with col_gr:
    st.write("### График решения")
    c_sign = -1 if obj_type == "max" else 1
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for con in st.session_state.rows:
        if con['op'] == "≤": A_ub.append([con['a'], con['b']]); b_ub.append(con['c'])
        elif con['op'] == "≥": A_ub.append([-con['a'], -con['b']]); b_ub.append(-con['c'])
        else: A_eq.append([con['a'], con['b']]); b_eq.append(con['c'])

    res = linprog([c_sign * c1, c_sign * c2], A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    fig = go.Figure()

    if res.success:
        ox, oy = res.x
        oz = c1*ox + c2*oy
        x_range = np.linspace(ox-25, ox+25, 1000)
        
        # 1. Chegaraviy chiziqlar (L1, L2...) va afsona
        for i, con in enumerate(st.session_state.rows):
            if con['b'] != 0:
                y_range = (con['c'] - con['a']*x_range) / con['b']
                # Afsonada tenglamani to'liq ko'rsatish
                label = f"{con['a']}·x + {con['b']}·y {con['op']} {con['c']}"
                fig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines', name=label))

        # 2. Maqsadli chiziq (Целевая прямая)
        z_y = (oz - c1*x_range) / c2
        fig.add_trace(go.Scatter(x=x_range, y=z_y, mode='lines', name=f"Z: {c1}x + {c2}y = {oz:.2f}", line=dict(color='black', dash='dash')))

        # 3. VZ Vektori (Gradient)
        fig.add_annotation(x=ox+4, y=oy+4, ax=ox, ay=oy, xref="x", yref="y", text="∇Z", showarrow=True, arrowhead=3, arrowcolor="red", font=dict(color="red"))
        
        # 4. Optimum nuqta (Yulduzcha bilan)
        fig.add_trace(go.Scatter(x=[ox], y=[oy], mode='markers+text', text=[f"Optimum ({ox:.2f}; {oy:.2f})"], 
                                 marker=dict(color='gold', size=14, symbol='star'), name="Оптимум"))

    # --- KICHIK KVADRAT SETKA SOZLAMALARI ---
    fig.update_layout(
        xaxis=dict(
            showgrid=True, 
            gridcolor='LightGrey', 
            zerolinecolor='black', 
            range=[ox-20, ox+20],
            dtick=5 # Setka kvadratlari hajmi 5 birlik (kichikroq kvadratlar)
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='LightGrey', 
            zerolinecolor='black', 
            range=[oy-20, oy+20],
            dtick=5, # Kichik kvadratli setka
            scaleanchor="x"
        ),
        plot_bgcolor='white',
        height=700,
        legend=dict(x=0.6, y=0.98, bordercolor="Black", borderwidth=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

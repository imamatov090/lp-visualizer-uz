import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF
import base64

# Sahifa sozlamalari
st.set_page_config(page_title="LPP Visual Solver", layout="wide")

# --- PDF GENERATSIYA FUNKSIYASI ---
def create_pdf(constraints, obj_coeffs, obj_type, res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Chiziqli dasturlash masalasi yechimi", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Maqsad funksiyasi: Z = {obj_coeffs[0]}*x + {obj_coeffs[1]}*y -> {obj_type}", ln=True)
    
    pdf.ln(5)
    pdf.cell(200, 10, "Cheklovlar:", ln=True)
    for i, c in enumerate(constraints):
        pdf.cell(200, 10, f"L{i+1}: {c['a']}*x + {c['b']}*y {c['op']} {c['c']}", ln=True)
    
    if res.success:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, f"Optimal yechim: x = {res.x[0]:.2f}, y = {res.x[1]:.2f}", ln=True)
        pdf.cell(200, 10, f"Z natijasi: {res.fun if obj_type=='min' else -res.fun:.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFEYS: MAQSAD FUNKSIYASI ---
st.title("LPP Vizualizatsiya va Tahlil")

st.subheader("Maqsad funksiyasi")
c_cols = st.columns([1, 0.5, 1, 0.5, 1])
with c_cols[0]: c_main1 = st.number_input("Z x koeffitsienti", value=3.2)
with c_cols[1]: st.markdown('<p style="padding-top: 35px; font-weight: bold;">*x +</p>', unsafe_allow_html=True)
with c_cols[2]: c_main2 = st.number_input("Z y koeffitsienti", value=-2.0)
with c_cols[3]: st.markdown('<p style="padding-top: 35px; font-weight: bold;">*y —></p>', unsafe_allow_html=True)
with c_cols[4]: obj_type = st.selectbox("Maqsad", ["max", "min"])

# --- INTERFEYS: CHEKLOVLAR ---
st.subheader("Cheklovlar")
if 'constraints' not in st.session_state:
    st.session_state.constraints = [{'a': 3.2, 'b': -2.0, 'op': '≤', 'c': 3.0}]

def add_constraint(): st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
def remove_constraint(): 
    if len(st.session_state.constraints) > 1: st.session_state.constraints.pop()

for i, constr in enumerate(st.session_state.constraints):
    # ELEMENTLARNI BIR QATORGA TEKISLASH (CSS padding bilan)
    cols = st.columns([1, 0.5, 1, 0.5, 0.7, 1])
    with cols[0]:
        st.session_state.constraints[i]['a'] = st.number_input(f"a{i}", value=float(constr['a']), key=f"a_{i}", label_visibility="collapsed")
    with cols[1]:
        st.markdown('<p style="padding-top: 10px; font-weight: bold; text-align: center;">*x +</p>', unsafe_allow_html=True)
    with cols[2]:
        st.session_state.constraints[i]['b'] = st.number_input(f"b{i}", value=float(constr['b']), key=f"b_{i}", label_visibility="collapsed")
    with cols[3]:
        st.markdown('<p style="padding-top: 10px; font-weight: bold; text-align: center;">*y</p>', unsafe_allow_html=True)
    with cols[4]:
        st.session_state.constraints[i]['op'] = st.selectbox(f"op{i}", ["≤", "≥", "="], index=["≤", "≥", "="].index(constr['op']), key=f"op_{i}", label_visibility="collapsed")
    with cols[5]:
        st.session_state.constraints[i]['c'] = st.number_input(f"c{i}", value=float(constr['c']), key=f"c_{i}", label_visibility="collapsed")

st.button("Cheklov qo'shish", on_click=add_constraint)
st.button("Oxirgisini o'chirish", on_click=remove_constraint)

# --- HISOB-KITOB VA GRAFIK ---
solve_btn = st.button("Yechish va Grafikni ko'rish")

if solve_btn:
    # Ma'lumotlarni yechish uchun tayyorlash
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    coeffs = [-c_main1 if obj_type == "max" else c_main1, -c_main2 if obj_type == "max" else c_main2]
    
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(coeffs, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None), method='highs')

    # --- GRAFIK QISMI (O'ZGARMAYDIGAN FINAL DIZAYN) ---
    fig = go.Figure()
    limit = 16
    x_range = np.linspace(-limit*2, limit*2, 1000)

    # ODR hisoblash
    corner_points = []
    for i in range(len(st.session_state.constraints)):
        for j in range(i + 1, len(st.session_state.constraints)):
            try:
                line1, line2 = st.session_state.constraints[i], st.session_state.constraints[j]
                A_mat = np.array([[line1['a'], line1['b']], [line2['a'], line2['b']]])
                B_mat = np.array([line1['c'], line2['c']])
                p = np.linalg.solve(A_mat, B_mat)
                
                is_valid = True
                for check in st.session_state.constraints:
                    val = check['a']*p[0] + check['b']*p[1]
                    if check['op'] == '≤' and val > check['c'] + 1e-5: is_valid = False
                    elif check['op'] == '≥' and val < check['c'] - 1e-5: is_valid = False
                    elif check['op'] == '=' and abs(val - check['c']) > 1e-5: is_valid = False
                if is_valid: corner_points.append(p)
            except: continue

    if corner_points:
        pts = np.array(corner_points)
        center = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:,1]-center[1], pts[:,0]-center[0])
        pts = pts[np.argsort(angles)]
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], fill="toself", fillcolor='rgba(0, 102, 204, 0.15)', line=dict(color='rgba(255,255,255,0)'), name="ОДР"))
        fig.add_trace(go.Scatter(x=pts[:,0], y=pts[:,1], mode='markers', marker=dict(color='red', size=8), name="Угловые точки"))
        fig.add_trace(go.Scatter(x=[center[0]], y=[center[1]], mode='markers', marker=dict(color='blue', size=8), name="Внутр. точка"))

    # Cheklov chiziqlari (Legendada to'liq, grafikda L1...)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-7:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            name_label = f"L{i+1}: {c['a']}*x+ {c['b']}*y {c['op']} {c['c']}"
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', line=dict(color=colors[i % len(colors)], width=2), name=name_label))
            
            # Grafik ichidagi belgi
            lx = -limit + 4 + i*1.5
            ly = (c['c'] - c['a'] * lx) / c['b']
            if -limit < ly < limit:
                fig.add_annotation(x=lx, y=ly, text=f"L{i+1}", showarrow=False, font=dict(color=colors[i % len(colors)], size=12, family="Arial Bold"), bgcolor="white")

    if res.success:
        opt_x, opt_y = res.x
        opt_val = c_main1 * opt_x + c_main2 * opt_y
        
        # Maqsad chizig'i va O'rtacha chiziq
        if abs(c_main2) > 1e-7:
            y_opt = (opt_val - c_main1 * x_range) / c_main2
            fig.add_trace(go.Scatter(x=x_range, y=y_opt, mode='lines', line=dict(color='black', dash='dash', width=2), name=f"Целевая прямая (Z={opt_val:.2f})"))
            
            if corner_points:
                z_mid = c_main1 * center[0] + c_main2 * center[1]
                y_mid = (z_mid - c_main1 * x_range) / c_main2
                fig.add_trace(go.Scatter(x=x_range, y=y_mid, mode='lines', line=dict(color='green', dash='dot', width=1.5), name=f"Линия уровня (Z={z_mid:.2f})"))

        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', text=["Оптимум"], textposition="top right", 
                                 marker=dict(color='gold', size=14, symbol='star', line=dict(color='black', width=1)), name="Оптимум"))

    # O'QLARNI SOZLASH (Strelka, 0 va Ticks)
    fig.add_annotation(x=limit, y=0, ax=-limit, ay=0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=2)
    fig.add_annotation(x=0, y=limit, ax=0, ay=-limit, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=2)
    
    for i in range(-limit+1, limit):
        fig.add_shape(type="line", x0=i, y0=-0.2, x1=i, y1=0.2, line=dict(color="black", width=1))
        fig.add_shape(type="line", x0=-0.2, y0=i, x1=0.2, y1=i, line=dict(color="black", width=1))
        if i != 0 and i % 2 == 0:
            fig.add_annotation(x=i, y=-0.8, text=str(i), showarrow=False, font=dict(size=10))
            fig.add_annotation(x=-0.8, y=i, text=str(i), showarrow=False, font=dict(size=10))

    fig.add_annotation(x=-0.6, y=-0.6, text="0", showarrow=False, font=dict(size=12, family="Arial Black"))
    fig.add_annotation(x=limit, y=0.8, text="X", showarrow=False, font=dict(size=16, family="Arial Black"))
    fig.add_annotation(x=0.8, y=limit, text="Y", showarrow=False, font=dict(size=16, family="Arial Black"))

    fig.update_layout(
        xaxis=dict(showgrid=False, visible=False, range=[-limit, limit+1]),
        yaxis=dict(showgrid=False, visible=False, range=[-limit, limit+1]),
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center", bordercolor="Black", borderwidth=1),
        height=800, margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- PDF EXPORT TUGMASI ---
    pdf_bytes = create_pdf(st.session_state.constraints, [c_main1, c_main2], obj_type, res)
    st.download_button(label="Natijalarni PDF ko'rinishida yuklab olish", data=pdf_bytes, file_name="yechim.pdf", mime="application/pdf")

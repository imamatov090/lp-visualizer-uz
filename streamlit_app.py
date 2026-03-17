import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog
from fpdf import FPDF

# Sahifa sozlamalari
st.set_page_config(page_title="Решатель ЛП", layout="wide")

# Sarlavha
st.markdown("<h1 style='text-align: center;'>📊 Линейное программирование — Решатель</h1>", unsafe_allow_html=True)
st.markdown("---")

# PDF yaratish funksiyasi (Rus tilida)
def create_pdf(opt_x, opt_y, opt_val, obj_type, constraints):
    pdf = FPDF()
    pdf.add_page()
    # Standart shrift kirillitsani qo'llab-quvvatlamasligi mumkin, 
    # shuning uchun lotin harflarida lekin ruscha ma'noda yozamiz yoki oddiy xulosa qilamiz
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Otchet resheniya zadachi LP", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tip funksii: {obj_type}", ln=True)
    pdf.cell(200, 10, txt=f"Optimalnoe znachenie X: {opt_x:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Optimalnoe znachenie Y: {opt_y:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Znachenie tselevoy funksii: {opt_val:.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KIRITISH ---
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
    
    if 'constraints' not in st.session_state:
        st.session_state.constraints = [
            {'a': 3.2, 'b': -2.0, 'op': '≤', 'c': 3.0},
            {'a': 1.6, 'b': 2.3, 'op': '≤', 'c': -5.0},
            {'a': 3.2, 'b': -6.0, 'op': '≥', 'c': 7.0},
            {'a': 7.0, 'b': -2.0, 'op': '≤', 'c': 10.0},
            {'a': -6.5, 'b': 3.0, 'op': '≤', 'c': 9.0}
        ]

    new_constraints = []
    # "Ограничение №..." yozuvlari olib tashlandi
    for i, cons in enumerate(st.session_state.constraints):
        c1_in, c2_in, op_in, c_target, del_btn = st.columns([2, 2, 2, 2, 1])
        with c1_in:
            a_v = st.number_input(f"A{i}", value=float(cons['a']), key=f"a{i}", label_visibility="collapsed")
        with c2_in:
            b_v = st.number_input(f"B{i}", value=float(cons['b']), key=f"b{i}", label_visibility="collapsed")
        with op_in:
            op_v = st.selectbox(f"Op{i}", ('≤', '≥', '='), index=('≤', '≥', '=').index(cons['op']), key=f"op{i}", label_visibility="collapsed")
        with c_target:
            c_v = st.number_input(f"C{i}", value=float(cons['c']), key=f"c{i}", label_visibility="collapsed")
        with del_btn:
            if st.button("🗑️", key=f"del{i}"):
                st.session_state.constraints.pop(i)
                st.rerun()
        new_constraints.append({'a': a_v, 'b': b_v, 'op': op_v, 'c': c_v})

    st.session_state.constraints = new_constraints
    
    if st.button("➕ Добавить ограничение"):
        st.session_state.constraints.append({'a': 1.0, 'b': 1.0, 'op': '≤', 'c': 10.0})
        st.rerun()

    st.markdown("---")
    solve_btn = st.button("🚀 Решить", type="primary", use_container_width=True)
    if st.button("🧹 Очистить", use_container_width=True):
        st.session_state.constraints = []
        st.rerun()

# --- ASOSIY QISM ---
if solve_btn:
    # Hisoblash (Linear Programming)
    obj = [-c1 if obj_type=="max" else c1, -c2 if obj_type=="max" else c2]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in st.session_state.constraints:
        if c['op'] == '≤': A_ub.append([c['a'], c['b']]); b_ub.append(c['c'])
        elif c['op'] == '≥': A_ub.append([-c['a'], -c['b']]); b_ub.append(-c['c'])
        else: A_eq.append([c['a'], c['b']]); b_eq.append(c['c'])
    
    res = linprog(obj, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None, bounds=(None, None))

    # Grafik (Plotly)
    fig = go.Figure()
    x_range = np.linspace(-20, 20, 500)
    
    for i, c in enumerate(st.session_state.constraints):
        if abs(c['b']) > 1e-9:
            y_vals = (c['c'] - c['a'] * x_range) / c['b']
            fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f"Линия {i+1}"))
        else:
            x_v = c['c'] / c['a']
            fig.add_trace(go.Scatter(x=[x_v, x_v], y=[-50, 50], mode='lines', name=f"Линия {i+1}"))

    if res.success:
        opt_x, opt_y = res.x
        opt_val = c1 * opt_x + c2 * opt_y
        
        # Optimum nuqtani belgilash
        fig.add_trace(go.Scatter(x=[opt_x], y=[opt_y], mode='markers+text', 
                                 text=["Оптимум"], textposition="top center",
                                 marker=dict(color='red', size=15, symbol='star')))
        
        st.subheader("📉 График решения")
        st.plotly_chart(fig, use_container_width=True)

        # Natijalarni chiqarish
        st.success(f"### Результат:")
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Оптимальный X", f"{opt_x:.2f}")
        col_res1.metric("Оптимальный Y", f"{opt_y:.2f}")
        col_res2.metric("Значение функции", f"{opt_val:.2f}")

        # PDF yuklab olish
        pdf_data = create_pdf(opt_x, opt_y, opt_val, obj_type, st.session_state.constraints)
        st.download_button(label="📥 Скачать отчёт (PDF)", 
                           data=pdf_data, 
                           file_name="otchet_resheniya.pdf", 
                           mime="application/pdf")
    else:
        st.error("Решение не найдено. Проверьте ограничения.")

else:
    st.info("Введите параметры функции и ограничений, затем нажмите кнопку 'Решить'.")

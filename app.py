import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="다단 사출 게이트 계산기 (Multi-Step)", layout="wide")

st.title("⚙️ 다단 사출 게이트 시간 계산기 (Multi-Step)")
st.caption("사출 속도 구간(Step)을 1~3단 중에서 자유롭게 설정할 수 있습니다.")
st.markdown("---")

# ==========================================
# [SECTION 1] 상단: 설정 입력(좌) vs 그래프(우)
# ==========================================
st.subheader("📍 1. 사출 조건 및 레진 선택")

top_left, top_right = st.columns([0.4, 0.6], gap="medium")

with top_left:
    with st.container(border=True):
        st.markdown("#### 🛠️ 사출 기본 설정")
        
        # 1. 레진 선택
        resin_type = st.selectbox(
            "사용 레진 선택 (Resin Type)",
            ["PC+ABS (ED18)", "ABS (General)", "HIPS (High Impact PS)"], index=0
        )
        
        # 2. 사출 압력 & 구간 수 선택 (핵심 기능)
        c_press, c_step = st.columns(2)
        inj_pressure = c_press.number_input("사출 압력 (bar)", value=1000.0, step=10.0, format="%.1f")
        
        # [Step 선택 기능] 화살표로 1~3단 조절
        num_steps = c_step.number_input("속도 구간 수 (Step)", min_value=1, max_value=3, value=3)

        # 3. 압축률 자동 계산
        resin_coeffs = {"PC+ABS (ED18)": 0.0060, "ABS (General)": 0.0065, "HIPS (High Impact PS)": 0.0075}
        current_coeff = resin_coeffs[resin_type]
        
        auto_mode = st.toggle(f"압축률 자동 계산", value=True)
        if auto_mode:
            calc_comp = min(inj_pressure * current_coeff, 20.0)
            compression_rate = st.slider("적용 압축률 (%)", 0.0, 20.0, float(f"{calc_comp:.1f}"), disabled=True, format="%.1f%%")
        else:
            compression_rate = st.slider("압축률 수동 설정 (%)", 0.0, 20.0, 6.0, 0.1, format="%.1f%%")

        st.markdown("---")
        st.markdown(f"#### 🚀 {num_steps}단 속도 프로파일 설정")

        # 위치 설정
        c1, c2 = st.columns(2)
        start_pos = c1.number_input("계량 완료 (mm)", value=150.0, format="%.1f")
        vp_pos = c2.number_input("V-P 절환 (mm)", value=20.0, format="%.1f")
        
        # --- 다단 속도 동적 입력창 ---
        # 기본값 초기화
        v1, s1, v2, s2, v3 = 0, 0, 0, 0, 0
        
        if num_steps == 1:
            # 1단 사출: Start -> VP
            v1 = st.number_input("1속 속도 (mm/s)", value=60.0, format="%.1f")
            # 1단은 중간 종료점이 없음 (VP까지 직행)
            
        elif num_steps == 2:
            # 2단 사출: Start -> s1 -> VP
            c_v1, c_s1 = st.columns(2)
            v1 = c_v1.number_input("1속 속도 (mm/s)", value=60.0, format="%.1f")
            s1 = c_s1.number_input("1속 종료 (mm)", value=80.0, format="%.1f")
            
            v2 = st.number_input("2속 속도 (mm/s)", value=40.0, format="%.1f")
            
        elif num_steps == 3:
            # 3단 사출
            c_v1, c_s1 = st.columns(2)
            v1 = c_v1.number_input("1속 속도 (mm/s)", value=60.0, format="%.1f")
            s1 = c_s1.number_input("1속 종료 (mm)", value=100.0, format="%.1f")
            
            c_v2, c_s2 = st.columns(2)
            v2 = c_v2.number_input("2속 속도 (mm/s)", value=40.0, format="%.1f")
            s2 = c_s2.number_input("2속 종료 (mm)", value=50.0, format="%.1f")
            
            v3 = st.number_input("3속 속도 (mm/s)", value=20.0, format="%.1f")

# --- 계산 로직 (Step별 분기) ---
comp_factor = 1 + (compression_rate / 100.0)
t1_theo, t2_theo, t3_theo = 0, 0, 0
total_time = 0
valid_input = True

# 입력값 검증 및 시간 계산
if num_steps == 1:
    if v1 > 0:
        t1_theo = (start_pos - vp_pos) / v1
        total_time = t1_theo * comp_factor
    else: valid_input = False
elif num_steps == 2:
    if v1 > 0 and v2 > 0:
        t1_theo = (start_pos - s1) / v1
        t2_theo = (s1 - vp_pos) / v2
        total_time = (t1_theo + t2_theo) * comp_factor
    else: valid_input = False
elif num_steps == 3:
    if v1 > 0 and v2 > 0 and v3 > 0:
        t1_theo = (start_pos - s1) / v1
        t2_theo = (s1 - s2) / v2
        t3_theo = (s2 - vp_pos) / v3
        total_time = (t1_theo + t2_theo + t3_theo) * comp_factor
    else: valid_input = False

def get_corrected_time(pos):
    if not valid_input: return 0
    theo = 0
    if num_steps == 1:
        theo = (start_pos - pos) / v1
    elif num_steps == 2:
        if pos >= s1: theo = (start_pos - pos) / v1
        else: theo = t1_theo + (s1 - pos) / v2
    elif num_steps == 3:
        if pos >= s1: theo = (start_pos - pos) / v1
        elif pos >= s2: theo = t1_theo + (s1 - pos) / v2
        else: theo = t1_theo + t2_theo + (s2 - pos) / v3
    return theo * comp_factor

with top_right:
    st.markdown("#### 📈 속도 및 시간 프로파일")
    
    if valid_input and total_time > 0:
        fig = go.Figure()
        
        # Step별 그래프 좌표 설정
        x_vals, y_vals = [], []
        if num_steps == 1:
            x_vals = [start_pos, vp_pos]
            y_vals = [v1, v1]
        elif num_steps == 2:
            x_vals = [start_pos, s1, s1, vp_pos]
            y_vals = [v1, v1, v2, v2]
        elif num_steps == 3:
            x_vals = [start_pos, s1, s1, s2, s2, vp_pos]
            y_vals = [v1, v1, v2, v2, v3, v3]

        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines+markers', fill='tozeroy', name='Speed',
            line=dict(color='#1f77b4', width=3), marker=dict(size=6)
        ))

        # V/P 라인
        last_v = y_vals[-1]
        fig.add_vline(x=vp_pos, line_width=2, line_dash="dash", line_color="red")
        fig.add_annotation(
            x=vp_pos, y=last_v * 1.2,
            text="<b>V/P</b>", showarrow=True, arrowhead=2, arrowcolor="red",
            font=dict(color="red", size=12)
        )

        fig.update_layout(
            title=dict(text=f"<b>SCREW POSITION vs SPEED ({num_steps} Steps)</b>", font=dict(size=15)),
            xaxis=dict(title="<b>SCREW POSITION (mm)</b>", autorange="reversed", gridcolor='lightgrey'),
            yaxis=dict(title="<b>SPEED (mm/s)</b>", gridcolor='lightgrey'),
            height=400, margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white', hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"**⏱️ [{num_steps}단 제어] 예상 총 사출 시간: {total_time:.3f} sec**")
    else:
        st.error("⚠️ 속도값은 0보다 커야 합니다.")

st.divider()

# ==========================================
# [SECTION 2] 하단: 게이트 입력(좌) vs 결과(우)
# ==========================================
left_col, right_col = st.columns([0.6, 0.4], gap="large")

with left_col:
    st.subheader("📥 2. 게이트 위치 입력 (30 Gates)")
    with st.container(border=True):
        in_cols = st.columns(2)
        gate_data = []
        for i in range(1, 31):
            target_col = in_cols[(i-1)//15]
            with target_col:
                r = st.columns([1, 2, 2])
                r[0].markdown(f"<div style='padding-top:10px;'><b>G{i:02d}</b></div>", unsafe_allow_html=True)
                op = r[1].text_input("Op", key=f"o{i}", placeholder="Open", label_visibility="collapsed")
                cl = r[2].text_input("Cl", key=f"c{i}", placeholder="Close", label_visibility="collapsed")
                
                err = False
                if op and cl:
                    try:
                        if float(op) <= float(cl): err = True
                    except ValueError: pass
                gate_data.append({"id": i, "op": op, "cl": cl, "err": err})

with right_col:
    st.subheader("📤 3. 환산 시간 결과")
    
    results = []
    for g in gate_data:
        if g["op"] and g["cl"] and not g["err"]:
            try:
                op_val = float(g["op"])
                cl_val = float(g["cl"])
                ot = get_corrected_time(op_val)
                ct = get_corrected_time(cl_val)
                results.append({"Gate": f"G{g['id']:02d}", "Open(s)": round(ot, 3), "Close(s)": round(ct, 3)})
            except ValueError: continue
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True, height=600)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 엑셀 다운로드 (CSV)", csv, f"results_{num_steps}step.csv", "text/csv", type="primary")
    else:
        st.info("왼쪽에 게이트 위치를 입력하세요.")

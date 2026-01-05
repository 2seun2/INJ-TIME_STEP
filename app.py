import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="다단 사출 게이트 계산기 (Pro+)", layout="wide")

st.title("⚙️ 다단 사출 게이트 시간 계산기 (Pro+)")
st.caption("사출 압력에 따른 레진 압축률 자동 보정 기능이 포함된 전문가 버전입니다.")
st.markdown("---")

# ==========================================
# [SECTION 1] 상단: 설정 입력(좌) vs 그래프(우)
# ==========================================
st.subheader("📍 1. 사출 조건 및 레진 특성")

top_left, top_right = st.columns([0.4, 0.6], gap="medium")

with top_left:
    with st.container(border=True):
        st.markdown("#### 🧪 압력 및 압축률 설정")
        
        # 1. 사출 압력 입력
        inj_pressure = st.number_input("실제 사출 압력 (Injection Pressure, bar)", value=1000.0, step=10.0, format="%.1f")
        
        # 2. 압축률 자동 계산 옵션
        auto_mode = st.toggle("압력 연동 자동 계산 (PC+ABS 기준)", value=True)
        
        if auto_mode:
            # [공식] PC+ABS 기준: 1000bar일 때 약 6.0% (계수 0.006)
            # 압력이 500bar면 3.0%, 1500bar면 9.0%로 자동 변환
            calc_comp = inj_pressure * 0.006
            if calc_comp > 20.0: calc_comp = 20.0 # 최대치 제한
            
            compression_rate = st.slider(
                "적용된 레진 압축률 (%)", 
                min_value=0.0, max_value=20.0, 
                value=float(f"{calc_comp:.1f}"), 
                disabled=True, # 자동 모드일 때는 슬라이더 잠금
                format="%.1f%%"
            )
            st.info(f"💡 {inj_pressure} bar 압력 기준, 약 {compression_rate}% 압축 발생")
        else:
            compression_rate = st.slider(
                "레진 압축률 수동 설정 (%)", 
                min_value=0.0, max_value=20.0, 
                value=6.0, step=0.1, 
                format="%.1f%%"
            )
            st.warning("사용자 수동 설정 모드입니다.")

        st.markdown("---")
        st.markdown("#### 🛠️ 위치 및 속도 설정")

        c1, c2 = st.columns(2)
        start_pos = c1.number_input("계량 완료 (mm)", value=150.0, step=1.0, format="%.1f")
        vp_pos = c2.number_input("V-P 절환 (mm)", value=20.0, step=1.0, format="%.1f")
        
        # 다단 속도 입력
        c_v1, c_s1 = st.columns(2)
        v1 = c_v1.number_input("1속 속도 (mm/s)", value=60.0, min_value=0.1, format="%.1f")
        s1 = c_s1.number_input("1속 종료 (mm)", value=100.0, format="%.1f")
        
        c_v2, c_s2 = st.columns(2)
        v2 = c_v2.number_input("2속 속도 (mm/s)", value=40.0, min_value=0.1, format="%.1f")
        s2 = c_s2.number_input("2속 종료 (mm)", value=50.0, format="%.1f")
        
        c_v3, _ = st.columns(2)
        v3 = c_v3.number_input("3속 속도 (mm/s)", value=20.0, min_value=0.1, format="%.1f")

# --- 계산 로직 (압력/압축률 반영) ---
comp_factor = 1 + (compression_rate / 100.0)

if v1 > 0 and v2 > 0 and v3 > 0:
    t1_theo = (start_pos - s1) / v1
    t2_theo = (s1 - s2) / v2
    t3_theo = (s2 - vp_pos) / v3
    
    # 압축 지연이 포함된 총 예상 시간
    total_time = (t1_theo + t2_theo + t3_theo) * comp_factor
else:
    t1_theo, t2_theo, t3_theo = 0, 0, 0
    total_time = 0

def get_corrected_time(pos):
    if v1 <= 0 or v2 <= 0 or v3 <= 0: return 0
    
    # 1. 이론적 도달 시간 계산
    if pos >= s1:
        theo_time = (start_pos - pos) / v1
    elif pos >= s2:
        theo_time = t1_theo + (s1 - pos) / v2
    else:
        theo_time = t1_theo + t2_theo + (s2 - pos) / v3
    
    # 2. 압축률 보정 (시간 지연 반영)
    return theo_time * comp_factor

with top_right:
    st.markdown("#### 📈 속도 및 시간 프로파일")
    
    if total_time > 0:
        fig = go.Figure()
        
        # 속도 프로파일
        fig.add_trace(go.Scatter(
            x=[start_pos, s1, s1, s2, s2, vp_pos],
            y=[v1, v1, v2, v2, v3, v3],
            mode='lines+markers', fill='tozeroy', name='Speed',
            line=dict(color='#1f77b4', width=3), marker=dict(size=6)
        ))

        # V/P 절환위치
        fig.add_vline(x=vp_pos, line_width=2, line_dash="dash", line_color="red")
        fig.add_annotation(
            x=vp_pos, y=v3 + (max(v1,v2,v3)*0.15),
            text="<b>V/P 절환</b>", showarrow=True, arrowhead=2, arrowcolor="red",
            font=dict(color="red", size=12)
        )

        fig.update_layout(
            title=dict(text="<b>SCREW POSITION vs SPEED</b>", font=dict(size=15)),
            xaxis=dict(title="<b>SCREW POSITION (mm)</b>", autorange="reversed", gridcolor='lightgrey'),
            yaxis=dict(title="<b>SPEED (mm/s)</b>", gridcolor='lightgrey'),
            height=400, margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white', hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 결과 요약
        st.success(f"""
        **⏱️ 최종 예상 사출 시간: {total_time:.3f} sec**
        - 이론 이동 시간: {(total_time/comp_factor):.3f} sec
        - **압축 지연 시간: {(total_time - total_time/comp_factor):.3f} sec** (압력 {inj_pressure}bar 영향)
        """)
    else:
        st.error("⚠️ 속도 설정값을 확인해주세요.")

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
    st.subheader("📤 3. 압력 보정 환산 시간")
    st.caption(f"사출 압력 {inj_pressure}bar 조건에서의 예상 시간입니다.")
    
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
        st.download_button("💾 엑셀 다운로드 (CSV)", csv, "pressure_corrected_results.csv", "text/csv", type="primary")
    else:
        st.info("왼쪽에 게이트 위치를 입력하세요.")

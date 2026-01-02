import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="다단 사출 게이트 계산기", layout="wide")

st.title("⚙️ 다단 사출 게이트 시간 계산기")
st.markdown("---")

# ==========================================
# [SECTION 1] 상단: 설정 입력(좌) vs 그래프(우)
# ==========================================
st.subheader("📍 1. 사출 조건 및 속도 프로파일")

top_left, top_right = st.columns([0.4, 0.6], gap="medium")

with top_left:
    st.markdown("#### 🛠️ 다단 속도 설정")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        start_pos = c1.number_input("계량 완료 위치 (mm)", value=150.0, step=1.0, format="%.1f")
        vp_pos = c2.number_input("V-P 절환 위치 (mm)", value=20.0, step=1.0, format="%.1f")
        
        st.markdown("---")
        
        # 1속
        c_v1, c_s1 = st.columns(2)
        v1 = c_v1.number_input("1속 속도 (mm/s)", value=60.0, min_value=0.1, step=1.0, format="%.1f")
        s1 = c_s1.number_input("1속 종료 (mm)", value=100.0, step=1.0, format="%.1f")
        
        # 2속
        c_v2, c_s2 = st.columns(2)
        v2 = c_v2.number_input("2속 속도 (mm/s)", value=40.0, min_value=0.1, step=1.0, format="%.1f")
        s2 = c_s2.number_input("2속 종료 (mm)", value=50.0, step=1.0, format="%.1f")
        
        # 3속 (오류 수정된 부분: 리스트 인덱싱 [0] 추가 및 레이아웃 정렬)
        # 위쪽과 줄을 맞추기 위해 columns(2)로 나누고 왼쪽 칸만 사용합니다.
        c_v3, _ = st.columns(2) 
        v3 = c_v3.number_input("3속 속도 (mm/s)", value=20.0, min_value=0.1, step=1.0, format="%.1f")

# --- 계산 로직 ---
if v1 > 0 and v2 > 0 and v3 > 0:
    t1 = (start_pos - s1) / v1
    t2 = (s1 - s2) / v2
    t3 = (s2 - vp_pos) / v3
    total_time = t1 + t2 + t3
else:
    t1, t2, t3, total_time = 0, 0, 0, 0

def get_time(pos):
    if v1 <= 0 or v2 <= 0 or v3 <= 0: return 0
    if pos >= s1: return (start_pos - pos) / v1
    elif pos >= s2: return t1 + (s1 - pos) / v2
    else: return t1 + t2 + (s2 - pos) / v3

with top_right:
    st.markdown("#### 📈 속도 프로파일 (Speed Graph)")
    
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
            height=380, margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white', hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"⏱️ 계산된 총 사출 시간: **{total_time:.3f} sec**")
    else:
        st.error("⚠️ 속도는 0보다 커야 합니다.")

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
                ot = get_time(float(g["op"]))
                ct = get_time(float(g["cl"]))
                results.append({"Gate": f"G{g['id']:02d}", "Open(s)": round(ot, 3), "Close(s)": round(ct, 3)})
            except ValueError: continue
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True, height=600)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 엑셀 다운로드 (CSV)", csv, "injection_results.csv", "text/csv", type="primary")
    else:
        st.info("왼쪽에 게이트 위치를 입력하세요.")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="다단 사출 게이트 타이머", layout="wide")

st.title("🚀 다단 사출(Multi-Stage) 게이트 시간 계산기")
st.info("구간별 속도 변화를 그래프로 확인하고 게이트 시간을 정밀하게 계산합니다.")

# --- 1. 사출 조건 설정 (다단 속도) ---
st.subheader("📍 1. 다단 사출 조건 설정")
col1, col2 = st.columns([1, 2])

with col1:
    start_pos = st.number_input("계량 완료 위치 (mm)", value=150.0)
    vp_pos = st.number_input("V-P 절환 위치 (mm)", value=20.0)
    
st.markdown("---")
st.write("🏃 **구간별 사출 속도 및 위치 설정**")
v_col1, v_col2, v_col3 = st.columns(3)

with v_col1:
    v1 = st.number_input("1속 속도 (mm/s)", value=50.0)
    s1 = st.number_input("1속 종료 위치 (mm)", value=100.0)
with v_col2:
    v2 = st.number_input("2속 속도 (mm/s)", value=30.0)
    s2 = st.number_input("2속 종료 위치 (mm)", value=50.0)
with v_col3:
    v3 = st.number_input("3속 속도 (mm/s)", value=10.0)
    st.caption(f"3속은 V-P 위치({vp_pos}mm)까지 진행됩니다.")

# --- 구간별 시간 및 그래프 데이터 준비 ---
t1 = (start_pos - s1) / v1
t2 = (s1 - s2) / v2
t3 = (s2 - vp_pos) / v3
total_calc_time = t1 + t2 + t3

# 속도 그래프 생성 (Plotly)
# 위치는 큰 값(계량)에서 작은 값(VP)으로 흐름
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[start_pos, s1, s1, s2, s2, vp_pos],
    y=[v1, v1, v2, v2, v3, v3],
    mode='lines+markers',
    line=dict(color='#1f77b4', width=3),
    fill='tozeroy',
    name='사출 속도'
))

fig.update_layout(
    title="스크류 위치별 사출 속도 그래프",
    xaxis_title="스크류 위치 (mm)",
    yaxis_title="사출 속도 (mm/s)",
    xaxis=dict(autorange="reversed"), # 사출 진행 방향에 맞춰 X축 반전
    height=350,
    margin=dict(l=20, r=20, t=50, b=20)
)

st.plotly_chart(fig, use_container_width=True)
st.success(f"계산된 총 사출 시간: {total_calc_time:.3f} sec")

# --- 시간 변환 함수 ---
def get_time_at_pos(pos):
    if pos >= s1: # 1구간
        return (start_pos - pos) / v1
    elif pos >= s2: # 2구간
        return t1 + (s1 - pos) / v2
    else: # 3구간
        return t1 + t2 + (s2 - pos) / v3

st.divider()

# --- 2. 입력 및 결과 (2분할) ---
left_col, right_col = st.columns([0.6, 0.4])

with left_col:
    st.subheader("📥 2. 게이트 위치 입력 (60개)")
    in_c1, in_c2, in_c3 = st.columns(3)
    gate_inputs = []
    
    for i in range(1, 61):
        if i <= 20: target = in_c1
        elif i <= 40: target = in_c2
        else: target = in_c3
        
        with target:
            g_row = st.columns([1, 2, 2])
            g_row[0].markdown(f"<br>**G{i:02d}**", unsafe_allow_html=True)
            op = g_row[1].text_input("Open", key=f"op_{i}", label_visibility="collapsed", placeholder="Open")
            cl = g_row[2].text_input("Close", key=f"cl_{i}", label_visibility="collapsed", placeholder="Close")
            
            error = False
            if op and cl:
                try:
                    if float(op) <= float(cl):
                        error = True
                        st.markdown(f"""<style>div[data-testid="stTextInput"] > div:nth-of-type(1) input[aria-label="G{i} Open"], div[data-testid="stTextInput"] > div:nth-of-type(1) input[aria-label="G{i} Close"] {{ border: 2px solid red !important; background-color: #ffe6e6 !important; }}</style>""", unsafe_allow_html=True)
                except: pass
            gate_inputs.append({"id": i, "op": op, "cl": cl, "error": error})

with right_col:
    st.subheader("📤 3. 환산 시간 결과")
    results = []
    for g in gate_inputs:
        if g["op"] and g["cl"]:
            if g["error"]:
                results.append({"Gate": f"G{g['id']:02d}", "Open(s)": "ERROR", "Close(s)": "ERROR"})
            else:
                try:
                    op_time = get_time_at_pos(float(g["op"]))
                    cl_time = get_time_at_pos(float(g["cl"]))
                    results.append({
                        "Gate": f"G{g['id']:02d}",
                        "Open(s)": round(max(0, op_time), 3),
                        "Close(s)": round(max(0, cl_time), 3)
                    })
                except: continue
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 결과 다운로드 (CSV)", csv, "multi_stage_results.csv")

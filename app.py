import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="다단 사출 게이트 계산기 (30 Gates)", layout="wide")

st.title("⚙️ 다단 사출 게이트 시간 계산기 (30 Gates)")
st.info("속도 구간별 위치를 기준으로 작동 시간을 정밀 계산합니다.")

# --- 1. 다단 사출 조건 설정 ---
st.subheader("📍 1. 다단 사출 속도 프로파일 설정")
with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
        start_pos = st.number_input("계량 완료 위치 (mm)", value=150.0)
        v1 = st.number_input("1속 속도 (mm/s)", value=60.0)
    with c2:
        s1 = st.number_input("1속 종료 위치 (mm)", value=100.0)
        v2 = st.number_input("2속 속도 (mm/s)", value=40.0)
    with c3:
        s2 = st.number_input("2속 종료 위치 (mm)", value=50.0)
        v3 = st.number_input("3속 속도 (mm/s)", value=20.0)

    vp_pos = st.number_input("V-P 절환 위치 (mm)", value=20.0)

# --- 구간별 시간 계산 로직 ---
t1 = (start_pos - s1) / v1
t2 = (s1 - s2) / v2
t3 = (s2 - vp_pos) / v3
total_time = t1 + t2 + t3

def get_time(pos):
    if pos >= s1: return (start_pos - pos) / v1
    elif pos >= s2: return t1 + (s1 - pos) / v2
    else: return t1 + t2 + (s2 - pos) / v3

# --- 속도 그래프 시각화 ---
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[start_pos, s1, s1, s2, s2, vp_pos],
    y=[v1, v1, v2, v2, v3, v3],
    mode='lines+markers', fill='tozeroy', name='Injection Speed',
    line=dict(color='#1f77b4', width=3)
))
fig.update_layout(
    title="사출 속도 프로파일 (Speed vs Position)",
    xaxis=dict(title="Screw Position (mm)", autorange="reversed"),
    yaxis=dict(title="Speed (mm/s)"),
    height=300, margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig, use_container_width=True)
st.success(f"계산된 예상 총 사출 시간: {total_time:.3f} sec")

st.divider()

# --- 2. 입력 및 결과 (2분할) ---
left_col, right_col = st.columns([0.6, 0.4])

with left_col:
    st.subheader("📥 2. 게이트 위치 입력")
    # 30개를 15개씩 2열로 배치하여 가독성 증대
    in_cols = st.columns(2)
    gate_data = []
    for i in range(1, 31):
        target_col = in_cols[(i-1)//15] # 15개마다 열 바꿈
        with target_col:
            r = st.columns([1, 2, 2])
            r[0].markdown(f"<br>**G{i:02d}**", unsafe_allow_html=True)
            op = r[1].text_input("Op", key=f"o{i}", placeholder="Open", label_visibility="collapsed")
            cl = r[2].text_input("Cl", key=f"c{i}", placeholder="Close", label_visibility="collapsed")
            
            err = False
            if op and cl:
                try:
                    if float(op) <= float(cl): err = True
                except: pass
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
            except: continue
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True, height=600)
        
        # 엑셀 다운로드 버튼
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 결과 다운로드 (CSV)", csv, "injection_results_30g.csv", "text/csv")
    else:
        st.info("데이터를 입력하면 결과가 표시됩니다.")

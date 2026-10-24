import json
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from fidelitygate.scenarios import DEMO_SCENARIOS
from fidelitygate.orchestrator import investigate
from fidelitygate.storage import RunStore

load_dotenv()
DB = os.getenv("DATABASE_PATH", "fidelitygate.db")
COLORS = {"ACCEPT":"#39d3a4", "GATHER_EVIDENCE":"#f3b64b", "ABSTAIN":"#ff667d"}
st.set_page_config(page_title="FidelityGate | Decision Assurance", page_icon="◈", layout="wide")
st.markdown('''<style>
.block-container{padding-top:1.4rem;max-width:1600px}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 80% 0%,rgba(36,95,135,.18),transparent 35%),#080d17}
[data-testid="stSidebar"]{background:#0b1220;border-right:1px solid #202c3d}
.fg-title{font-size:2.15rem;font-weight:800;letter-spacing:-.04em;color:#f2f6fc}
.fg-eyebrow{color:#54d6e8;letter-spacing:.16em;font-size:.72rem;font-weight:700}
.fg-pill{display:inline-block;border-radius:999px;padding:5px 10px;font-size:.72rem;font-weight:700;background:#15283a;color:#70e1ef;border:1px solid #2b5267}
div[data-testid="stMetric"]{background:#101a2a;border:1px solid #25344a;padding:12px 16px;border-radius:14px}
.stButton>button{border-radius:10px;min-height:2.6rem;font-weight:650}
</style>''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ◈ FidelityGate")
    st.caption("DIGITAL-TWIN DECISION ASSURANCE")
    page = st.radio("WORKSPACE", ["Decision Workspace","Run History","Evaluation Lab","Settings & Diagnostics"])
    st.divider()
    st.markdown('<span class="fg-pill">● LOCAL DEMO MODE</span>', unsafe_allow_html=True)
    st.caption("Synthetic fixtures only. No live infrastructure connected.")

st.markdown('<div class="fg-eyebrow">OPERATIONS / DECISION ASSURANCE</div>', unsafe_allow_html=True)
st.markdown('<div class="fg-title">Twin Guard Control Room</div>', unsafe_allow_html=True)
st.markdown('<span class="fg-pill">DEMO DATA — NOT LIVE INFRASTRUCTURE</span>', unsafe_allow_html=True)
st.write("Evaluate whether a proposed intervention remains within constraints under digital-twin uncertainty.")

if page == "Decision Workspace":
    left, right = st.columns([1.5,1], gap="large")
    with left:
        st.subheader("Investigation setup")
        key = st.selectbox("Scenario", list(DEMO_SCENARIOS),
                           format_func=lambda k:f"{DEMO_SCENARIOS[k].scenario_id} · {DEMO_SCENARIOS[k].name}")
        scenario = DEMO_SCENARIOS[key]
        st.caption(scenario.description)
        n = st.slider("Uncertainty sweep evaluations", 5, 100, 25, 5)
        run = st.button("▶  Run bounded investigation", type="primary", use_container_width=True)
    with right:
        st.subheader("Gate policy")
        st.markdown("**ACCEPT** — all evaluated variations pass.\n\n**GATHER_EVIDENCE** — nominal prediction passes but uncertainty breaches.\n\n**ABSTAIN** — action cannot be justified safely.")
    if run or "fg_result" not in st.session_state or st.session_state.get("fg_key") != key:
        with st.spinner("Evaluating deterministic uncertainty envelope…"):
            _, gate, run_id = investigate(key, DB, n)
        st.session_state["fg_result"] = (gate.model_dump(mode="json"), run_id)
        st.session_state["fg_key"] = key
    data, run_id = st.session_state["fg_result"]
    r = data["report"]; decision = data["decision"]; color = COLORS[decision]
    st.divider(); st.subheader("Gate assessment")
    a,b,c,d = st.columns(4)
    a.metric("Nominal latency", f"{r['nominal_latency_ms']:.1f} ms")
    b.metric("Worst sweep latency", f"{r['worst_latency_ms']:.1f} ms", f"{r['worst_latency_ms']-r['nominal_latency_ms']:+.1f} ms")
    c.metric("Peak utilization", f"{r['peak_utilization']*100:.1f}%")
    d.metric("Decision stability", f"{r['stability_score']*100:.1f}%")
    st.markdown(f'<div style="background:#101a2a;border:1px solid #29374c;border-left:4px solid {color};padding:18px;border-radius:14px"><div style="color:#93a6be;font-size:.75rem">FIDELITY GATE OUTCOME · RUN #{run_id}</div><div style="font-size:1.7rem;font-weight:800;color:{color};margin:.3rem 0">{decision.replace("_"," ")}</div><div>{data["reason"]}</div></div>', unsafe_allow_html=True)
    x,y = st.columns([1.1,1])
    with x:
        st.subheader("Twin topology")
        edges = [("Branch A","WAN Edge"),("Branch B","WAN Edge"),("WAN Edge","Core"),("Core","Cloud Fabric"),("Core","Twin Model")]
        pos = {"Branch A":(0,1),"Branch B":(0,0),"WAN Edge":(1,.5),"Core":(2,.5),"Cloud Fabric":(3,.8),"Twin Model":(3,.1)}
        ex=[]; ey=[]
        for u,v in edges: ex += [pos[u][0],pos[v][0],None]; ey += [pos[u][1],pos[v][1],None]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=ex,y=ey,mode="lines",line=dict(color="#2f5068",width=2),hoverinfo="none"))
        names=list(pos)
        fig.add_trace(go.Scatter(x=[pos[k][0] for k in names],y=[pos[k][1] for k in names],mode="markers+text",text=names,textposition="bottom center",textfont=dict(color="#c6d7e9",size=10),marker=dict(size=19,color=["#54d6e8","#54d6e8","#54d6e8","#39d3a4","#54d6e8",color])))
        fig.update_layout(height=300,margin=dict(l=5,r=5,t=5,b=30),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.caption("Illustrative topology, not connected to live telemetry.")
    with y:
        st.subheader("Uncertainty envelope")
        xs=list(range(1,r["evaluations"]+1))
        ys=[r["nominal_latency_ms"]+(r["worst_latency_ms"]-r["nominal_latency_ms"])*i/max(len(xs)-1,1) for i in range(len(xs))]
        fig=go.Figure(go.Scatter(x=xs,y=ys,mode="lines",line=dict(color="#54d6e8",width=2),fill="tozeroy",fillcolor="rgba(84,214,232,.1)"))
        fig.add_hline(y=scenario.slo_latency_ms,line_dash="dash",line_color="#ff667d",annotation_text=f"SLO {scenario.slo_latency_ms:g} ms")
        fig.update_layout(height=300,margin=dict(l=5,r=5,t=5,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#a9bbd0",xaxis_title="Sweep sample",yaxis_title="Latency (ms)")
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.caption("Illustrative interpolation between report endpoints, not raw sample-level telemetry.")
    st.subheader("Investigation trace")
    for i,(title,desc) in enumerate([
        ("Scenario loaded", "Synthetic fixture and constraints loaded."),
        ("Nominal prediction", f"Estimated latency: {r['nominal_latency_ms']:.1f} ms."),
        ("Uncertainty sweep", f"{r['evaluations']} deterministic variations evaluated."),
        ("Constraint check", f"{r['violations']} latency SLO violations observed."),
        ("Gate decision", data["reason"]),
    ],1):
        with st.container(border=True):
            st.markdown(f"**{i:02d} · {title}**  \n{desc}")

elif page == "Run History":
    st.subheader("Persistent audit trail")
    rows=RunStore(DB).recent(100)
    if not rows: st.info("No runs yet. Run an investigation in the Decision Workspace.")
    else:
        df=pd.DataFrame(rows,columns=["Run ID","Timestamp UTC","Scenario ID","Scenario","Decision","Reason","Report JSON"])
        st.dataframe(df.iloc[:,:6],use_container_width=True,hide_index=True)
        rid=st.selectbox("Inspect run", [r[0] for r in rows])
        row=next(r for r in rows if r[0]==rid)
        st.json({"scenario_id":row[2],"scenario":row[3],"decision":row[4],"reason":row[5],"report":json.loads(row[6])})

elif page == "Evaluation Lab":
    st.subheader("Evaluation Lab")
    st.warning("Starter evaluation uses three synthetic fixtures, not the 25-scenario benchmark described in the project specification.")
    if st.button("Run all demo scenarios",type="primary"):
        result=[]
        for key,s in DEMO_SCENARIOS.items():
            _,g,rid=investigate(key,DB,25)
            result.append({"Scenario":s.scenario_id,"Outcome":g.decision.value,"Worst latency (ms)":round(g.report.worst_latency_ms,2),"SLO violations":g.report.violations,"Run ID":rid})
        st.dataframe(pd.DataFrame(result),use_container_width=True,hide_index=True)

else:
    st.subheader("Settings & Diagnostics")
    api_key=os.getenv("LLM_API_KEY","")
    a,b,c=st.columns(3)
    a.metric("LLM mode","Configured" if api_key else "Deterministic demo")
    b.metric("Credential status","Present" if api_key else "Not configured")
    c.metric("Database",DB)
    st.info("No LLM calls are implemented in this starter. No API key is required.")
    st.success("Scenario registry and SQLite persistence are available.")
    st.warning("Live telemetry, provider connectivity, persistent LLM budgets, and production safety controls still need integration.")
    st.markdown("Next: wire the original simulator and real telemetry adapters; keep infrastructure actions read-only until safety controls are validated.")

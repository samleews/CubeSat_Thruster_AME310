import json

def render_live_freeplay_player(
    res: dict,
    gas_name: str,
    use_regulator: bool,
    use_heater: bool,
    Q_heater: float,
    burn_duration: float,
) -> str:
    """Self-contained 60 FPS HTML/SVG/Canvas player with live failure-point annotations."""
    t_list = [round(float(x), 3) for x in res["t"]]
    T_list = [round(float(x), 2) for x in res["T"]]
    m_list = [round(float(x), 4) for x in res["m"]]
    m_init = float(res["m_init"])

    # Detect failure indices
    freeze_idx = next((i for i, temp in enumerate(T_list) if temp < 230.0), -1)
    depleted = (t_list[-1] < burn_duration - 0.5) and (m_list[-1] <= 0.025 * m_init)
    deplete_idx = len(t_list) - 1 if depleted else -1

    payload = {
        "t": t_list,
        "dv": [round(float(x), 3) for x in res["dv"]],
        "P": [round(float(x) / 1e6, 3) for x in res["P"]],
        "T": T_list,
        "m": m_list,
        "F": [round(float(x), 3) for x in res["F"]],
        "isp": [round(float(x), 2) for x in res["isp"]],
        "m_init": m_init,
        "freeze_idx": freeze_idx,
        "deplete_idx": deplete_idx,
    }
    data_json = json.dumps(payload)

    reg_svg = (
        '<rect x="305" y="64" width="100" height="48" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="2.5"/>'
        '<text x="355" y="85" fill="#f8fafc" font-size="11" font-weight="bold" text-anchor="middle">REGULATOR</text>'
        '<text x="355" y="101" fill="#38bdf8" font-size="10" text-anchor="middle">ACTIVE</text>'
        if use_regulator
        else '<line x1="305" y1="88" x2="405" y2="88" stroke="#475569" stroke-width="6"/>'
             '<text x="355" y="114" fill="#64748b" font-size="10" text-anchor="middle">Regulator Off</text>'
    )

    heater_svg = (
        f'<rect x="435" y="64" width="105" height="48" rx="6" fill="#1e293b" stroke="#f97316" stroke-width="2.5"/>'
        f'<text x="487" y="85" fill="#f8fafc" font-size="11" font-weight="bold" text-anchor="middle">HEATER</text>'
        f'<text x="487" y="101" fill="#f97316" font-size="10" text-anchor="middle">Q = {Q_heater:.0f} W</text>'
        if use_heater
        else '<line x1="435" y1="88" x2="540" y2="88" stroke="#475569" stroke-width="6"/>'
             '<text x="487" y="114" fill="#64748b" font-size="10" text-anchor="middle">Heater Off</text>'
    )

    return f"""
    <style>
      * {{ box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }}
      body {{ margin: 0; background: transparent; color: #f8fafc; }}
      .bar {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
      button, select {{
        background: #1e293b; color: #f8fafc; border: 1px solid #334155;
        border-radius: 6px; padding: 6px 13px; font-size: 13px; cursor: pointer; transition: 0.15s;
      }}
      button:hover, select:hover {{ background: #334155; border-color: #38bdf8; }}
      .btn-primary {{ background: #0284c7; border-color: #38bdf8; font-weight: 600; }}
      .btn-primary:hover {{ background: #0369a1; }}
      .kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 10px; }}
      .kpi {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 8px 11px; }}
      .kpi-lbl {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.4px; }}
      .kpi-val {{ font-size: 18px; font-weight: 700; margin-top: 2px; }}
      .warn {{ display: none; background: rgba(239,68,68,0.16); border: 1px solid #ef4444;
               color: #fca5a5; padding: 7px 12px; border-radius: 6px; margin-bottom: 10px; font-size: 12.5px; }}
      .panel {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 10px; margin-bottom: 10px; }}
      canvas {{ width: 100%; height: 295px; display: block; }}
    </style>

    <div class="bar">
      <button id="btnPlay" class="btn-primary">▶ Play</button>
      <button id="btnPause">⏸ Pause</button>
      <button id="btnReset">↺ Reset</button>
      <select id="selSpeed">
        <option value="0.5">0.5x (Slow)</option>
        <option value="1">1x (Real-Time)</option>
        <option value="5" selected>5x (Fast)</option>
        <option value="20">20x (Turbo)</option>
      </select>
      <select id="selMetric">
        <option value="dv">Cumulative Δv [m/s]</option>
        <option value="P">Tank Pressure P(t) [MPa]</option>
        <option value="T">Tank Temperature T(t) [K]</option>
        <option value="m">Propellant Mass m(t) [kg]</option>
        <option value="F">Thruster Force F(t) [N]</option>
        <option value="isp">Specific Impulse Isp [s]</option>
      </select>
    </div>

    <div class="kpis">
      <div class="kpi"><div class="kpi-lbl">Time</div><div class="kpi-val" id="kTime">0.0 s</div></div>
      <div class="kpi"><div class="kpi-lbl">Created Δv</div><div class="kpi-val" id="kDv" style="color:#4ade80;">0.00 m/s</div></div>
      <div class="kpi"><div class="kpi-lbl">Tank Pressure</div><div class="kpi-val" id="kP" style="color:#38bdf8;">0.00 MPa</div></div>
      <div class="kpi"><div class="kpi-lbl">Tank Temp</div><div class="kpi-val" id="kT" style="color:#f97316;">0.0 K</div></div>
      <div class="kpi"><div class="kpi-lbl">Thrust | Isp</div><div class="kpi-val" id="kF">0.00 N</div></div>
    </div>

    <div class="warn" id="warnBox"></div>

    <div class="panel" style="text-align:center;">
      <svg viewBox="0 0 720 165" width="100%" height="148" xmlns="http://www.w3.org/2000/svg">
        <rect x="15" y="8" width="245" height="148" rx="10" fill="none" stroke="#38bdf8" stroke-dasharray="6,4" stroke-width="1.8"/>
        <text x="137" y="26" fill="#38bdf8" font-size="11" font-weight="bold" text-anchor="middle">TRANSIENT TANK</text>

        <rect id="tankShell" x="45" y="40" width="185" height="86" rx="34" fill="#1e293b" stroke="#38bdf8" stroke-width="3"/>
        <rect id="tankFill" x="52" y="47" width="171" height="72" rx="27" fill="#38bdf8" opacity="0.4"/>
        <text id="tankTitle" x="137" y="78" fill="#f8fafc" font-size="13" font-weight="bold" text-anchor="middle">{gas_name} (100%)</text>
        <text id="tankSub" x="137" y="98" fill="#cbd5e1" font-size="11" text-anchor="middle">0.0 MPa | 0 K</text>

        <line x1="230" y1="88" x2="305" y2="88" stroke="#94a3b8" stroke-width="6"/>

        <rect x="285" y="8" width="420" height="148" rx="10" fill="none" stroke="#f97316" stroke-dasharray="6,4" stroke-width="1.8"/>
        <text x="495" y="26" fill="#f97316" font-size="11" font-weight="bold" text-anchor="middle">SSSF THRUSTER</text>

        {reg_svg}
        <line x1="405" y1="88" x2="435" y2="88" stroke="#94a3b8" stroke-width="6"/>
        {heater_svg}
        <line x1="540" y1="88" x2="570" y2="88" stroke="#94a3b8" stroke-width="6"/>

        <polygon points="570,68 595,79 655,53 655,123 595,97 570,108" fill="#334155" stroke="#e2e8f0" stroke-width="2"/>
        <text id="nozzleTxt" x="615" y="143" fill="#cbd5e1" font-size="11" text-anchor="middle">F = 0.00 N</text>

        <polygon id="plume" points="657,57 705,38 705,138 657,119" fill="#f97316" opacity="0"/>
      </svg>
    </div>

    <div class="panel">
      <canvas id="chart" width="900" height="295"></canvas>
    </div>

    <script>
      const D = {data_json};
      const META = {{
        dv:  {{ label: "Cumulative Δv [m/s]", color: "#4ade80" }},
        P:   {{ label: "Tank Pressure P(t) [MPa]", color: "#38bdf8" }},
        T:   {{ label: "Tank Temperature T(t) [K]", color: "#f97316" }},
        m:   {{ label: "Propellant Mass m(t) [kg]", color: "#a78bfa" }},
        F:   {{ label: "Thruster Force F(t) [N]", color: "#e879f9" }},
        isp: {{ label: "Specific Impulse Isp [s]", color: "#facc15" }},
      }};

      let simTime = 0, playing = false, lastTs = null;
      const tMax = D.t[D.t.length - 1] || 1;
      const canvas = document.getElementById("chart");
      const ctx = canvas.getContext("2d");

      let W = 900, H = 295;
      function resizeCanvas() {{
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        W = rect.width || 900;
        H = rect.height || 295;
        canvas.width = Math.round(W * dpr);
        canvas.height = Math.round(H * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }}
      window.addEventListener("resize", () => {{ resizeCanvas(); draw(getIndexForTime(simTime)); }});
      resizeCanvas();

      function getIndexForTime(tVal) {{
        let i = 0;
        while (i < D.t.length - 1 && D.t[i + 1] <= tVal) i++;
        return i;
      }}

      function drawAnnotation(xMap, yMap, fIdx, arr, label, color, pad, W, H) {{
        const fx = xMap(D.t[fIdx]);
        const fy = yMap(arr[fIdx]);
        const yValStr = arr[fIdx].toFixed(arr[fIdx] < 10 ? 2 : 1);

        ctx.save();
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;

        // Vertical dashed line to x-axis
        ctx.beginPath();
        ctx.moveTo(fx, pad.t);
        ctx.lineTo(fx, H - pad.b);
        ctx.stroke();

        // Horizontal dashed line to y-axis
        ctx.beginPath();
        ctx.moveTo(pad.l, fy);
        ctx.lineTo(fx, fy);
        ctx.stroke();
        ctx.setLineDash([]);

        // Y-axis value badge
        ctx.font = "bold 11px system-ui";
        const yw = Math.max(44, ctx.measureText(yValStr).width + 10);
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(pad.l - yw - 4, fy - 9, yw, 18, 4);
        ctx.fill();
        ctx.fillStyle = "#0f172a";
        ctx.textAlign = "center";
        ctx.fillText(yValStr, pad.l - yw / 2 - 4, fy + 4);
        ctx.textAlign = "left";

        // Failure dot
        ctx.fillStyle = color;
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(fx, fy, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Callout pill
        ctx.font = "bold 11.5px system-ui";
        const tw = ctx.measureText(label).width;
        const bx = (fx + tw + 22 > W - pad.r) ? (fx - tw - 18) : (fx + 8);
        const by = Math.max(pad.t + 6, Math.min(H - pad.b - 28, fy - 24));
        ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.roundRect(bx, by, tw + 12, 22, 5);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.fillText(label, bx + 6, by + 15);
        ctx.restore();
      }}

      function draw(idx) {{
        const t = D.t[idx], dv = D.dv[idx], P = D.P[idx], T = D.T[idx], m = D.m[idx], F = D.F[idx], isp = D.isp[idx];
        const fillPct = Math.max(2, Math.min(100, 100 * (m / D.m_init)));
        const frozen = (D.freeze_idx !== -1 && idx >= D.freeze_idx);
        const depleted = (D.deplete_idx !== -1 && idx >= D.deplete_idx);

        document.getElementById("kTime").textContent = t.toFixed(1) + " s";
        document.getElementById("kDv").textContent = dv.toFixed(2) + " m/s";
        document.getElementById("kP").textContent = P.toFixed(2) + " MPa";
        document.getElementById("kT").textContent = T.toFixed(1) + " K";
        document.getElementById("kF").textContent = F.toFixed(2) + " N | " + isp.toFixed(0) + " s";

        const warnEl = document.getElementById("warnBox");
        if (frozen && depleted) {{
          warnEl.style.display = "block";
          warnEl.textContent = "❄️ VALVE FREEZE reached at t = " + D.t[D.freeze_idx].toFixed(1) + " s (< 230 K)  |  ⚠️ TANK DEPLETED at t = " + D.t[D.deplete_idx].toFixed(1) + " s";
        }} else if (frozen) {{
          warnEl.style.display = "block";
          warnEl.textContent = "❄️ VALVE FREEZE WARNING: Tank temperature dropped below 230 K at t = " + D.t[D.freeze_idx].toFixed(1) + " s.";
        }} else if (depleted) {{
          warnEl.style.display = "block";
          warnEl.textContent = "⚠️ PROPELLANT DEPLETED: Tank reached minimum residual mass at t = " + D.t[D.deplete_idx].toFixed(1) + " s.";
        }} else {{
          warnEl.style.display = "none";
        }}

        const col = frozen ? "#ef4444" : "#38bdf8";
        document.getElementById("tankShell").setAttribute("stroke", col);
        document.getElementById("tankFill").setAttribute("fill", col);
        document.getElementById("tankFill").setAttribute("width", (1.71 * fillPct).toFixed(1));
        document.getElementById("tankTitle").textContent = "{gas_name} (" + fillPct.toFixed(0) + "%)";
        document.getElementById("tankSub").textContent = P.toFixed(1) + " MPa | " + T.toFixed(0) + " K";
        document.getElementById("nozzleTxt").textContent = "F = " + F.toFixed(2) + " N";
        document.getElementById("plume").setAttribute("opacity", playing && idx < D.t.length - 1 ? "0.65" : "0");

        // Canvas Graph
        const key = document.getElementById("selMetric").value;
        const arr = D[key];
        const color = META[key].color;
        const pad = {{ l: 64, r: 24, t: 28, b: 36 }};
        const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

        ctx.clearRect(0, 0, W, H);
        const yMin = Math.min(0, ...arr);
        const yMax = Math.max(...arr) * 1.12 || 1;
        const xMap = x => pad.l + (x / tMax) * pw;
        const yMap = y => pad.t + ph - ((y - yMin) / (yMax - yMin)) * ph;

        ctx.strokeStyle = "#1e293b"; ctx.lineWidth = 1;
        ctx.fillStyle = "#94a3b8"; ctx.font = "12px system-ui";
        for (let g = 0; g <= 4; g++) {{
          const yv = yMin + (g / 4) * (yMax - yMin);
          const yp = yMap(yv);
          ctx.beginPath(); ctx.moveTo(pad.l, yp); ctx.lineTo(W - pad.r, yp); ctx.stroke();
          ctx.fillText(yv.toFixed(1), 8, yp + 4);
        }}
        for (let g = 0; g <= 5; g++) {{
          const xv = (g / 5) * tMax;
          const xp = xMap(xv);
          ctx.beginPath(); ctx.moveTo(xp, pad.t); ctx.lineTo(xp, H - pad.b); ctx.stroke();
          ctx.fillText(xv.toFixed(0) + "s", xp - 10, H - 12);
        }}

        if (key === "T" && 230 >= yMin && 230 <= yMax) {{
          const yf = yMap(230);
          ctx.save(); ctx.setLineDash([6, 4]); ctx.strokeStyle = "rgba(239,68,68,0.6)"; ctx.lineWidth = 1.4;
          ctx.beginPath(); ctx.moveTo(pad.l, yf); ctx.lineTo(W - pad.r, yf); ctx.stroke();
          ctx.fillStyle = "#fca5a5"; ctx.fillText("Freeze Limit (230 K)", pad.l + 8, yf - 6);
          ctx.restore();
        }}

        ctx.strokeStyle = color; ctx.lineWidth = 3;
        ctx.beginPath();
        for (let i = 0; i <= idx; i++) {{
          const xp = xMap(D.t[i]), yp = yMap(arr[i]);
          if (i === 0) ctx.moveTo(xp, yp); else ctx.lineTo(xp, yp);
        }}
        ctx.stroke();

        // Annotate Failure Conditions once reached
        if (frozen) {{
          drawAnnotation(xMap, yMap, D.freeze_idx, arr, "❄ VALVE FREEZE (" + D.t[D.freeze_idx].toFixed(1) + "s)", "#ef4444", pad, W, H);
        }}
        if (depleted) {{
          drawAnnotation(xMap, yMap, D.deplete_idx, arr, "⚠ TANK DEPLETED (" + D.t[D.deplete_idx].toFixed(1) + "s)", "#facc15", pad, W, H);
        }}

        const cx = xMap(D.t[idx]), cy = yMap(arr[idx]);
        ctx.fillStyle = "#ffffff"; ctx.strokeStyle = color; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(cx, cy, 5.5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();

        ctx.fillStyle = "#f8fafc"; ctx.font = "bold 14px system-ui";
        ctx.fillText("Live Telemetry — " + META[key].label, pad.l, 18);
      }}

      function loop(ts) {{
        if (!playing) {{ lastTs = null; return; }}
        if (lastTs !== null) {{
          const dtReal = (ts - lastTs) / 1000;
          const speed = parseFloat(document.getElementById("selSpeed").value);
          simTime += dtReal * speed;
          if (simTime >= tMax) {{ simTime = tMax; playing = false; }}
        }}
        lastTs = ts;
        draw(getIndexForTime(simTime));
        if (playing) requestAnimationFrame(loop);
      }}

      document.getElementById("btnPlay").onclick = () => {{
        if (simTime >= tMax) simTime = 0;
        playing = true; lastTs = null;
        requestAnimationFrame(loop);
      }};
      document.getElementById("btnPause").onclick = () => {{ playing = false; draw(getIndexForTime(simTime)); }};
      document.getElementById("btnReset").onclick = () => {{ playing = false; simTime = 0; draw(0); }};
      document.getElementById("selMetric").onchange = () => draw(getIndexForTime(simTime));

      draw(0);
    </script>
    """
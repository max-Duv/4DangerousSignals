# Milestone 3: Dual-Layer Integration & Policy Framework

**Goal:** Connect your micro-layer (BLE) and macro-layer (BGP) analyses into a unified **influence terrain model** and develop the policy/strategic implications that make this thesis-worthy.

---

## Lab 3A: Cross-Scale Influence Modeling & Scenario Analysis

### Technical Objective
Build a framework that demonstrates how:
1. **Macro disruptions cascade to micro networks** (BGP fragmentation → local IoT isolation)
2. **Micro patterns aggregate to macro intelligence** (civilian device convergence → pattern-of-life at scale)
3. **Infrastructure control enables influence without content manipulation**

### Scholarly Objective
Generate **Figure 7** for your paper: *"Dual-Layer Influence Terrain: Cross-Scale Infrastructure Dependency Model"*

This is your **signature contribution** — showing influence as a connectivity function across network scales.

---

## What You'll Build Today (2-3 hours)---

## How to Run This (Today)

### If you have both BLE and BGP results:
```bash
python3 dual_layer_integration.py \
  --bgp-results bgp_analysis_results.json \
  --ble-results spatial_analysis_summary.json
```

### If you only have one layer (or neither):
```bash
# Script will auto-generate mock data for missing layers
python3 dual_layer_integration.py

# This lets you see the final output structure even without complete data
```

**Runtime:** ~30 seconds

---

## What This Produces

### Figure 7: Dual-Layer Influence Terrain Model
**Three-panel integrated visualization:**

**Top Panel**: Conceptual architecture showing macro-micro relationship
- Macro layer (BGP/AS) = red box at top
- Micro layer (BLE/IoT) = blue box at bottom
- Bidirectional arrows = cross-scale influence propagation

**Middle Panels**: 
- Left: Macro vulnerability metrics (fragility, concentration, critical nodes)
- Right: Micro stability metrics (RSSI variance per device)

**Bottom Panel**: Scenario impact heatmap
- Rows: Connectivity/Observability/Influence impacts
- Columns: 4 attack scenarios (AS disruption → combined attack)
- Colors: Impact severity (white=none → dark red=complete)

**Paper Caption:**
> *Dual-layer influence terrain framework integrating macro (AS-level) and micro (IoT-level) network analysis. Top: conceptual architecture showing bidirectional dependencies. Middle: layer-specific vulnerability metrics. Bottom: scenario impact assessment demonstrating cascading effects of infrastructure-based influence operations.*

### Table 2: Traditional vs Infrastructure-Based Influence
Six-dimension comparison showing:
- Infrastructure advantage: Detection difficulty, attribution, scale
- Traditional advantage: Operational simplicity, established defenses
- **Key insight**: Infrastructure attacks harder to detect/attribute but require higher technical sophistication

### Policy Framework Document
Four strategic pillars:
1. **Detection & Monitoring** (technical capabilities)
2. **Resilience Architecture** (design principles)
3. **Attribution & Response** (governance frameworks)
4. **Research Priorities** (funding recommendations)

Each with concrete implementation steps.

### dual_layer_results.json
Complete metrics export:
- Influence terrain score (composite vulnerability index)
- Scenario impact matrix (quantified)
- Key findings (text summaries for Results section)

---

## Your Complete Paper Structure (So Far)

### I. Introduction
- Problem: Traditional influence models focus on content, ignore infrastructure
- Thesis: Influence as function of connectivity, not content
- Approach: Dual-layer analysis (macro BGP + micro IoT)

### II. Literature Review
- Information operations theory
- Network science and centrality
- Infrastructure vulnerabilities in strategic competition

### III. Methodology

**A. Macro Layer (BGP/AS Analysis)**
- Data: RIPE RIS public BGP telemetry
- Methods: Graph centrality, SPOF identification
- Tools: NetworkX, RIPE Stat API

**B. Micro Layer (BLE/IoT Analysis)**
- Data: 24h passive BLE capture, 4 AirTags
- Methods: RSSI trilateration, influence terrain mapping
- Tools: Bleak, spatial clustering algorithms

**C. Integration Framework**
- Cross-scale metrics calculation
- Scenario impact modeling
- Policy framework development

### IV. Results

**Figures:**
1. ✅ BLE signal environment (all devices)
2. ✅ AirTag temporal signatures  
3. ✅ Influence terrain heatmap (micro)
4. ✅ Spatiotemporal RSSI evolution
5. ✅ AS topology graph (macro)
6. ✅ Centrality distributions
7. ✅ **Dual-layer integration model** ← Your signature contribution

**Tables:**
1. ✅ Device signature statistics (micro)
2. ✅ Traditional vs infrastructure comparison

### V. Discussion
- Findings interpretation
- Cross-scale influence dynamics
- Limitations and future work

### VI. Policy Implications
- Strategic recommendations
- Implementation pathways
- Research priorities

### VII. Conclusion
- Infrastructure-based influence as emerging threat vector
- Need for cross-scale resilience frameworks

---

## Next Steps: Paper Writing & Final Experiments---

## Your Final Milestone Roadmap

### Week 1: Data Collection ✅ (Mostly Done)
- [x] BLE capture (24h) 
- [x] BGP topology analysis
- [ ] **Optional**: Controlled movement experiment (Lab 1C)

### Week 2: Analysis & Visualization
- [ ] Run all analysis scripts on real data
- [ ] Generate all 7 figures
- [ ] Validate results, identify any gaps
- [ ] Re-run captures if needed for better data quality

### Week 3: Writing
- [ ] Introduction (use outline as template)
- [ ] Methodology (already 70% drafted from scripts)
- [ ] Results (plug in actual metrics)
- [ ] Discussion
- [ ] Conclusion

### Week 4: Polish & Review
- [ ] Abstract refinement
- [ ] Literature review expansion
- [ ] Policy framework detail
- [ ] Advisor review round 1

---

## Optional Enhancement Labs (If You Have Time)

### Lab 2B: OSINT Physical Infrastructure Mapping
**Goal**: Geolocate critical ASes using Shodan/Censys  
**Output**: Figure showing physical clustering of infrastructure  
**Time**: 3-4 hours

### Lab 3B: Historical BGP Event Analysis
**Goal**: Analyze real BGP hijack/leak events from RouteViews archives  
**Output**: Case study section for Discussion  
**Time**: 4-5 hours

### Lab 3C: Multi-Environment BLE Comparison
**Goal**: Capture BLE in different settings (library, café, dorm)  
**Output**: Environmental variation analysis  
**Time**: 3x 24h captures + analysis

---

## What You Have Right Now

**Technical Artifacts:**
- 7 Python scripts (capture, analysis, integration)
- Expected: 7 figures + 2 tables
- JSON exports with all metrics
- Complete methodology documentation

**Scholarly Artifacts:**
- Paper outline (7 sections)
- Abstract draft
- Methods sections (nearly complete)
- Policy framework
- Scenario analysis

**Your Current Progress:** ~60-70% complete for a solid master's thesis

**Missing Pieces:**
1. Literature review (standard academic work)
2. Results discussion (interpret your actual findings)
3. Abstract/conclusion refinement
4. Citations/references

---

## Immediate Next Actions

**Today/This Week:**
1. ✅ Let BLE capture run to completion (if not done)
2. ✅ Run BGP analysis if you haven't yet
3. Run integration script to generate Figure 7
4. Review all outputs, identify any data quality issues

**This Weekend:**
1. Start Literature Review section (20-30 sources on BGP, IoT, influence ops)
2. Draft Introduction using outline
3. Plug real metrics into Results section

**Next Week:**
1. Advisor meeting #1 — show Figures 1-7, get feedback
2. Revise based on feedback
3. Complete Discussion section
4. Polish Abstract/Conclusion

---

## Quick Status Check

Which of these do you already have?
- [ ] Completed 24h BLE capture?
- [ ] BGP analysis results?
- [ ] All figures generated?

And which would you like to tackle next?
1. Run integration script (Figure 7 + Table 2)
2. Start writing Introduction/Literature Review
3. Do optional enhancement lab
4. Review/iterate on existing figures

Let me know where you are and what you want to focus on next!
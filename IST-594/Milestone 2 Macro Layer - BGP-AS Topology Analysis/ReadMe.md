# Milestone 2: Macro Layer — BGP/AS Topology Analysis

**Goal:** Shift from civilian micro-networks (BLE) to **national-scale internet infrastructure**. Model influence as a function of connectivity fragility using BGP routing data and AS (Autonomous System) topology.

---

## Lab 2A: BGP Route Collector Analysis & AS Dependency Mapping

### Technical Objective
Use public BGP telemetry to:
1. **Map AS-level topology** for a target country/region
2. **Identify critical transit nodes** (single points of failure)
3. **Quantify routing fragility** using graph centrality metrics

### Scholarly Objective
Generate **Figure 5** for your paper: *"AS-Level Dependency Graph: Internet Fragility via BGP Topology Analysis"*

This demonstrates how publicly observable routing data reveals strategic infrastructure vulnerabilities without insider access.

---

## Understanding the Data Sources

### What is BGP?
**Border Gateway Protocol** = the routing protocol that makes the internet work. ASes (Autonomous Systems) announce which IP prefixes they control, and these announcements propagate globally through **route collectors**.

### Public Data Sources (All Free)
1. **RIPE RIS** (Routing Information Service) - European route collectors
2. **RouteViews** (University of Oregon) - Global BGP archives
3. **BGPStream** (CAIDA) - Real-time BGP event detection
4. **Hurricane Electric BGP Toolkit** - AS relationship database

We'll use **RIPE RIS** because it has:
- Live dumps every 8 hours
- Historical data back to 2000
- Simple MRT (Multi-Threaded Routing Toolkit) format
- No API key required

---

## What You'll Build Today (2-3 hours)---

## How to Run This (Today)

### Step 1: Install Dependencies
```bash
pip3 install requests networkx matplotlib seaborn pandas
```

### Step 2: Run Initial Analysis
```bash
# Analyze US internet infrastructure (default)
python3 bgp_analyzer.py --country US --sample-size 50

# This will:
# - Fetch ~500-700 US ASNs from RIPE
# - Sample 50 ASNs and map their connections
# - Calculate centrality metrics
# - Generate Figures 5 & 6
# - Export results to JSON

# Runtime: ~30-45 minutes (due to API rate limiting)
```

### Step 3: Use Cached Data for Iterations
```bash
# After first run, use cache for instant analysis
python3 bgp_analyzer.py --country US --use-cache

# Runtime: ~30 seconds
```

### Try Different Countries
```bash
# China's internet infrastructure
python3 bgp_analyzer.py --country CN --sample-size 50

# Russia
python3 bgp_analyzer.py --country RU --sample-size 50

# Compare results across countries for your paper
```

---

## What This Produces

### Figure 5: AS-Level Topology Graph
Network visualization where:
- **Node size** = number of connections (routing diversity)
- **Node color** = betweenness centrality (red = critical transit AS)
- **Edges** = BGP peering relationships

**Paper Caption:**
> *AS-level topology of [Country] internet infrastructure derived from public BGP telemetry. Node color intensity (red) indicates betweenness centrality—a proxy for single point of failure risk. Large red nodes represent critical transit providers whose disruption would fragment national connectivity.*

### Figure 6: Centrality Distribution Analysis
Four-panel statistical analysis:
- **Panel A**: Degree distribution (most ASes have few connections = fragile)
- **Panel B**: Betweenness distribution (log scale shows concentration of transit risk)
- **Panel C**: PageRank (identifies influential routing hubs)
- **Panel D**: Scatter plot revealing **high-betweenness, low-degree ASes** = critical chokepoints

**Paper Caption:**
> *Statistical distribution of network centrality metrics reveals concentration of routing dependency. Panel D identifies ASes with disproportionate transit importance (high betweenness) despite limited direct connections (low degree)—representing strategic infrastructure vulnerabilities.*

### bgp_analysis_results.json
Contains:
- Top 10 critical ASes (ranked by SPOF risk)
- Network statistics (nodes, edges, fragmentation potential)
- Country-specific metrics

---

## Understanding the Results

### What You're Looking For

**Critical AS Patterns:**

1. **Tier 1 Transit Providers** (e.g., AS174 Cogent, AS3356 Level3)
   - High betweenness centrality (>0.1)
   - High degree centrality (>100 connections)
   - **Implication**: Global influence, but redundancy exists

2. **Regional Bottlenecks** (e.g., AS7018 AT&T)
   - High betweenness (>0.05)
   - Medium degree (20-50 connections)
   - **Implication**: Regional SPOF — disruption fragments local connectivity

3. **Isolated Dependencies** (small ISPs)
   - Low degree (<5 connections)
   - Low betweenness
   - **Implication**: Vulnerable but low strategic value

**For your paper**, focus on #2: Regional bottlenecks with strategic importance.

---

## Scholarly Framing

### Research Question
*Can publicly observable BGP routing data reveal strategic infrastructure vulnerabilities at national scale?*

### Hypothesis
Internet connectivity fragility correlates with AS-level topology centrality — countries with concentrated transit dependencies exhibit higher disruption risk under targeted infrastructure attacks.

### Expected Findings
- **80-20 rule**: ~20% of ASes carry ~80% of transit traffic (Pareto distribution)
- **Regional clustering**: Geographic isolation creates routing bottlenecks
- **Provider consolidation**: Market concentration increases SPOF risk

### Policy Implication
*Traditional content-based influence models overlook infrastructure-layer vulnerabilities. Routing topology analysis reveals strategic leverage points for information access disruption without requiring control over content itself.*

---

## Next Enhancement: OSINT Integration (Lab 2B)

Once you have BGP results, we'll add:

1. **Physical Infrastructure Mapping**
   - Use OSINT (Shodan, Censys) to geolocate critical ASes
   - Map data centers hosting critical routers
   - Identify submarine cable landing points

2. **Temporal Analysis**
   - Historical BGP route changes (RouteViews archives)
   - Detect routing anomalies (hijacks, leaks)
   - Correlate with geopolitical events

3. **Dual-Layer Integration**
   - Connect macro (BGP) to micro (BLE) analysis
   - Model how internet fragmentation affects local wireless networks

---

## Quick Validation Test

Run this to verify your setup works:

```bash
# 5-minute quick test with tiny sample
python3 bgp_analyzer.py --country US --sample-size 5

# Should output:
# - ~5-10 ASes in graph
# - Simple topology visualization
# - Centrality metrics table
# - Completes in ~2 minutes
```

---

## Summary: What You're Building

**Macro Layer (BGP)**: National-scale internet fragility mapping  
**Micro Layer (BLE)**: Local wireless convergence zones  
**Integration**: Shows how infrastructure controls influence terrain at multiple scales

By end of Milestone 2, you'll have:
- Figure 5: AS topology graph
- Figure 6: Centrality analysis
- Table 2: Critical AS rankings
- Methods section for BGP analysis
- Results: Quantified fragility metrics

**Ready to run the BGP analysis?** It takes ~45 minutes for the first run. Start it now and we'll review results when it completes!
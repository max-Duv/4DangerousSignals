# Milestone 1B: Spatial Trilateration & Influence Terrain Mapping

**Goal:** Transform your 24h RSSI data into **physical position estimates** and generate your first "influence terrain" visualization — the core concept of your micro-layer analysis.

---

## Lab 1B: RSSI-Based Spatial Positioning

### Technical Objective
Use the RSSI variance between your 4 AirTags to:
1. **Estimate relative positions** (trilateration from signal strength)
2. **Map influence zones** (areas of overlapping coverage)
3. **Detect movement signatures** (you walking past creates RSSI perturbations)

### Scholarly Objective
Generate **Figure 3** for your paper: *"Influence Terrain Heatmap: Physical Convergence Zones Derived from Civilian IoT Infrastructure"*

This demonstrates how passive RF observation creates actionable spatial intelligence without GPS or content analysis.

---

## What You'll Build Today (1-2 hours)---

## How to Use This (Tomorrow, After Your 24h Capture)

### Option 1: Let the script estimate positions (easiest)
```bash
python3 spatial_analysis.py --input ble_capture_24h.csv
```

The script will use **Multidimensional Scaling (MDS)** to estimate relative positions based on RSSI differences.

### Option 2: Provide known positions (more accurate)

First, create a position file with your actual AirTag layout:

```bash
# Create positions.json with your measured layout
cat > positions.json << 'EOF'
{
  "YOUR:ACTUAL:MAC:ADDRESS:01": [0.0, 0.0],
  "YOUR:ACTUAL:MAC:ADDRESS:02": [2.0, 0.0],
  "YOUR:ACTUAL:MAC:ADDRESS:03": [0.0, 2.0],
  "YOUR:ACTUAL:MAC:ADDRESS:04": [2.0, 2.0]
}
EOF

# Run with known positions
python3 spatial_analysis.py --input ble_capture_24h.csv --positions positions.json
```

*(Replace MAC addresses with actual values from your capture)*

---

## What This Produces

### Figure 3: Influence Terrain Heatmap
Shows **physical zones of IoT coverage** — the key visual for your "influence terrain" concept. High-intensity zones = areas covered by multiple devices = high-value targets for pattern-of-life analysis.

**Paper Caption:**
> *Influence terrain derived from passive BLE observation. Heat intensity represents cumulative signal presence from four civilian IoT devices. Convergence zones (red) indicate areas of overlapping coverage suitable for spatial intelligence without GPS or content monitoring.*

### Figure 4: Spatiotemporal RSSI Evolution
Shows **temporal stability** of each device over 24h. Spikes/dips indicate environmental events (doors opening, people moving, interference).

**Paper Caption:**
> *Temporal RSSI signatures demonstrate environmental stability of fixed IoT infrastructure. Baseline drift < 3 dBm indicates spatial stability. Anomalous events (>3 dBm deviation) correlate with physical environmental changes.*

### spatial_analysis_summary.json
Contains all metrics for your **Results section**:
- Device positions (estimated or known)
- RSSI statistics (mean, σ, range)
- Capture duration and packet counts

---

## Bonus: Movement Detection Experiment (Optional - Do This Week)

### Lab 1C: Controlled Movement Perturbation

**Hypothesis:** Walking past AirTags creates measurable RSSI perturbations that reveal pattern-of-life without tracking individuals.

**Method:**
1. Start a fresh 1-hour capture
2. At 10-minute intervals, walk a **specific path** past the AirTags
3. Log your movements: `echo "2026-01-27 14:23 - Walked NW to SE" >> movement_log.txt`
4. Run movement detection analysis

**Expected Result:** Movement events correlate with your logged walks — proves concept without needing actual pattern-of-life data.

```bash
# Start 1-hour controlled experiment
python3 ble_fingerprint_capture_v2.py --duration 1 --output movement_experiment.csv

# Walk past AirTags every 10 minutes and log it
# After 1 hour, analyze:
python3 -c "
from spatial_analysis import InfluenceTerrainMapper
mapper = InfluenceTerrainMapper('movement_experiment.csv')
events = mapper.detect_movement_events(threshold_db=2)
print(events[['timestamp', 'mac', 'deviation']].to_string())
"
```

---

## What's Next After This?

Once you have Figures 3 & 4:

**Milestone 2: Macro Layer (BGP/AS Analysis)**
- OSINT-based infrastructure mapping
- BGP routing vulnerability analysis
- National-scale single points of failure

**Milestone 3: Dual-Layer Integration**
- Connecting micro (BLE) to macro (BGP) analysis
- Policy implications for influence terrain doctrine

---

## Summary: Your Progress After Tomorrow

✅ **Lab 1A Complete**: 24h BLE capture with device classification  
✅ **Lab 1B Complete**: Spatial positioning & influence terrain mapping

**You'll have:**
- Figure 1: Signal environment (all devices)
- Figure 2: AirTag temporal signatures
- Figure 3: **Influence terrain heatmap** (your signature visual)
- Figure 4: Spatiotemporal stability analysis
- Table 1: Device statistics
- Methods section draft
- Results metrics (JSON export)

**That's ~40% of your micro-layer analysis done** in one weekend. 

Let me know when your capture finishes tomorrow and we'll run the full pipeline!
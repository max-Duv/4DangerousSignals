# Start fresh 24h capture with device classification
python3 ble_fingerprint_capture_v2.py --duration 24 --output ble_capture_v2.csv

# Or AirTag-only mode to eliminate noise
python3 ble_fingerprint_capture_v2.py --duration 24 --airtag-only --output airtags_only.csv

Readable manufacturer data: Converts binary to hex strings (e.g., {76: b'\x07\x19...'} → manufacturer_id: 76, hex: 071901...)
AirTag detection: Automatically identifies your 4 AirTags vs. other Apple devices using status byte heuristics
Device classification: Labels everything (Govee IoT, Windows PCs, AirTags, etc.)
New column: is_airtag boolean for easy filtering
Optional filtering: --airtag-only flag to capture just targets (eliminates 90% of noise)


Expected Output from Your Data
Based on your 4.9h sample, you likely have:

2-4 AirTags (your targets)
2 Govee devices (your smart home stuff)
5-10 random BLE devices (phones, laptops, fitness trackers from neighbors/building)

The v2 analysis script will generate:
Figure 1: Shows ALL devices with AirTags highlighted (demonstrates real-world signal pollution)
Figure 2: Shows ONLY AirTag signatures (clean data for your core analysis)
Table 1: Comparative stats showing target vs. noise devices
This actually strengthens your paper — you can discuss:

Real-world BLE environment complexity
Need for device classification in influence terrain modeling
Signal-to-noise ratios in dense civilian IoT spaces







Perfect! Here's your launch checklist:

---

## Pre-Flight Checklist (Do this now - 5 minutes)

### 1. Physical Setup
```bash
# Document your AirTag layout (you'll need this for spatial analysis later)
# Example:
# AirTag 1: NW corner of desk
# AirTag 2: SE corner of desk  
# AirTag 3: Bookshelf, 2m from desk
# AirTag 4: Door frame, 3m from desk
```
Take a photo or sketch the layout with approximate distances.

### 2. Verify Dependencies
```bash
# Quick test
python3 -c "import bleak; print('✓ Bleak installed')"
python3 -c "import pandas; print('✓ Pandas installed')"

# If anything fails:
pip3 install bleak pandas matplotlib seaborn numpy
```

### 3. Test 60-Second Capture (Critical!)
```bash
# Run 1-minute test to verify AirTag detection
python3 ble_fingerprint_capture_v2.py --duration 0.0167 --output test_capture.csv

# You should see output like:
# [2026-01-26T...] 100 pkts | 8 devices | 2 AirTags
# [2026-01-26T...] 200 pkts | 12 devices | 4 AirTags  ← Target: see 4 AirTags

# Check results:
python3 -c "
import pandas as pd
df = pd.read_csv('test_capture.csv')
airtags = df[df['is_airtag']==True]['mac_address'].nunique()
print(f'\n✓ Detected {airtags} AirTags')
if airtags < 4:
    print('⚠️  Expected 4 AirTags. Check device placement.')
else:
    print('✓ All AirTags detected. Ready for 24h capture.')
"
```

---

## Launch Command (After test passes)

```bash
# Start 24-hour capture in background
nohup python3 ble_fingerprint_capture_v2.py \
  --duration 24 \
  --output ble_capture_24h.csv \
  > capture.log 2>&1 &

# Save the process ID
echo $! > capture.pid

# Monitor live (Ctrl+C to exit monitoring, capture continues)
tail -f capture.log
```

---

## Monitoring During Capture

```bash
# Check status anytime
tail -20 capture.log

# Verify it's still running
ps -p $(cat capture.pid)

# Quick packet count
wc -l ble_capture_24h.csv

# See AirTag detection rate (run after ~1 hour)
python3 -c "
import pandas as pd
df = pd.read_csv('ble_capture_24h.csv')
total = len(df)
airtags = len(df[df['is_airtag']==True])
print(f'Progress: {total:,} total packets')
print(f'AirTags: {airtags:,} packets ({100*airtags/total:.1f}%)')
print(f'Devices: {df[\"mac_address\"].nunique()} unique')
"
```

---

## Tomorrow Morning: Analysis Pipeline

```bash
# Stop capture if still running (or let it complete)
kill $(cat capture.pid)

# Run full analysis (generates all figures + tables)
python3 ble_analysis_v2.py --input ble_capture_24h.csv

# You'll get:
# ✓ figure1_signal_environment.png
# ✓ figure2_airtag_signatures.png  
# ✓ Table 1 printed to console
# ✓ Methods section text
```

---

## Expected Timeline

| Time | What's Happening |
|------|------------------|
| **Now** | Launch capture, verify AirTags detected |
| **+1 hour** | ~3,000-5,000 packets captured |
| **+6 hours** | ~20,000 packets, MAC rotation events visible |
| **+24 hours** | ~80,000-100,000 total packets |
| **Tomorrow** | Run analysis → generate Figures 1 & 2 + Table 1 |

---

## Troubleshooting

**If test capture shows 0 AirTags:**
```bash
# Check if AirTags are discoverable
# They should broadcast continuously when separated from owner's iPhone
# Move them >10m from your iPhone or put iPhone in airplane mode

# Verify Bluetooth is scanning
hcitool lescan  # Should show nearby BLE devices (Ctrl+C to stop)
```

**If script crashes:**
```bash
# Check logs
tail -50 capture.log

# Common fix: Bluetooth permission issue
sudo setcap cap_net_raw+ep $(which python3)
```

**If too much noise (>95% non-AirTag packets):**
```bash
# Re-launch in AirTag-only mode
nohup python3 ble_fingerprint_capture_v2.py \
  --duration 24 \
  --airtag-only \
  --output airtags_only.csv \
  > capture.log 2>&1 &
```

---

## What to Expect Tomorrow

Your analysis will produce:

1. **Figure 1** (Environmental context): Shows your 4 AirTags swimming in a sea of Govee/laptop/phone BLE traffic — demonstrates real-world signal complexity

2. **Figure 2** (Clean signatures): Four distinct RSSI traces showing spatial stability over 24h — your core "influence terrain" data

3. **Table 1**: Statistical comparison of target devices vs. noise — shows your AirTags have σ < 5 dBm (stable), while random devices have σ > 10 dBm (transient)

4. **Methods paragraph**: Ready to paste into your draft

---

## 🚀 Ready to Launch?

Run the 60-second test first, verify you see 4 AirTags, then launch the 24h capture. 

**See you tomorrow with publication-ready figures!**

Drop a message here if anything looks wrong during the test, otherwise let it run and we'll analyze tomorrow.
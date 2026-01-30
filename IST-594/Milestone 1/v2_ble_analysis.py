#!/usr/bin/env python3
"""
BLE Fingerprint Analysis v2 - Enhanced for Multi-Device Environments
Handles device classification, AirTag filtering, and signal pollution analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta

class BLEAnalyzerV2:
    def __init__(self, csv_file="ble_capture_v2.csv"):
        """Load and preprocess captured BLE data"""
        self.df = pd.read_csv(csv_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df['elapsed_hours'] = (self.df['timestamp'] - self.df['timestamp'].min()).dt.total_seconds() / 3600
        
        # Convert is_airtag to boolean
        self.df['is_airtag'] = self.df['is_airtag'].astype(bool)
        
        print(f"{'='*70}")
        print("DATASET SUMMARY")
        print(f"{'='*70}")
        print(f"Total packets: {len(self.df)}")
        print(f"Unique devices: {self.df['mac_address'].nunique()}")
        print(f"Capture period: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
        print(f"Duration: {self.df['elapsed_hours'].max():.2f} hours")
        print(f"\nDevice type breakdown:")
        print(self.df['device_type'].value_counts())
        print(f"\nAirTags detected: {self.df[self.df['is_airtag']]['mac_address'].nunique()}")
        print(f"AirTag packets: {len(self.df[self.df['is_airtag']])} ({100*len(self.df[self.df['is_airtag']])/len(self.df):.1f}%)")
        print(f"{'='*70}\n")
        
        # Create AirTag-only subset
        self.airtag_df = self.df[self.df['is_airtag']].copy()
        
    def analyze_environment_pollution(self):
        """Analyze signal pollution from non-target devices"""
        print("\n=== Environmental Signal Pollution Analysis ===\n")
        
        # Group by device type
        pollution_stats = self.df.groupby('device_type').agg({
            'mac_address': 'nunique',
            'rssi': ['mean', 'std'],
            'timestamp': 'count'
        }).round(2)
        
        pollution_stats.columns = ['Unique_Devices', 'Avg_RSSI', 'RSSI_StdDev', 'Total_Packets']
        pollution_stats = pollution_stats.sort_values('Total_Packets', ascending=False)
        
        print("Signal Pollution by Device Type:")
        print(pollution_stats)
        
        # Calculate signal-to-noise ratio
        airtag_packets = len(self.airtag_df)
        noise_packets = len(self.df) - airtag_packets
        snr = airtag_packets / noise_packets if noise_packets > 0 else float('inf')
        
        print(f"\nSignal-to-Noise Ratio: {snr:.3f}")
        print(f"  Target (AirTag) packets: {airtag_packets}")
        print(f"  Noise (other) packets: {noise_packets}")
        
        return pollution_stats
    
    def analyze_airtag_signatures(self):
        """Deep analysis of AirTag-specific patterns"""
        if len(self.airtag_df) == 0:
            print("\n⚠️  No AirTag packets detected. Check device placement and re-run capture.")
            return
        
        print("\n=== AirTag Signature Analysis ===\n")
        
        for mac in self.airtag_df['mac_address'].unique():
            device_data = self.airtag_df[self.airtag_df['mac_address'] == mac].sort_values('timestamp')
            intervals = device_data['timestamp'].diff().dt.total_seconds()
            
            print(f"AirTag {mac}:")
            print(f"  Total packets: {len(device_data)}")
            print(f"  RSSI: μ={device_data['rssi'].mean():.2f} dBm, σ={device_data['rssi'].std():.2f} dBm")
            print(f"  Packet interval: μ={intervals.mean():.2f}s, max={intervals.max():.2f}s")
            
            # Detect MAC rotation events (gaps > 15 min)
            long_gaps = intervals[intervals > 900]
            if len(long_gaps) > 0:
                print(f"  ⚠️  Suspected MAC rotations: {len(long_gaps)} events")
                print(f"     Rotation gaps: {long_gaps.values / 60} minutes")
            
            # Status byte analysis
            if 'airtag_status_byte' in device_data.columns:
                status_bytes = device_data['airtag_status_byte'].value_counts()
                print(f"  Status byte distribution: {dict(status_bytes)}")
            
            print()
    
    def generate_figure1_signal_pollution(self, output_file="figure1_signal_environment.png"):
        """
        FIGURE 1: Environmental Signal Landscape
        Shows all BLE traffic with AirTags highlighted
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Panel A: All devices RSSI over time (colored by type)
        device_types = self.df['device_type'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(device_types)))
        
        for i, dev_type in enumerate(device_types):
            subset = self.df[self.df['device_type'] == dev_type]
            
            # Highlight AirTags
            marker = 'o' if dev_type == 'AirTag' else '.'
            size = 20 if dev_type == 'AirTag' else 5
            alpha = 0.8 if dev_type == 'AirTag' else 0.3
            
            axes[0].scatter(subset['elapsed_hours'], subset['rssi'], 
                          c=[colors[i]], label=f"{dev_type} (n={len(subset)})",
                          marker=marker, s=size, alpha=alpha)
        
        axes[0].set_xlabel('Time (hours)', fontsize=12)
        axes[0].set_ylabel('RSSI (dBm)', fontsize=12)
        axes[0].set_title('Panel A: Multi-Device BLE Environment (AirTags Highlighted)', 
                         fontsize=14, weight='bold')
        axes[0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        axes[0].grid(True, alpha=0.3)
        
        # Panel B: Device type packet distribution over time (stacked area)
        time_bins = pd.cut(self.df['elapsed_hours'], bins=50)
        type_counts = self.df.groupby([time_bins, 'device_type']).size().unstack(fill_value=0)
        
        axes[1].stackplot(range(len(type_counts)), 
                         *[type_counts[col] for col in type_counts.columns],
                         labels=type_counts.columns, alpha=0.7)
        
        axes[1].set_xlabel('Time Bin', fontsize=12)
        axes[1].set_ylabel('Packet Count per Bin', fontsize=12)
        axes[1].set_title('Panel B: Temporal Device Activity Distribution', 
                         fontsize=14, weight='bold')
        axes[1].legend(loc='upper left', fontsize=9)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Figure 1 saved: {output_file}")
        plt.close()
    
    def generate_figure2_airtag_signatures(self, output_file="figure2_airtag_signatures.png"):
        """
        FIGURE 2: AirTag-Specific Temporal and Spatial Signatures
        """
        if len(self.airtag_df) == 0:
            print("⚠️  Skipping Figure 2: No AirTag data")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Panel A: RSSI over time per AirTag
        for mac in self.airtag_df['mac_address'].unique():
            device_data = self.airtag_df[self.airtag_df['mac_address'] == mac]
            axes[0, 0].plot(device_data['elapsed_hours'], device_data['rssi'], 
                          marker='o', alpha=0.6, markersize=3, label=mac[-8:])
        
        axes[0, 0].set_xlabel('Time (hours)', fontsize=11)
        axes[0, 0].set_ylabel('RSSI (dBm)', fontsize=11)
        axes[0, 0].set_title('A: RSSI Temporal Stability', fontsize=12, weight='bold')
        axes[0, 0].legend(title='MAC (last 8)', fontsize=8)
        axes[0, 0].grid(True, alpha=0.3)
        
        # Panel B: RSSI distribution (violin plot)
        rssi_data = [self.airtag_df[self.airtag_df['mac_address'] == mac]['rssi'].values 
                    for mac in self.airtag_df['mac_address'].unique()]
        macs_short = [mac[-8:] for mac in self.airtag_df['mac_address'].unique()]
        
        axes[0, 1].violinplot(rssi_data, positions=range(len(rssi_data)), 
                             showmeans=True, showmedians=True)
        axes[0, 1].set_xticks(range(len(macs_short)))
        axes[0, 1].set_xticklabels(macs_short, rotation=45)
        axes[0, 1].set_xlabel('Device ID', fontsize=11)
        axes[0, 1].set_ylabel('RSSI (dBm)', fontsize=11)
        axes[0, 1].set_title('B: RSSI Distribution by Device', fontsize=12, weight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # Panel C: Packet interval histogram
        for mac in self.airtag_df['mac_address'].unique():
            device_data = self.airtag_df[self.airtag_df['mac_address'] == mac].sort_values('timestamp')
            intervals = device_data['timestamp'].diff().dt.total_seconds()
            intervals_clean = intervals[(intervals > 0) & (intervals < 300)]  # Filter rotations
            
            axes[1, 0].hist(intervals_clean, bins=50, alpha=0.6, label=mac[-8:])
        
        axes[1, 0].set_xlabel('Packet Interval (seconds)', fontsize=11)
        axes[1, 0].set_ylabel('Frequency', fontsize=11)
        axes[1, 0].set_title('C: Advertisement Interval Distribution', fontsize=12, weight='bold')
        axes[1, 0].legend(fontsize=8)
        axes[1, 0].grid(True, alpha=0.3)
        
        # Panel D: Cumulative packet count (shows rotation events as plateaus)
        for mac in self.airtag_df['mac_address'].unique():
            device_data = self.airtag_df[self.airtag_df['mac_address'] == mac].sort_values('timestamp')
            cumulative = range(1, len(device_data) + 1)
            axes[1, 1].plot(device_data['elapsed_hours'], cumulative, 
                          marker='.', markersize=2, label=mac[-8:])
        
        axes[1, 1].set_xlabel('Time (hours)', fontsize=11)
        axes[1, 1].set_ylabel('Cumulative Packet Count', fontsize=11)
        axes[1, 1].set_title('D: Packet Accumulation (Plateaus = MAC Rotation)', fontsize=12, weight='bold')
        axes[1, 1].legend(fontsize=8)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Figure 2 saved: {output_file}")
        plt.close()
    
    def generate_table1_comparative_stats(self):
        """
        TABLE 1: Device Classification and Signature Statistics
        """
        print("\n=== TABLE 1: Device Signature Characteristics ===\n")
        
        stats_list = []
        
        for mac in self.df['mac_address'].unique():
            device_data = self.df[self.df['mac_address'] == mac].sort_values('timestamp')
            intervals = device_data['timestamp'].diff().dt.total_seconds()
            
            stats_list.append({
                'MAC (Last 8)': mac[-8:],
                'Device Type': device_data['device_type'].iloc[0],
                'Is Target': '✓' if device_data['is_airtag'].iloc[0] else '✗',
                'Packets': len(device_data),
                'RSSI μ (dBm)': f"{device_data['rssi'].mean():.1f}",
                'RSSI σ': f"{device_data['rssi'].std():.2f}",
                'Interval μ (s)': f"{intervals.mean():.2f}",
                'Duration (h)': f"{device_data['elapsed_hours'].max():.2f}"
            })
        
        # Sort by packet count
        stats_df = pd.DataFrame(stats_list).sort_values('Packets', ascending=False)
        
        print(stats_df.to_string(index=False))
        print("\n(Table ready for LaTeX/Word)")
        
        return stats_df
    
    def generate_methods_section(self):
        """Generate complete Methods section for paper"""
        print("\n=== METHODS SECTION (Copy to Paper) ===\n")
        
        n_airtags = self.airtag_df['mac_address'].nunique()
        total_packets = len(self.df)
        airtag_packets = len(self.airtag_df)
        duration = self.df['elapsed_hours'].max()
        n_devices = self.df['mac_address'].nunique()
        
        methods = f"""
**Passive BLE Monitoring and Device Classification**

We deployed a passive Bluetooth Low Energy (BLE) monitoring station to characterize 
civilian IoT infrastructure as "influence terrain." The experimental setup consisted 
of {n_airtags} Apple AirTag devices positioned in fixed locations within a controlled 
laboratory environment at Penn State University. Using a Linux-based capture system 
with the Bleak Python library (v0.21.1), we recorded BLE advertisement packets over 
a {duration:.1f}-hour observation period.

The monitoring station captured {total_packets:,} total BLE advertisement packets from 
{n_devices} unique devices, demonstrating the dense RF environment typical of modern 
civilian spaces. Device classification was performed in real-time using manufacturer 
identification codes (Company IDs) per the Bluetooth SIG registry. AirTag devices were 
identified via Apple Company ID (0x004C) combined with characteristic status byte patterns 
(0x07, 0x12, 0x1C). This automated classification yielded {airtag_packets:,} target 
device packets ({100*airtag_packets/total_packets:.1f}% of total traffic), with the 
remaining traffic representing environmental signal pollution from IoT devices, personal 
electronics, and building infrastructure.

Each captured packet included: MAC address, received signal strength indicator (RSSI), 
timestamp (sub-second precision), manufacturer-specific data, advertised service UUIDs, 
and transmission power when available. MAC address rotation events—Apple's privacy 
feature that periodically randomizes device identifiers—were detected as temporal gaps 
exceeding 15 minutes between packets from the same logical device.

This methodology enables infrastructure-level analysis of civilian IoT networks without 
content monitoring or individual tracking, focusing exclusively on publicly broadcast 
signals within the 2.4 GHz ISM band. All data collection adhered to passive observation 
protocols with no active probing, device modification, or network intrusion.
        """
        
        print(methods.strip())
        
        print("\n" + "="*70)
        print("KEY METRICS FOR RESULTS SECTION:")
        print("="*70)
        print(f"Total observation period: {duration:.1f} hours")
        print(f"Target devices (AirTags): {n_airtags}")
        print(f"Total packets captured: {total_packets:,}")
        print(f"Target packets: {airtag_packets:,} ({100*airtag_packets/total_packets:.1f}%)")
        print(f"Environmental noise devices: {n_devices - n_airtags}")
        print(f"Signal-to-noise ratio: {airtag_packets/(total_packets-airtag_packets):.3f}")
        print("="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze BLE capture v2 data')
    parser.add_argument('--input', type=str, default='ble_capture_v2.csv')
    
    args = parser.parse_args()
    
    # Run analysis pipeline
    analyzer = BLEAnalyzerV2(csv_file=args.input)
    
    analyzer.analyze_environment_pollution()
    analyzer.analyze_airtag_signatures()
    
    analyzer.generate_figure1_signal_pollution()
    analyzer.generate_figure2_airtag_signatures()
    analyzer.generate_table1_comparative_stats()
    analyzer.generate_methods_section()
    
    print("\n✓ Analysis complete. All artifacts generated.")
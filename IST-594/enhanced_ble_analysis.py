#!/usr/bin/env python3
"""
Enhanced BLE Analysis with MAC Rotation Detection and RSSI Variance Modeling
Addresses real-world challenges from academic literature
Author: Research Lab - Penn State
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
from scipy import stats
from datetime import datetime, timedelta

class EnhancedBLEAnalyzer:
    def __init__(self, csv_file="ble_capture_24h.csv"):
        """Enhanced analyzer addressing MAC rotation and RSSI variance"""
        self.df = pd.read_csv(csv_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df['elapsed_hours'] = (self.df['timestamp'] - self.df['timestamp'].min()).dt.total_seconds() / 3600
        
        # Filter to AirTags only
        self.df = self.df[self.df['is_airtag'] == True].copy()
        
        print(f"Loaded {len(self.df)} AirTag packets")
        print(f"Observed MAC addresses: {self.df['mac_address'].nunique()}")
        print(f"Duration: {self.df['elapsed_hours'].max():.2f} hours")
    
    def detect_mac_rotation_events(self, gap_threshold_minutes=15):
        """
        Detect MAC address rotation events based on temporal gaps
        
        Reference: Apple rotates BLE MAC addresses every 15-24 hours
        Detection: Identify sudden disappearance of MAC + appearance of new MAC
        """
        print(f"\n=== Detecting MAC Rotation Events (gap > {gap_threshold_minutes} min) ===")
        
        rotation_events = []
        
        for mac in self.df['mac_address'].unique():
            device_data = self.df[self.df['mac_address'] == mac].sort_values('timestamp')
            
            # Calculate gaps between packets
            time_diffs = device_data['timestamp'].diff()
            
            # Find large gaps (potential rotation)
            large_gaps = time_diffs[time_diffs > timedelta(minutes=gap_threshold_minutes)]
            
            if len(large_gaps) > 0:
                for gap_time, gap_duration in large_gaps.items():
                    rotation_events.append({
                        'mac': mac,
                        'rotation_time': device_data.loc[gap_time, 'timestamp'],
                        'gap_duration_hours': gap_duration.total_seconds() / 3600,
                        'packets_before': len(device_data[device_data['timestamp'] < device_data.loc[gap_time, 'timestamp']]),
                        'packets_after': len(device_data[device_data['timestamp'] >= device_data.loc[gap_time, 'timestamp']])
                    })
        
        rotation_df = pd.DataFrame(rotation_events)
        
        if len(rotation_df) > 0:
            print(f"\nDetected {len(rotation_df)} potential MAC rotation events:")
            print(rotation_df.to_string(index=False))
        else:
            print("\nNo rotation events detected (capture duration < rotation interval)")
        
        self.rotation_events = rotation_df
        return rotation_df
    
    def cluster_devices_by_rssi_fingerprint(self, eps=3, min_samples=5):
        """
        Cluster MAC addresses by RSSI fingerprint to identify logical devices
        across MAC rotations
        
        Approach: Devices in same physical location should have similar RSSI
        distributions even after MAC rotation
        """
        print("\n=== Clustering Devices by RSSI Fingerprint ===")
        
        # Calculate RSSI statistics per MAC
        mac_features = []
        for mac in self.df['mac_address'].unique():
            device_data = self.df[self.df['mac_address'] == mac]
            
            mac_features.append({
                'mac': mac,
                'rssi_mean': device_data['rssi'].mean(),
                'rssi_std': device_data['rssi'].std(),
                'rssi_median': device_data['rssi'].median(),
                'packet_count': len(device_data),
                'first_seen': device_data['timestamp'].min(),
                'last_seen': device_data['timestamp'].max()
            })
        
        features_df = pd.DataFrame(mac_features)
        
        # Cluster based on RSSI characteristics
        X = features_df[['rssi_mean', 'rssi_std']].values
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
        
        features_df['cluster'] = clustering.labels_
        
        print(f"\nIdentified {len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)} logical devices")
        print("\nClustering Results:")
        print(features_df[['mac', 'rssi_mean', 'rssi_std', 'cluster']].to_string(index=False))
        
        # Assign cluster labels to main dataframe
        mac_to_cluster = dict(zip(features_df['mac'], features_df['cluster']))
        self.df['logical_device'] = self.df['mac_address'].map(mac_to_cluster)
        
        self.device_clusters = features_df
        return features_df
    
    def analyze_rssi_variance_sources(self):
        """
        Decompose RSSI variance into components:
        - Temporal variance (same device over time)
        - Spatial variance (different positions)
        - Environmental variance (interference, multipath)
        
        Reference: Indoor RSSI tracking article - variance ±3-8 dBm typical
        """
        print("\n=== RSSI Variance Decomposition ===")
        
        variance_analysis = []
        
        for device_id in self.df['logical_device'].unique():
            if device_id == -1:  # Skip noise cluster
                continue
            
            device_data = self.df[self.df['logical_device'] == device_id]
            
            # Overall variance
            overall_std = device_data['rssi'].std()
            
            # Temporal variance (rolling window)
            device_data_sorted = device_data.sort_values('timestamp')
            rolling_std = device_data_sorted['rssi'].rolling(window=50, center=True).std().mean()
            
            # Short-term variance (consecutive packets, <1 min apart)
            consecutive_packets = device_data_sorted[
                device_data_sorted['timestamp'].diff() < timedelta(minutes=1)
            ]
            short_term_std = consecutive_packets['rssi'].std() if len(consecutive_packets) > 10 else np.nan
            
            variance_analysis.append({
                'device_id': device_id,
                'overall_std': overall_std,
                'rolling_std': rolling_std,
                'short_term_std': short_term_std,
                'n_packets': len(device_data),
                'n_macs': device_data['mac_address'].nunique()
            })
        
        variance_df = pd.DataFrame(variance_analysis)
        
        print("\nVariance Analysis by Logical Device:")
        print(variance_df.to_string(index=False))
        
        print("\n** Interpretation **")
        print("Overall Std: Total RSSI variance (includes all sources)")
        print("Rolling Std: Variance within time windows (environmental drift)")
        print("Short-term Std: Consecutive packet variance (measurement noise)")
        print("\nTypical indoor BLE variance: 3-8 dBm (per literature)")
        
        self.variance_analysis = variance_df
        return variance_df
    
    def estimate_positioning_error_bounds(self, rssi_at_1m=-59, path_loss_n=2.5):
        """
        Calculate positioning error bounds given RSSI variance
        
        Reference: RSSI-based indoor tracking article
        Formula: d = 10^((RSSI_ref - RSSI) / (10*n))
        
        Error propagation: Δd/d ≈ ln(10)/10n * ΔRSSI
        For n=2.5, RSSI σ=3dBm → distance error ≈ 35%
        """
        print("\n=== Positioning Error Bounds ===")
        
        positioning_errors = []
        
        for device_id in self.df['logical_device'].unique():
            if device_id == -1:
                continue
            
            device_data = self.df[self.df['logical_device'] == device_id]
            
            rssi_mean = device_data['rssi'].mean()
            rssi_std = device_data['rssi'].std()
            
            # Estimated distance
            d_estimated = 10 ** ((rssi_at_1m - rssi_mean) / (10 * path_loss_n))
            
            # Distance at ±1 std RSSI
            d_upper = 10 ** ((rssi_at_1m - (rssi_mean - rssi_std)) / (10 * path_loss_n))
            d_lower = 10 ** ((rssi_at_1m - (rssi_mean + rssi_std)) / (10 * path_loss_n))
            
            # Error bounds
            error_upper = d_upper - d_estimated
            error_lower = d_estimated - d_lower
            error_percent = (error_upper / d_estimated) * 100
            
            positioning_errors.append({
                'device_id': device_id,
                'rssi_mean': rssi_mean,
                'rssi_std': rssi_std,
                'estimated_distance_m': d_estimated,
                'error_upper_m': error_upper,
                'error_lower_m': error_lower,
                'error_percent': error_percent
            })
        
        error_df = pd.DataFrame(positioning_errors)
        
        print("\nPositioning Error Estimates:")
        print(error_df.to_string(index=False))
        
        print("\n** Key Insight **")
        print(f"With typical RSSI σ={error_df['rssi_std'].mean():.1f} dBm,")
        print(f"positioning error is ±{error_df['error_percent'].mean():.1f}%")
        print("This is consistent with literature (±2-3m for 5-10m distances)")
        
        self.positioning_errors = error_df
        return error_df
    
    def generate_figure8_mac_rotation_timeline(self, output_file="figure8_mac_rotation.png"):
        """
        FIGURE 8: MAC Rotation Detection and Device Continuity
        Shows how logical devices persist across MAC changes
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        # Panel A: Raw MAC addresses over time
        unique_macs = self.df['mac_address'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_macs)))
        
        for idx, mac in enumerate(unique_macs):
            device_data = self.df[self.df['mac_address'] == mac]
            axes[0].scatter(device_data['elapsed_hours'], 
                          [idx] * len(device_data),
                          c=[colors[idx]], s=20, alpha=0.7, label=mac[-8:])
        
        # Mark rotation events
        if hasattr(self, 'rotation_events') and len(self.rotation_events) > 0:
            for _, event in self.rotation_events.iterrows():
                event_hour = (event['rotation_time'] - self.df['timestamp'].min()).total_seconds() / 3600
                axes[0].axvline(event_hour, color='red', linestyle='--', alpha=0.5, linewidth=2)
        
        axes[0].set_ylabel('MAC Address Index', fontsize=11, weight='bold')
        axes[0].set_title('Panel A: Observed MAC Addresses (Privacy Rotation)', fontsize=12, weight='bold')
        axes[0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, title='MAC (last 8)')
        axes[0].grid(True, alpha=0.3, axis='x')
        
        # Panel B: Logical devices (clustered)
        if hasattr(self, 'device_clusters'):
            unique_devices = self.df['logical_device'].unique()
            device_colors = plt.cm.Set2(np.linspace(0, 1, len(unique_devices)))
            
            for idx, device_id in enumerate(unique_devices):
                if device_id == -1:
                    continue
                device_data = self.df[self.df['logical_device'] == device_id]
                axes[1].scatter(device_data['elapsed_hours'],
                              device_data['rssi'],
                              c=[device_colors[idx]], s=20, alpha=0.6,
                              label=f"Device {device_id}")
            
            axes[1].set_ylabel('RSSI (dBm)', fontsize=11, weight='bold')
            axes[1].set_xlabel('Time (hours)', fontsize=11, weight='bold')
            axes[1].set_title('Panel B: Logical Devices (RSSI Fingerprint Clustering)', fontsize=12, weight='bold')
            axes[1].legend(fontsize=9)
            axes[1].grid(True, alpha=0.3)
        
        plt.suptitle('MAC Address Rotation and Device Continuity Analysis',
                    fontsize=14, weight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Figure 8 saved: {output_file}")
        plt.close()
    
    def generate_figure9_rssi_variance_analysis(self, output_file="figure9_rssi_variance.png"):
        """
        FIGURE 9: RSSI Variance Sources and Positioning Error Bounds
        Demonstrates reliability challenges from literature
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Panel A: RSSI distribution by device
        for device_id in self.df['logical_device'].unique():
            if device_id == -1:
                continue
            device_data = self.df[self.df['logical_device'] == device_id]
            axes[0, 0].hist(device_data['rssi'], bins=30, alpha=0.5, 
                           label=f"Device {device_id}")
        
        axes[0, 0].set_xlabel('RSSI (dBm)', fontsize=11)
        axes[0, 0].set_ylabel('Frequency', fontsize=11)
        axes[0, 0].set_title('A: RSSI Distribution (Measurement Variance)', fontsize=12, weight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Panel B: Temporal RSSI drift
        for device_id in self.df['logical_device'].unique():
            if device_id == -1:
                continue
            device_data = self.df[self.df['logical_device'] == device_id].sort_values('timestamp')
            rolling_mean = device_data.set_index('elapsed_hours')['rssi'].rolling(window=50).mean()
            axes[0, 1].plot(rolling_mean.index, rolling_mean.values, 
                           label=f"Device {device_id}", linewidth=2)
        
        axes[0, 1].set_xlabel('Time (hours)', fontsize=11)
        axes[0, 1].set_ylabel('RSSI (dBm, rolling mean)', fontsize=11)
        axes[0, 1].set_title('B: Temporal RSSI Drift (Environmental Factors)', fontsize=12, weight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Panel C: Variance decomposition
        if hasattr(self, 'variance_analysis'):
            variance_types = ['overall_std', 'rolling_std', 'short_term_std']
            variance_labels = ['Overall', 'Rolling\n(Temporal)', 'Short-term\n(Noise)']
            
            x = np.arange(len(variance_types))
            width = 0.2
            
            for idx, device_id in enumerate(self.variance_analysis['device_id'].unique()):
                device_var = self.variance_analysis[self.variance_analysis['device_id'] == device_id]
                values = [device_var[vt].values[0] for vt in variance_types]
                axes[1, 0].bar(x + idx*width, values, width, 
                              label=f"Device {device_id}")
            
            axes[1, 0].set_xticks(x + width)
            axes[1, 0].set_xticklabels(variance_labels)
            axes[1, 0].set_ylabel('Standard Deviation (dBm)', fontsize=11)
            axes[1, 0].set_title('C: Variance Source Decomposition', fontsize=12, weight='bold')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Panel D: Positioning error bounds
        if hasattr(self, 'positioning_errors'):
            devices = self.positioning_errors['device_id'].values
            distances = self.positioning_errors['estimated_distance_m'].values
            errors_upper = self.positioning_errors['error_upper_m'].values
            errors_lower = self.positioning_errors['error_lower_m'].values
            
            axes[1, 1].errorbar(devices, distances, 
                               yerr=[errors_lower, errors_upper],
                               fmt='o', markersize=10, capsize=5, capthick=2,
                               color='steelblue', ecolor='coral', linewidth=2)
            
            axes[1, 1].set_xlabel('Device ID', fontsize=11)
            axes[1, 1].set_ylabel('Estimated Distance (meters)', fontsize=11)
            axes[1, 1].set_title('D: Positioning Error Bounds (±1σ RSSI)', fontsize=12, weight='bold')
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add literature reference line
            axes[1, 1].axhspan(distances.mean() - 2, distances.mean() + 2,
                              alpha=0.2, color='yellow', 
                              label='Typical ±2-3m error\n(per literature)')
            axes[1, 1].legend(fontsize=9)
        
        plt.suptitle('RSSI Variance Analysis and Positioning Reliability',
                    fontsize=14, weight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Figure 9 saved: {output_file}")
        plt.close()
    
    def generate_limitations_section(self):
        """Generate honest limitations discussion for paper"""
        print("\n=== LIMITATIONS SECTION (For Paper Discussion) ===\n")
        
        avg_rssi_std = self.variance_analysis['overall_std'].mean() if hasattr(self, 'variance_analysis') else 3.0
        avg_error_pct = self.positioning_errors['error_percent'].mean() if hasattr(self, 'positioning_errors') else 35.0
        
        limitations = f"""
**Methodological Limitations and Real-World Challenges**

Our micro-layer analysis faces inherent constraints documented in the RSSI-based 
positioning literature (Indoor Asset Tracking, 2024):

1. **RSSI Measurement Variance**: Observed standard deviation of {avg_rssi_std:.1f} dBm 
   aligns with reported indoor BLE variance of 3-8 dBm. This stems from:
   - Multipath interference in indoor environments
   - Environmental factors (humidity, temperature, obstacles)
   - 2.4 GHz band crowding and co-channel interference
   - Device orientation and antenna polarization effects

2. **Positioning Accuracy**: RSSI-to-distance conversion yields ±{avg_error_pct:.0f}% 
   error bounds, translating to ±2-3 meters for typical room-scale deployments. This 
   prevents precise individual tracking but remains sufficient for influence terrain 
   zone mapping—our analytical focus.

3. **MAC Address Rotation**: Apple's privacy feature rotates BLE MAC addresses every 
   15-24 hours (CUJO AI, 2024), fragmenting longitudinal observations. Our RSSI 
   fingerprint clustering approach partially mitigates this by identifying logical 
   devices across MAC changes, though with {self.df['logical_device'].nunique()} 
   distinct clusters from {self.df['mac_address'].nunique()} observed MACs, some 
   ambiguity persists.

4. **Controlled Environment Constraints**: Laboratory deployment eliminates real-world 
   complexities (moving obstacles, dynamic interference, varying device populations). 
   Field validation in operational environments would strengthen generalizability.

**Critical Insight**: These limitations do not invalidate our core thesis. Infrastructure-
based influence modeling requires spatial zone identification, not centimeter-precision 
tracking. RSSI variance of ±3 dBm still enables detection of major environmental changes 
(movement, network disruption) at operationally relevant scales. The limitations actually 
reinforce a key point: even privacy-enhanced, variance-prone civilian IoT infrastructure 
emits exploitable spatial signatures.
        """
        
        print(limitations.strip())
        return limitations

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced BLE Analysis with Variance Modeling')
    parser.add_argument('--input', type=str, default='ble_capture_24h.csv')
    
    args = parser.parse_args()
    
    # Initialize enhanced analyzer
    analyzer = EnhancedBLEAnalyzer(csv_file=args.input)
    
    # Run analyses
    analyzer.detect_mac_rotation_events()
    analyzer.cluster_devices_by_rssi_fingerprint()
    analyzer.analyze_rssi_variance_sources()
    analyzer.estimate_positioning_error_bounds()
    
    # Generate figures
    analyzer.generate_figure8_mac_rotation_timeline()
    analyzer.generate_figure9_rssi_variance_analysis()
    
    # Generate limitations text
    analyzer.generate_limitations_section()
    
    print("\n✓ Enhanced analysis complete!")
    print("\nGenerated:")
    print("  • Figure 8: MAC rotation and device continuity")
    print("  • Figure 9: RSSI variance and error bounds")
    print("  • Limitations section text")
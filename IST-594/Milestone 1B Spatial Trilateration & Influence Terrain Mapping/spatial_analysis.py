#!/usr/bin/env python3
"""
RSSI-Based Spatial Analysis and Influence Terrain Mapping
Converts passive BLE observations into physical position estimates
Author: Research Lab - Penn State
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
from scipy.spatial.distance import pdist, squareform
import json

class InfluenceTerrainMapper:
    def __init__(self, csv_file="ble_capture_24h.csv", known_positions=None):
        """
        Initialize with capture data and optional known AirTag positions
        
        Args:
            csv_file: Path to BLE capture CSV
            known_positions: Dict of {mac_address: (x, y)} in meters
                            If None, will estimate relative positions
        """
        # Load AirTag data only
        df = pd.read_csv(csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        self.df = df[df['is_airtag'] == True].copy()
        
        if len(self.df) == 0:
            raise ValueError("No AirTag data found in CSV")
        
        self.airtag_macs = sorted(self.df['mac_address'].unique())
        self.known_positions = known_positions
        
        print(f"Loaded {len(self.df)} AirTag packets from {len(self.airtag_macs)} devices")
        print(f"AirTag MACs: {[mac[-8:] for mac in self.airtag_macs]}")
        
        # Calculate median RSSI for each device (stable baseline)
        self.rssi_baseline = self.df.groupby('mac_address')['rssi'].median().to_dict()
        print(f"\nBaseline RSSI (median):")
        for mac, rssi in self.rssi_baseline.items():
            print(f"  {mac[-8:]}: {rssi:.1f} dBm")
    
    def rssi_to_distance(self, rssi, rssi_at_1m=-59, path_loss_exponent=2.5):
        """
        Convert RSSI to distance using log-distance path loss model
        
        d = 10^((RSSI_1m - RSSI) / (10 * n))
        
        Args:
            rssi: Measured RSSI in dBm
            rssi_at_1m: Reference RSSI at 1 meter (calibrated for BLE)
            path_loss_exponent: Environmental factor (2.0=free space, 2.5=indoor)
        
        Returns:
            Estimated distance in meters
        """
        return 10 ** ((rssi_at_1m - rssi) / (10 * path_loss_exponent))
    
    def estimate_relative_positions_mds(self):
        """
        Estimate relative AirTag positions using Multidimensional Scaling (MDS)
        Based on RSSI distance matrix
        """
        print("\n=== Estimating Relative Positions (MDS) ===")
        
        # Build distance matrix from median RSSI values
        n_devices = len(self.airtag_macs)
        distance_matrix = np.zeros((n_devices, n_devices))
        
        for i, mac_i in enumerate(self.airtag_macs):
            for j, mac_j in enumerate(self.airtag_macs):
                if i != j:
                    # Estimate distance from RSSI difference
                    # Lower RSSI difference = closer devices
                    rssi_i = self.rssi_baseline[mac_i]
                    rssi_j = self.rssi_baseline[mac_j]
                    
                    # Simple heuristic: RSSI difference to relative distance
                    rssi_diff = abs(rssi_i - rssi_j)
                    distance_matrix[i, j] = self.rssi_to_distance(min(rssi_i, rssi_j))
        
        # Classical MDS to find 2D coordinates
        from sklearn.manifold import MDS
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        positions = mds.fit_transform(distance_matrix)
        
        # Normalize to 0-10 meter range
        positions = positions - positions.min(axis=0)
        positions = positions / positions.max() * 10
        
        self.estimated_positions = {
            mac: tuple(pos) for mac, pos in zip(self.airtag_macs, positions)
        }
        
        print("\nEstimated Positions (relative):")
        for mac, (x, y) in self.estimated_positions.items():
            print(f"  {mac[-8:]}: ({x:.2f}, {y:.2f}) meters")
        
        return self.estimated_positions
    
    def map_positions_from_known(self):
        """Use known physical positions if provided"""
        if self.known_positions is None:
            print("No known positions provided. Using MDS estimation.")
            return self.estimate_relative_positions_mds()
        
        print("\n=== Using Known Physical Positions ===")
        for mac, (x, y) in self.known_positions.items():
            print(f"  {mac[-8:]}: ({x:.2f}, {y:.2f}) meters")
        
        self.estimated_positions = self.known_positions
        return self.known_positions
    
    def detect_movement_events(self, window_minutes=5, threshold_db=3):
        """
        Detect temporal RSSI anomalies that indicate environmental changes
        (e.g., person walking past, door opening, interference)
        
        Args:
            window_minutes: Rolling window for baseline calculation
            threshold_db: RSSI change threshold for event detection
        
        Returns:
            DataFrame of detected events
        """
        print(f"\n=== Detecting Movement Events (threshold: {threshold_db} dB) ===")
        
        events = []
        
        for mac in self.airtag_macs:
            device_data = self.df[self.df['mac_address'] == mac].copy()
            device_data = device_data.sort_values('timestamp')
            
            # Calculate rolling median RSSI
            device_data['rssi_baseline'] = device_data['rssi'].rolling(
                window=window_minutes*12,  # ~12 packets/min typical
                center=True
            ).median()
            
            # Detect deviations
            device_data['rssi_deviation'] = abs(device_data['rssi'] - device_data['rssi_baseline'])
            
            # Flag events
            anomalies = device_data[device_data['rssi_deviation'] > threshold_db]
            
            for _, row in anomalies.iterrows():
                events.append({
                    'timestamp': row['timestamp'],
                    'mac': mac,
                    'rssi': row['rssi'],
                    'baseline': row['rssi_baseline'],
                    'deviation': row['rssi_deviation']
                })
            
            print(f"  {mac[-8:]}: {len(anomalies)} events detected")
        
        events_df = pd.DataFrame(events)
        return events_df
    
    def generate_influence_terrain_heatmap(self, output_file="figure3_influence_terrain.png", 
                                          grid_resolution=100):
        """
        FIGURE 3: Influence Terrain Heatmap
        Shows spatial zones of IoT coverage - the core "influence terrain" concept
        """
        positions = self.estimated_positions or self.map_positions_from_known()
        
        # Create spatial grid
        x_coords = [pos[0] for pos in positions.values()]
        y_coords = [pos[1] for pos in positions.values()]
        
        x_min, x_max = min(x_coords) - 2, max(x_coords) + 2
        y_min, y_max = min(y_coords) - 2, max(y_coords) + 2
        
        x_grid = np.linspace(x_min, x_max, grid_resolution)
        y_grid = np.linspace(y_min, y_max, grid_resolution)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        # Calculate "influence" at each grid point
        # Influence = sum of signal strength from all devices
        influence = np.zeros_like(X)
        
        for mac, (x_dev, y_dev) in positions.items():
            rssi_baseline = self.rssi_baseline[mac]
            
            # Distance from each grid point to device
            distances = np.sqrt((X - x_dev)**2 + (Y - y_dev)**2)
            
            # Convert to influence (higher RSSI = more influence)
            # Use inverse square law approximation
            device_influence = 1 / (1 + distances**2)
            influence += device_influence
        
        # Normalize
        influence = influence / influence.max()
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Heatmap
        contour = ax.contourf(X, Y, influence, levels=20, cmap='YlOrRd', alpha=0.8)
        
        # Device positions
        for mac, (x, y) in positions.items():
            ax.plot(x, y, 'ko', markersize=15, markeredgewidth=2, 
                   markeredgecolor='white', label=f"{mac[-8:]}")
            ax.text(x, y+0.3, mac[-8:], ha='center', fontsize=9, 
                   weight='bold', color='white',
                   bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        # Styling
        ax.set_xlabel('X Position (meters)', fontsize=13, weight='bold')
        ax.set_ylabel('Y Position (meters)', fontsize=13, weight='bold')
        ax.set_title('Influence Terrain: IoT Coverage Zones\n' + 
                    'Heat intensity represents cumulative signal presence',
                    fontsize=15, weight='bold', pad=20)
        
        # Colorbar
        cbar = plt.colorbar(contour, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Normalized Influence Score', fontsize=12, weight='bold')
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_aspect('equal')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Figure 3 saved: {output_file}")
        plt.close()
    
    def generate_figure4_temporal_spatial(self, output_file="figure4_spatiotemporal.png"):
        """
        FIGURE 4: Spatiotemporal Signature Evolution
        Shows how RSSI changes over time for each device
        """
        fig, axes = plt.subplots(len(self.airtag_macs), 1, 
                                figsize=(14, 3*len(self.airtag_macs)), 
                                sharex=True)
        
        if len(self.airtag_macs) == 1:
            axes = [axes]
        
        for idx, mac in enumerate(self.airtag_macs):
            device_data = self.df[self.df['mac_address'] == mac].copy()
            device_data = device_data.sort_values('timestamp')
            
            # Time in hours
            device_data['hours'] = (device_data['timestamp'] - device_data['timestamp'].min()).dt.total_seconds() / 3600
            
            # Plot RSSI over time
            axes[idx].plot(device_data['hours'], device_data['rssi'], 
                         color='steelblue', alpha=0.6, linewidth=0.8)
            
            # Rolling median
            rolling_median = device_data.set_index('hours')['rssi'].rolling(
                window=50, center=True
            ).median()
            axes[idx].plot(rolling_median.index, rolling_median.values, 
                         color='red', linewidth=2, label='Rolling Median')
            
            # Baseline
            baseline = self.rssi_baseline[mac]
            axes[idx].axhline(baseline, color='green', linestyle='--', 
                            linewidth=2, label=f'Baseline: {baseline:.1f} dBm')
            
            # Styling
            axes[idx].set_ylabel('RSSI (dBm)', fontsize=11, weight='bold')
            axes[idx].set_title(f'Device {mac[-8:]}', fontsize=12, weight='bold')
            axes[idx].legend(loc='upper right', fontsize=9)
            axes[idx].grid(True, alpha=0.3)
        
        axes[-1].set_xlabel('Time (hours)', fontsize=12, weight='bold')
        
        plt.suptitle('Spatiotemporal RSSI Evolution: Environmental Stability Analysis', 
                    fontsize=15, weight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Figure 4 saved: {output_file}")
        plt.close()
    
    def export_analysis_summary(self, output_file="spatial_analysis_summary.json"):
        """Export all metrics for paper"""
        summary = {
            'capture_summary': {
                'total_packets': len(self.df),
                'n_devices': len(self.airtag_macs),
                'duration_hours': (self.df['timestamp'].max() - self.df['timestamp'].min()).total_seconds() / 3600
            },
            'device_positions': {
                mac[-8:]: {'x': pos[0], 'y': pos[1]} 
                for mac, pos in self.estimated_positions.items()
            },
            'rssi_baselines': {
                mac[-8:]: float(rssi) 
                for mac, rssi in self.rssi_baseline.items()
            },
            'rssi_statistics': {
                mac[-8:]: {
                    'mean': float(self.df[self.df['mac_address']==mac]['rssi'].mean()),
                    'std': float(self.df[self.df['mac_address']==mac]['rssi'].std()),
                    'min': float(self.df[self.df['mac_address']==mac]['rssi'].min()),
                    'max': float(self.df[self.df['mac_address']==mac]['rssi'].max())
                }
                for mac in self.airtag_macs
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Summary exported: {output_file}")
        return summary

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='RSSI-Based Spatial Analysis')
    parser.add_argument('--input', type=str, default='ble_capture_24h.csv')
    parser.add_argument('--positions', type=str, default=None,
                       help='JSON file with known positions: {"MAC": [x, y], ...}')
    
    args = parser.parse_args()
    
    # Load known positions if provided
    known_pos = None
    if args.positions:
        with open(args.positions, 'r') as f:
            known_pos = {k: tuple(v) for k, v in json.load(f).items()}
    
    # Run analysis
    mapper = InfluenceTerrainMapper(csv_file=args.input, known_positions=known_pos)
    
    # Position estimation
    mapper.map_positions_from_known()
    
    # Movement detection
    events = mapper.detect_movement_events()
    
    # Generate figures
    mapper.generate_influence_terrain_heatmap()
    mapper.generate_figure4_temporal_spatial()
    
    # Export metrics
    mapper.export_analysis_summary()
    
    print("\n✓ Spatial analysis complete!")
    print("\nGenerated:")
    print("  • Figure 3: Influence terrain heatmap")
    print("  • Figure 4: Spatiotemporal RSSI evolution")
    print("  • spatial_analysis_summary.json")
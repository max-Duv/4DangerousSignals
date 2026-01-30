#!/usr/bin/env python3
"""
BGP/AS Topology Analysis for Infrastructure Influence Modeling
Analyzes routing dependencies and identifies critical infrastructure
Author: Research Lab - Penn State
"""

import requests
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
from datetime import datetime
import time

class BGPAnalyzer:
    def __init__(self, target_country="US", cache_dir="bgp_cache"):
        """
        Initialize BGP analyzer for a target country
        
        Args:
            target_country: ISO 2-letter country code (US, CN, RU, etc.)
            cache_dir: Directory to cache downloaded data
        """
        self.target_country = target_country
        self.cache_dir = cache_dir
        self.as_graph = nx.DiGraph()
        self.as_metadata = {}
        
        # Create cache directory
        import os
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"BGP Analyzer initialized for country: {target_country}")
    
    def fetch_country_asns(self):
        """
        Fetch all ASNs registered in target country
        Uses RIPE Stat API for country-to-ASN mapping
        """
        print(f"\n=== Fetching ASNs for {self.target_country} ===")
        
        url = f"https://stat.ripe.net/data/country-resource-list/data.json?resource={self.target_country}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract ASNs
            asns = []
            if 'data' in data and 'resources' in data['data']:
                asn_list = data['data']['resources'].get('asn', [])
                for asn in asn_list:
                    if isinstance(asn, int):
                        asns.append(asn)
                    elif isinstance(asn, str) and asn.isdigit():
                        asns.append(int(asn))
            
            self.country_asns = set(asns)
            print(f"Found {len(self.country_asns)} ASNs registered in {self.target_country}")
            
            # Cache results
            cache_file = f"{self.cache_dir}/{self.target_country}_asns.json"
            with open(cache_file, 'w') as f:
                json.dump(list(self.country_asns), f)
            
            return self.country_asns
            
        except Exception as e:
            print(f"Error fetching ASNs: {e}")
            # Try to load from cache
            try:
                cache_file = f"{self.cache_dir}/{self.target_country}_asns.json"
                with open(cache_file, 'r') as f:
                    self.country_asns = set(json.load(f))
                print(f"Loaded {len(self.country_asns)} ASNs from cache")
                return self.country_asns
            except:
                print("No cached data available. Using sample ASNs.")
                # Fallback: major US providers
                self.country_asns = {7018, 3356, 174, 1299, 6939, 701, 209}
                return self.country_asns
    
    def fetch_as_relationships(self, sample_size=50):
        """
        Fetch AS relationship data (customer-provider, peer-peer)
        Uses CAIDA AS Relationships dataset concept
        
        For demonstration, we'll use RIPE Stat API to get AS neighbors
        """
        print(f"\n=== Building AS Relationship Graph (sample: {sample_size}) ===")
        
        # Sample ASNs to analyze (full analysis would take hours)
        sample_asns = list(self.country_asns)[:sample_size]
        
        for idx, asn in enumerate(sample_asns):
            print(f"Processing AS{asn} ({idx+1}/{len(sample_asns)})...", end='\r')
            
            try:
                # Fetch AS neighbors from RIPE
                url = f"https://stat.ripe.net/data/asn-neighbours/data.json?resource=AS{asn}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if 'data' in data and 'neighbours' in data['data']:
                    neighbours = data['data']['neighbours']
                    
                    # Add node
                    self.as_graph.add_node(asn, country=self.target_country)
                    
                    # Add edges (we assume provider relationship for simplicity)
                    for neighbour in neighbours:
                        neighbour_asn = neighbour.get('asn')
                        if neighbour_asn:
                            self.as_graph.add_edge(asn, neighbour_asn)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"\nError processing AS{asn}: {e}")
                continue
        
        print(f"\nBuilt graph: {self.as_graph.number_of_nodes()} nodes, {self.as_graph.number_of_edges()} edges")
        
        # Cache graph
        nx.write_gpickle(self.as_graph, f"{self.cache_dir}/as_graph_{self.target_country}.gpickle")
        
        return self.as_graph
    
    def load_cached_graph(self):
        """Load previously cached AS graph"""
        try:
            cache_file = f"{self.cache_dir}/as_graph_{self.target_country}.gpickle"
            self.as_graph = nx.read_gpickle(cache_file)
            print(f"Loaded cached graph: {self.as_graph.number_of_nodes()} nodes")
            return True
        except:
            print("No cached graph found")
            return False
    
    def analyze_centrality(self):
        """
        Calculate network centrality metrics to identify critical ASes
        
        Metrics:
        - Degree centrality: Number of connections (routing diversity)
        - Betweenness centrality: Transit importance (SPOF risk)
        - PageRank: Overall influence in routing topology
        """
        print("\n=== Calculating Centrality Metrics ===")
        
        if self.as_graph.number_of_nodes() == 0:
            print("Error: Graph is empty. Run fetch_as_relationships() first.")
            return None
        
        # Convert to undirected for centrality calculations
        G_undirected = self.as_graph.to_undirected()
        
        # Calculate metrics
        degree_cent = nx.degree_centrality(G_undirected)
        betweenness_cent = nx.betweenness_centrality(G_undirected)
        pagerank = nx.pagerank(self.as_graph)
        
        # Combine into DataFrame
        centrality_df = pd.DataFrame({
            'ASN': list(degree_cent.keys()),
            'Degree_Centrality': list(degree_cent.values()),
            'Betweenness_Centrality': list(betweenness_cent.values()),
            'PageRank': list(pagerank.values())
        })
        
        # Sort by betweenness (most critical for routing)
        centrality_df = centrality_df.sort_values('Betweenness_Centrality', ascending=False)
        
        print("\nTop 10 Critical ASes (by Betweenness Centrality):")
        print(centrality_df.head(10).to_string(index=False))
        
        self.centrality_df = centrality_df
        return centrality_df
    
    def identify_single_points_of_failure(self, threshold_percentile=95):
        """
        Identify ASes whose removal would fragment the network
        Uses betweenness centrality as proxy for SPOF risk
        """
        print(f"\n=== Identifying Single Points of Failure (>{threshold_percentile}th percentile) ===")
        
        threshold = self.centrality_df['Betweenness_Centrality'].quantile(threshold_percentile/100)
        
        spofs = self.centrality_df[
            self.centrality_df['Betweenness_Centrality'] >= threshold
        ]
        
        print(f"\nIdentified {len(spofs)} critical ASes:")
        print(spofs[['ASN', 'Betweenness_Centrality', 'Degree_Centrality']].to_string(index=False))
        
        self.spofs = spofs
        return spofs
    
    def simulate_as_removal(self, asn):
        """
        Simulate removal of an AS to measure impact on network connectivity
        
        Returns:
            dict: Impact metrics (connectivity drop, components created, etc.)
        """
        G_original = self.as_graph.to_undirected()
        
        # Baseline metrics
        original_components = nx.number_connected_components(G_original)
        original_largest = len(max(nx.connected_components(G_original), key=len))
        
        # Remove AS
        G_modified = G_original.copy()
        G_modified.remove_node(asn)
        
        # New metrics
        new_components = nx.number_connected_components(G_modified)
        new_largest = len(max(nx.connected_components(G_modified), key=len)) if G_modified.number_of_nodes() > 0 else 0
        
        impact = {
            'asn': asn,
            'components_created': new_components - original_components,
            'connectivity_loss': (original_largest - new_largest) / original_largest,
            'nodes_isolated': original_largest - new_largest
        }
        
        return impact
    
    def generate_figure5_as_topology(self, output_file="figure5_as_topology.png"):
        """
        FIGURE 5: AS-Level Dependency Graph
        Visualizes routing topology with critical nodes highlighted
        """
        print("\n=== Generating AS Topology Visualization ===")
        
        if self.as_graph.number_of_nodes() == 0:
            print("Error: No graph data. Run fetch_as_relationships() first.")
            return
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Use spring layout for AS graph
        pos = nx.spring_layout(self.as_graph, k=0.5, iterations=50, seed=42)
        
        # Node sizes based on degree
        node_sizes = [self.as_graph.degree(node) * 50 for node in self.as_graph.nodes()]
        
        # Node colors based on betweenness centrality
        betweenness = nx.betweenness_centrality(self.as_graph.to_undirected())
        node_colors = [betweenness.get(node, 0) for node in self.as_graph.nodes()]
        
        # Draw network
        nx.draw_networkx_edges(self.as_graph, pos, alpha=0.2, width=0.5, 
                              edge_color='gray', arrows=False, ax=ax)
        
        nodes = nx.draw_networkx_nodes(self.as_graph, pos, 
                                       node_size=node_sizes,
                                       node_color=node_colors,
                                       cmap='YlOrRd',
                                       alpha=0.8,
                                       ax=ax)
        
        # Label top 5 critical nodes
        if hasattr(self, 'centrality_df'):
            top_nodes = self.centrality_df.head(5)['ASN'].values
            labels = {node: f"AS{node}" for node in top_nodes if node in pos}
            nx.draw_networkx_labels(self.as_graph, pos, labels, 
                                   font_size=9, font_weight='bold',
                                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                                   ax=ax)
        
        # Colorbar
        sm = plt.cm.ScalarMappable(cmap='YlOrRd', 
                                   norm=plt.Normalize(vmin=min(node_colors), 
                                                     vmax=max(node_colors)))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Betweenness Centrality (SPOF Risk)', fontsize=12, weight='bold')
        
        ax.set_title(f'AS-Level Topology: {self.target_country} Internet Infrastructure\n' +
                    f'{self.as_graph.number_of_nodes()} ASes, {self.as_graph.number_of_edges()} connections',
                    fontsize=15, weight='bold', pad=20)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Figure 5 saved: {output_file}")
        plt.close()
    
    def generate_figure6_centrality_distribution(self, output_file="figure6_centrality_dist.png"):
        """
        FIGURE 6: Centrality Metric Distributions
        Shows statistical distribution of network criticality
        """
        if not hasattr(self, 'centrality_df'):
            print("Error: Run analyze_centrality() first")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Degree centrality histogram
        axes[0, 0].hist(self.centrality_df['Degree_Centrality'], bins=30, 
                       color='steelblue', alpha=0.7, edgecolor='black')
        axes[0, 0].set_xlabel('Degree Centrality', fontsize=11)
        axes[0, 0].set_ylabel('Frequency', fontsize=11)
        axes[0, 0].set_title('A: Degree Centrality Distribution', fontsize=12, weight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Betweenness centrality (log scale)
        axes[0, 1].hist(self.centrality_df['Betweenness_Centrality'], bins=30,
                       color='coral', alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel('Betweenness Centrality', fontsize=11)
        axes[0, 1].set_ylabel('Frequency', fontsize=11)
        axes[0, 1].set_title('B: Betweenness Centrality (SPOF Risk)', fontsize=12, weight='bold')
        axes[0, 1].set_yscale('log')
        axes[0, 1].grid(True, alpha=0.3)
        
        # PageRank distribution
        axes[1, 0].hist(self.centrality_df['PageRank'], bins=30,
                       color='green', alpha=0.7, edgecolor='black')
        axes[1, 0].set_xlabel('PageRank Score', fontsize=11)
        axes[1, 0].set_ylabel('Frequency', fontsize=11)
        axes[1, 0].set_title('C: PageRank Distribution', fontsize=12, weight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Scatter: Degree vs Betweenness
        axes[1, 1].scatter(self.centrality_df['Degree_Centrality'],
                          self.centrality_df['Betweenness_Centrality'],
                          alpha=0.6, s=50, c='purple')
        axes[1, 1].set_xlabel('Degree Centrality', fontsize=11)
        axes[1, 1].set_ylabel('Betweenness Centrality', fontsize=11)
        axes[1, 1].set_title('D: Degree vs Betweenness (Routing Diversity vs Transit Risk)', 
                            fontsize=12, weight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.suptitle('Network Centrality Analysis: Infrastructure Criticality Metrics',
                    fontsize=15, weight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Figure 6 saved: {output_file}")
        plt.close()
    
    def export_results(self, output_file="bgp_analysis_results.json"):
        """Export analysis results for paper"""
        results = {
            'metadata': {
                'target_country': self.target_country,
                'analysis_date': datetime.now().isoformat(),
                'total_asns': len(self.country_asns),
                'graph_nodes': self.as_graph.number_of_nodes(),
                'graph_edges': self.as_graph.number_of_edges()
            },
            'top_critical_ases': self.centrality_df.head(10).to_dict('records') if hasattr(self, 'centrality_df') else [],
            'spof_count': len(self.spofs) if hasattr(self, 'spofs') else 0
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Results exported: {output_file}")
        return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BGP/AS Topology Analysis')
    parser.add_argument('--country', type=str, default='US', help='ISO country code (US, CN, RU, etc.)')
    parser.add_argument('--sample-size', type=int, default=50, help='Number of ASes to sample')
    parser.add_argument('--use-cache', action='store_true', help='Load from cached data if available')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = BGPAnalyzer(target_country=args.country)
    
    # Fetch data or load cache
    if args.use_cache and analyzer.load_cached_graph():
        print("Using cached graph data")
    else:
        analyzer.fetch_country_asns()
        analyzer.fetch_as_relationships(sample_size=args.sample_size)
    
    # Run analysis
    analyzer.analyze_centrality()
    analyzer.identify_single_points_of_failure()
    
    # Generate visualizations
    analyzer.generate_figure5_as_topology()
    analyzer.generate_figure6_centrality_distribution()
    
    # Export results
    analyzer.export_results()
    
    print("\n✓ BGP analysis complete!")
    print("\nGenerated:")
    print("  • Figure 5: AS topology graph")
    print("  • Figure 6: Centrality distributions")
    print("  • bgp_analysis_results.json")
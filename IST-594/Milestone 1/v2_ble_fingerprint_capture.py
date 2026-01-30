#!/usr/bin/env python3
"""
BLE Beacon Fingerprinting v2 - Enhanced AirTag Detection
Adds device classification, manufacturer decoding, and AirTag filtering
Author: Research Lab - Penn State
"""

import asyncio
import datetime
import json
import csv
from bleak import BleakScanner
from collections import defaultdict
import binascii

class BLEFingerprinterV2:
    def __init__(self, output_file="ble_capture_v2.csv", airtag_only=False):
        self.output_file = output_file
        self.airtag_only = airtag_only
        self.packet_count = defaultdict(int)
        self.session_start = datetime.datetime.now()
        self.airtag_macs = set()  # Track discovered AirTags
        
        # Initialize CSV with headers
        self._init_csv()
        
    def _init_csv(self):
        """Create CSV with headers"""
        headers = [
            'timestamp', 'mac_address', 'rssi', 'local_name',
            'device_type', 'manufacturer_id', 'manufacturer_data_hex',
            'service_uuids', 'tx_power', 'is_airtag', 'airtag_status_byte'
        ]
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
    
    def _decode_manufacturer_data(self, manufacturer_data):
        """Extract and decode manufacturer data"""
        if not manufacturer_data:
            return None, None, None
        
        # manufacturer_data is dict: {company_id: bytes}
        for company_id, data_bytes in manufacturer_data.items():
            data_hex = binascii.hexlify(data_bytes).decode('ascii')
            return company_id, data_hex, data_bytes
        
        return None, None, None
    
    def _classify_device(self, device, advertisement_data, manufacturer_id, manufacturer_bytes):
        """Classify device type based on manufacturer and pattern"""
        
        # Apple devices (Company ID 76)
        if manufacturer_id == 76:
            if manufacturer_bytes and len(manufacturer_bytes) > 2:
                # AirTag detection: Apple Company ID + specific data patterns
                # AirTags typically start with 0x12 or 0x07 in status byte (index 0)
                status_byte = manufacturer_bytes[0]
                
                # AirTag heuristic: status byte patterns
                # 0x07, 0x12, 0x1C are common AirTag status bytes
                if status_byte in [0x07, 0x12, 0x1C, 0x01]:
                    return "AirTag", status_byte
                else:
                    return "Apple Device (Other)", status_byte
            return "Apple Device (Unknown)", None
        
        # Other known manufacturers
        manufacturer_names = {
            6: "Microsoft",
            89: "Xiaomi", 
            224: "Google",
            76: "Apple",
            117: "Samsung",
            529: "Tile",
            34819: "Govee",
            34818: "Govee"
        }
        
        if manufacturer_id in manufacturer_names:
            return manufacturer_names[manufacturer_id], None
        
        # Check local name patterns
        local_name = advertisement_data.local_name or ""
        if "Govee" in local_name:
            return "Govee IoT", None
        elif "DESKTOP" in local_name or "PC" in local_name:
            return "Windows PC", None
        
        return "Unknown BLE", None
    
    def detection_callback(self, device, advertisement_data):
        """Process each BLE advertisement packet with classification"""
        timestamp = datetime.datetime.now().isoformat()
        
        # Decode manufacturer data
        manufacturer_id, manufacturer_hex, manufacturer_bytes = \
            self._decode_manufacturer_data(advertisement_data.manufacturer_data)
        
        # Classify device
        device_type, airtag_status = self._classify_device(
            device, advertisement_data, manufacturer_id, manufacturer_bytes
        )
        
        is_airtag = (device_type == "AirTag")
        
        # Track AirTag MACs
        if is_airtag:
            self.airtag_macs.add(device.address)
        
        # Filter if airtag_only mode
        if self.airtag_only and not is_airtag:
            return
        
        # Build record
        record = {
            'timestamp': timestamp,
            'mac_address': device.address,
            'rssi': advertisement_data.rssi,
            'local_name': advertisement_data.local_name or "",
            'device_type': device_type,
            'manufacturer_id': manufacturer_id or "",
            'manufacturer_data_hex': manufacturer_hex or "",
            'service_uuids': ";".join(advertisement_data.service_uuids) if advertisement_data.service_uuids else "",
            'tx_power': advertisement_data.tx_power or "",
            'is_airtag': is_airtag,
            'airtag_status_byte': f"0x{airtag_status:02x}" if airtag_status is not None else ""
        }
        
        # Write to CSV
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=record.keys())
            writer.writerow(record)
        
        self.packet_count[device.address] += 1
        
        # Console feedback
        total_packets = sum(self.packet_count.values())
        if total_packets % 100 == 0:
            airtag_count = len(self.airtag_macs)
            print(f"[{timestamp[:19]}] {total_packets} pkts | {len(self.packet_count)} devices | {airtag_count} AirTags")
    
    async def scan_continuous(self, duration_hours=24):
        """Run continuous BLE scan"""
        end_time = datetime.datetime.now() + datetime.timedelta(hours=duration_hours)
        
        mode = "AirTag-only" if self.airtag_only else "All devices"
        print(f"Starting BLE capture ({mode}) for {duration_hours} hours...")
        print(f"Output: {self.output_file}")
        print("-" * 70)
        
        scanner = BleakScanner(detection_callback=self.detection_callback)
        await scanner.start()
        
        try:
            while datetime.datetime.now() < end_time:
                await asyncio.sleep(1)
                
                # Detailed status every 30 minutes
                if (datetime.datetime.now() - self.session_start).seconds % 1800 == 0:
                    await self._print_status()
                    
        except KeyboardInterrupt:
            print("\n\nCapture interrupted by user")
        finally:
            await scanner.stop()
            await self._print_final_summary()
    
    async def _print_status(self):
        """Print detailed status update"""
        elapsed = (datetime.datetime.now() - self.session_start).seconds / 3600
        print(f"\n{'='*70}")
        print(f"Status Update - {elapsed:.1f}h elapsed")
        print(f"{'='*70}")
        print(f"Total packets: {sum(self.packet_count.values())}")
        print(f"Unique devices: {len(self.packet_count)}")
        print(f"AirTags discovered: {len(self.airtag_macs)}")
        
        if self.airtag_macs:
            print("\nAirTag MACs:")
            for mac in sorted(self.airtag_macs):
                count = self.packet_count[mac]
                print(f"  {mac}: {count} packets")
        print(f"{'='*70}\n")
    
    async def _print_final_summary(self):
        """Print final capture summary"""
        print("\n" + "="*70)
        print("CAPTURE COMPLETE")
        print("="*70)
        print(f"Total packets: {sum(self.packet_count.values())}")
        print(f"Unique devices: {len(self.packet_count)}")
        print(f"AirTags found: {len(self.airtag_macs)}")
        print(f"Output: {self.output_file}")
        print("="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BLE Fingerprinting v2 with AirTag Detection')
    parser.add_argument('--duration', type=float, default=24, help='Capture duration in hours')
    parser.add_argument('--output', type=str, default='ble_capture_v2.csv', help='Output CSV')
    parser.add_argument('--airtag-only', action='store_true', help='Capture only AirTags (filter noise)')
    
    args = parser.parse_args()
    
    fingerprinter = BLEFingerprinterV2(
        output_file=args.output,
        airtag_only=args.airtag_only
    )
    
    asyncio.run(fingerprinter.scan_continuous(duration_hours=args.duration))
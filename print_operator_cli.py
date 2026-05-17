"""
Print Operator CLI Tool
========================
This script is used by the print operator (you) to process customer orders
and slice STL files using Bambu Studio CLI with AI-recommended settings.

Usage:
    # Process a specific order
    python print_operator_cli.py --order-file orders/order_123456/order_123456_summary.txt --stl-file orders/order_123456/model.stl
    
    # List all pending orders
    python print_operator_cli.py --list-orders
    
    # Interactive mode
    python print_operator_cli.py
"""

import argparse
import subprocess
import json
import os
import sys
from pathlib import Path

def list_orders():
    """List all orders in the orders directory"""
    orders_dir = Path(__file__).parent / "orders"
    
    if not orders_dir.exists():
        print("✗ No orders directory found")
        print(f"  Expected location: {orders_dir}")
        return
    
    order_dirs = [d for d in orders_dir.iterdir() if d.is_dir() and d.name.startswith("order_")]
    
    if not order_dirs:
        print("📭 No orders found")
        return
    
    print("=" * 80)
    print(f"  PENDING ORDERS ({len(order_dirs)} total)")
    print("=" * 80)
    
    for order_dir in sorted(order_dirs):
        order_id = order_dir.name.replace("order_", "")
        json_file = order_dir / f"order_{order_id}_data.json"
        
        print(f"\n📦 Order #{order_id}")
        print(f"   Location: {order_dir}")
        
        if json_file.exists():
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"   STL File: {data.get('stl_file', 'N/A')}")
            print(f"   Priority: {data.get('priority', 'N/A')}")
            print(f"   Material: {data.get('recommendations', {}).get('material', 'N/A')}")
            print(f"   Cost: ${data.get('total_cost', 0):.2f}")
            
            # Show CLI command to process
            stl_file = order_dir / data.get('stl_file', '')
            summary_file = order_dir / f"order_{order_id}_summary.txt"
            
            if stl_file.exists() and summary_file.exists():
                print(f"\n   🔧 To process this order:")
                print(f"      python print_operator_cli.py --stl-file \"{stl_file}\" --order-file \"{summary_file}\"")
        else:
            print(f"   ⚠️ Order data file not found")
        
        print("-" * 80)

def check_bambu_cli():
    """Check if Bambu Studio CLI is available"""
    try:
        cli_names = ['bambu-cli', 'BambuStudio-cli', 'bambu_studio_cli']
        
        for cli_name in cli_names:
            result = subprocess.run(
                [cli_name, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ Found Bambu Studio CLI: {cli_name}")
                return cli_name
        return None
    except Exception:
        return None

def parse_order_summary(order_file):
    """Parse order summary text file to extract settings"""
    with open(order_file, 'r') as f:
        content = f.read()
    
    # Extract key information
    order_data = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            order_data[key] = value
    
    return order_data

def build_cli_command(stl_file, output_file, settings, cli_exe='bambu-cli'):
    """Build Bambu Studio CLI command from settings"""
    
    cmd = [
        cli_exe,
        'slice',
        stl_file,
        '-o', output_file,
    ]
    
    # Add parameters based on settings
    if 'material' in settings:
        material = settings['material'].split()[0].upper()
        cmd.extend(['--filament-type', material])
    
    if 'layer_height' in settings:
        layer_height = settings['layer_height'].replace('mm', '').strip()
        cmd.extend(['--layer-height', layer_height])
    
    if 'infill' in settings:
        infill = settings['infill'].replace('%', '').strip()
        cmd.extend(['--infill-density', f"{infill}%"])
    
    if 'walls' in settings:
        walls = settings['walls'].split()[0]
        cmd.extend(['--wall-loops', walls])
    
    if 'supports' in settings and settings['supports'].lower() != 'none':
        cmd.append('--support-material')
    
    return cmd

def slice_model(stl_file, order_file=None, output_file=None):
    """Slice a model using Bambu Studio CLI"""
    
    # Check CLI availability
    cli_exe = check_bambu_cli()
    if not cli_exe:
        print("✗ ERROR: Bambu Studio CLI not found!")
        print("\nPlease install Bambu Studio and add it to your PATH")
        print("Download: https://bambulab.com/en/download/studio")
        return False
    
    # Parse order file if provided
    settings = {}
    if order_file:
        print(f"\n📄 Reading order file: {order_file}")
        settings = parse_order_summary(order_file)
        print(f"✓ Order ID: {settings.get('order_id', 'N/A')}")
        print(f"✓ Material: {settings.get('material', 'N/A')}")
        print(f"✓ Layer Height: {settings.get('layer_height', 'N/A')}")
        print(f"✓ Infill: {settings.get('infill', 'N/A')}")
    
    # Determine output file
    if not output_file:
        base_name = Path(stl_file).stem
        output_file = f"{base_name}_sliced.3mf"
    
    # Build command
    cmd = build_cli_command(stl_file, output_file, settings, cli_exe)
    
    print(f"\n🔧 Slicing command:")
    print(f"   {' '.join(cmd)}")
    print(f"\n⏳ Starting slicing process...")
    
    try:
        # Execute CLI command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"\n✓ SUCCESS! Model sliced successfully")
            print(f"✓ Output saved to: {output_file}")
            
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"✓ File size: {size:,} bytes")
            
            if result.stdout:
                print("\nCLI Output:")
                print(result.stdout)
            
            return True
        else:
            print(f"\n✗ ERROR: Slicing failed (exit code {result.returncode})")
            if result.stderr:
                print("Error details:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("\n✗ ERROR: Slicing timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False

def interactive_mode():
    """Run in interactive mode"""
    print("=" * 60)
    print("  PRINT OPERATOR CLI - Interactive Mode")
    print("=" * 60)
    
    # Get STL file
    stl_file = input("\n📦 Enter path to STL file: ").strip().strip('"')
    if not os.path.exists(stl_file):
        print(f"✗ ERROR: File not found: {stl_file}")
        return
    
    # Ask for order file
    use_order = input("\n📄 Do you have an order summary file? (y/n): ").strip().lower()
    order_file = None
    
    if use_order == 'y':
        order_file = input("📄 Enter path to order summary: ").strip().strip('"')
        if not os.path.exists(order_file):
            print(f"✗ WARNING: Order file not found, proceeding with defaults")
            order_file = None
    
    # Ask for output file
    output_file = input("\n💾 Enter output filename (or press Enter for auto): ").strip()
    if not output_file:
        output_file = None
    
    # Confirm
    print("\n" + "=" * 60)
    print("Ready to slice:")
    print(f"  Input:  {stl_file}")
    print(f"  Order:  {order_file if order_file else 'None (using defaults)'}")
    print(f"  Output: {output_file if output_file else 'Auto-generated'}")
    print("=" * 60)
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed == 'y':
        slice_model(stl_file, order_file, output_file)
    else:
        print("Cancelled.")

def main():
    parser = argparse.ArgumentParser(
        description="Print Operator CLI Tool - Process customer orders and slice STL files"
    )
    parser.add_argument('--stl-file', '-s', help='Path to STL file')
    parser.add_argument('--order-file', '-o', help='Path to order summary file')
    parser.add_argument('--output', '-out', help='Output filename for sliced model')
    parser.add_argument('--check-cli', action='store_true', help='Check if Bambu Studio CLI is installed')
    parser.add_argument('--list-orders', '-l', action='store_true', help='List all pending orders')
    
    args = parser.parse_args()
    
    # List orders mode
    if args.list_orders:
        list_orders()
        sys.exit(0)
    
    # Check CLI mode
    if args.check_cli:
        cli = check_bambu_cli()
        if cli:
            print(f"✓ Bambu Studio CLI is installed: {cli}")
            sys.exit(0)
        else:
            print("✗ Bambu Studio CLI not found")
            sys.exit(1)
    
    # If STL file provided, process it
    if args.stl_file:
        if not os.path.exists(args.stl_file):
            print(f"✗ ERROR: STL file not found: {args.stl_file}")
            sys.exit(1)
        
        success = slice_model(args.stl_file, args.order_file, args.output)
        sys.exit(0 if success else 1)
    
    # Otherwise, run interactive mode
    interactive_mode()

if __name__ == "__main__":
    main()

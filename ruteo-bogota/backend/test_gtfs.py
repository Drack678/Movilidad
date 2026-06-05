import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.gtfs_service import get_gtfs

print("Testing GTFS service...")
try:
    gtfs = get_gtfs()
    print("[OK] GTFS loaded successfully!")
    print(f"   - Stops: {len(gtfs.stops)}")
    print(f"   - Routes: {len(gtfs.routes)}")
    print(f"   - Trunk route IDs: {len(gtfs.trunk_route_ids)}")
    
    # Test building the network
    print("\nBuilding trunk network...")
    network = gtfs.build_trunk_network()
    print("[OK] Network built!")
    print(f"   - Nodes: {len(network['nodes'])}")
    print(f"   - Lines: {len(network['lines'])}")
    print(f"   - Stats: {network['stats']}")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

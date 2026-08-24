import argparse
import datetime
import os
import shutil
from src.utils.json_utils import load_json, save_json

def create_version(description, approver, component, old_version_file, new_version_str):
    registry_path = "config/version_registry.json"
    registry = load_json(registry_path)
    
    current_version = registry["current_versions"].get(component, "1.0.0")
    if current_version == new_version_str:
        print(f"Error: Version {new_version_str} is already the active version for {component}.")
        return
        
    # Archive current version before modifying
    archive_dir = "config/archive"
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{component}_v{current_version}.json")
    
    if os.path.exists(old_version_file):
        shutil.copy2(old_version_file, archive_path)
        
    # Read the file and update its internal version string
    comp_data = load_json(old_version_file)
    comp_data["version"] = new_version_str
    save_json(comp_data, old_version_file)
    
    # Update registry
    registry["current_versions"][component] = new_version_str
    
    history_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "change": description,
        "approver": approver,
        "updated_components": [
            {
                "component": component,
                "old_version": current_version,
                "new_version": new_version_str
            }
        ]
    }
    registry["history"].append(history_entry)
    save_json(registry, registry_path)
    
    print(f"Successfully bumped {component} to {new_version_str}.")

def main():
    parser = argparse.ArgumentParser(description="Version control for configuration")
    subparsers = parser.add_subparsers(dest="command")
    
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--change", required=True, help="Description of the change")
    create_parser.add_argument("--approver", required=True, help="Who approved the change")
    create_parser.add_argument("--component", required=True, help="Component to bump (e.g., scoring_config)")
    create_parser.add_argument("--file", required=True, help="Path to the config file being updated")
    create_parser.add_argument("--new-version", required=True, help="New version string (e.g., 1.1.0)")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_version(args.change, args.approver, args.component, args.file, args.new_version)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

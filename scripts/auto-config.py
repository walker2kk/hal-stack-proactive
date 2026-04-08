#!/usr/bin/env python3
"""
Auto-configure token tracker by reading user's openclaw.json configuration.
Extracts default model and all configured models.
"""
import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".openclaw/openclaw.json"
OUTPUT_CONFIG_PATH = Path.home() / ".openclaw/workspace/skills/hal-stack-proactive/config/user-models.json"

def read_openclaw_config(config_path=DEFAULT_CONFIG_PATH):
    """Read and parse openclaw.json."""
    if not config_path.exists():
        print(f"⚠️  OpenClaw config not found at {config_path}")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing openclaw.json: {e}")
        return None

def extract_models(config):
    """Extract default model and all configured models from config."""
    result = {
        "default_model": None,
        "configured_models": [],
        "source": str(DEFAULT_CONFIG_PATH)
    }
    
    agents = config.get("agents", {}).get("defaults", {})
    
    # Extract primary default model
    model_config = agents.get("model", {})
    if isinstance(model_config, str):
        result["default_model"] = model_config
    elif isinstance(model_config, dict):
        result["default_model"] = model_config.get("primary")
    
    # Extract all configured models from models catalog
    models_catalog = agents.get("models", {})
    if models_catalog and isinstance(models_catalog, dict):
        result["configured_models"] = list(models_catalog.keys())
    
    return result

def save_config(data):
    """Save extracted model configuration."""
    OUTPUT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved auto-configuration to {OUTPUT_CONFIG_PATH}")
    return True

def main():
    """Auto-configure token tracker."""
    config = read_openclaw_config()
    if not config:
        # Write empty config
        save_config({
            "default_model": None,
            "configured_models": [],
            "source": None
        })
        print("Using built-in defaults.")
        return 0
    
    extracted = extract_models(config)
    save_config(extracted)
    
    if extracted["default_model"]:
        print(f"✓ Found default model: {extracted['default_model']}")
    if extracted["configured_models"]:
        print(f"✓ Found {len(extracted['configured_models'])} configured models:")
        for model in extracted["configured_models"]:
            print(f"    - {model}")
    
    print("\nToken tracker auto-configured successfully!")
    return 0

if __name__ == "__main__":
    exit(main())

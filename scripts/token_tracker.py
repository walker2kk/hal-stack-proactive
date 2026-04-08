#!/usr/bin/env python3
"""
Token usage tracker with budget alerts.
Monitors API usage and warns when approaching limits.
Supports any model provider through OpenClaw session logging.
Automatically reads model configuration from user's openclaw.json.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

STATE_FILE = Path.home() / ".openclaw/workspace/memory/token-tracker-state.json"
USER_CONFIG_PATH = Path.home() / ".openclaw/workspace/skills/hal-stack-proactive/config/user-models.json"

# Pricing data - update this when model prices change
# Format: (input_cost_per_million, output_cost_per_million)
MODEL_PRICING = {
    # Anthropic
    "anthropic/claude-opus-4": (15.0, 75.0),
    "anthropic/claude-sonnet-4-5": (3.0, 15.0),
    "anthropic/claude-haiku-4": (0.25, 1.25),
    # OpenAI
    "openai/gpt-4o": (2.5, 10.0),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-image-1": (0.04, None),  # per image
    # Google
    "google/gemini-2.0-flash": (0.15, 0.75),
    "google/gemini-2.0-pro": (1.25, 3.75),
    # Volces/ByteDance
    "volces/ark-code-latest": (0.5, 1.0),
    "volces/ark-deepseek-v3": (0.3, 0.8),
    # Default fallback - generic pricing
    "default": (0.5, 1.0),
}

def load_state():
    """Load tracking state from file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "daily_usage": {},
        "alerts_sent": [],
        "last_reset": datetime.now().isoformat(),
        "config": {
            "daily_limit_usd": 5.0,
            "warn_threshold": 0.8
        }
    }

def load_user_models():
    """Load user-configured models from auto-extracted config."""
    if USER_CONFIG_PATH.exists():
        try:
            with open(USER_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "default_model": None,
        "configured_models": [],
        "source": None
    }

def get_default_model():
    """Get the user's default model from auto-configuration."""
    config = load_user_models()
    return config.get("default_model")

def save_state(state):
    """Save tracking state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_model_pricing(model):
    """Get pricing for a model, return default if not found."""
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    # Try prefix matching (e.g. "volces/*" matches any volces model)
    for key in MODEL_PRICING:
        if key.endswith("*") and model.startswith(key[:-1]):
            return MODEL_PRICING[key]
    # Return default
    return MODEL_PRICING["default"]

def calculate_cost(input_tokens, output_tokens, model):
    """Calculate cost in USD for given token count and model."""
    input_cost_per_m, output_cost_per_m = get_model_pricing(model)
    
    input_cost = (input_tokens / 1_000_000) * input_cost_per_m
    if output_cost_per_m is not None:
        output_cost = (output_tokens / 1_000_000) * output_cost_per_m
    else:
        output_cost = 0
    
    return input_cost + output_cost

def get_auto_configured_default():
    """Get default model from auto-configuration, fall back to built-in default."""
    default = get_default_model()
    if default:
        return default
    return "anthropic/claude-sonnet-4-5"

def check_budget(daily_limit_usd=None, warn_threshold=None):
    """Check if usage is approaching daily budget.
    
    Args:
        daily_limit_usd: Daily spending limit in USD (overrides config)
        warn_threshold: Fraction of limit to trigger warning (default 80%)
    
    Returns:
        dict with status, usage, limit, and alert message if applicable
    """
    state = load_state()
    today = datetime.now().date().isoformat()
    
    # Get config from state or use defaults
    config = state.get("config", {})
    if daily_limit_usd is None:
        daily_limit_usd = config.get("daily_limit_usd", 5.0)
    if warn_threshold is None:
        warn_threshold = config.get("warn_threshold", 0.8)
    
    # Reset if new day
    if today not in state["daily_usage"]:
        state["daily_usage"][today] = {
            "cost": 0.0, 
            "tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        state["alerts_sent"] = []
        save_state(state)
    
    usage = state["daily_usage"][today]
    percent_used = (usage["cost"] / daily_limit_usd) * 100 if daily_limit_usd > 0 else 0
    
    result = {
        "date": today,
        "cost": usage["cost"],
        "tokens": usage.get("tokens", usage["cost"] * 100_000),  # backward compat
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "limit": daily_limit_usd,
        "percent_used": percent_used,
        "default_model": get_auto_configured_default(),
        "status": "ok"
    }
    
    # Check thresholds
    if daily_limit_usd > 0:
        if percent_used >= 100:
            result["status"] = "exceeded"
            result["alert"] = f"⚠️ Daily budget exceeded! ${usage['cost']:.2f} / ${daily_limit_usd:.2f}"
        elif percent_used >= (warn_threshold * 100):
            result["status"] = "warning"
            result["alert"] = f"⚠️ Approaching daily limit: ${usage['cost']:.2f} / ${daily_limit_usd:.2f} ({percent_used:.0f}%)"
    
    return result

def record_usage(input_tokens, output_tokens, model=None):
    """Record token usage for today.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier (e.g. "volces/ark-code-latest"). 
                If None, uses auto-configured default from openclaw.json.
    """
    if model is None:
        model = get_auto_configured_default()
    
    cost = calculate_cost(input_tokens, output_tokens, model)
    
    state = load_state()
    today = datetime.now().date().isoformat()
    
    if today not in state["daily_usage"]:
        state["daily_usage"][today] = {
            "cost": 0.0,
            "tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
    
    state["daily_usage"][today]["cost"] += cost
    state["daily_usage"][today]["tokens"] += (input_tokens + output_tokens)
    state["daily_usage"][today]["input_tokens"] += input_tokens
    state["daily_usage"][today]["output_tokens"] += output_tokens
    
    save_state(state)
    
    return {
        "added_cost": cost,
        "added_tokens": input_tokens + output_tokens,
        "model": model
    }

def suggest_cheaper_model(current_model=None, task_type="general"):
    """Suggest cheaper alternative models based on task type.
    
    Args:
        current_model: Currently configured model. If None, uses auto-configured default.
        task_type: Type of task (general, simple, complex)
    
    Returns:
        dict with suggestion and cost savings
    """
    if current_model is None:
        current_model = get_auto_configured_default()
    
    suggestions = {
        "simple": [
            ("anthropic/claude-haiku-4", "12x cheaper, great for file reads, routine checks"),
            ("google/gemini-2.0-flash", "much cheaper, good for simple tasks"),
            ("openai/gpt-4o-mini", "17x cheaper, fast and capable")
        ],
        "general": [
            ("anthropic/claude-sonnet-4-5", "Balanced performance and cost"),
            ("google/gemini-2.0-flash", "Much cheaper, decent quality"),
            ("volces/ark-deepseek-v3", "Low cost, good quality")
        ],
        "complex": [
            ("anthropic/claude-opus-4", "Best reasoning, use sparingly"),
            ("anthropic/claude-sonnet-4-5", "Good balance for most complex tasks")
        ]
    }
    
    current_input, current_output = get_model_pricing(current_model)
    current_avg = (current_input + current_output) / 2
    
    result = {
        "current": current_model,
        "current_avg_cost_per_million": current_avg,
        "suggestions": []
    }
    
    for (suggested, description) in suggestions.get(task_type, suggestions["general"]):
        s_input, s_output = get_model_pricing(suggested)
        s_avg = (s_input + s_output) / 2
        if current_avg > 0:
            savings_x = round(current_avg / s_avg, 1)
            description += f" (≈ {savings_x}x cheaper)"
        result["suggestions"].append((suggested, description))
    
    return result

def configure(daily_limit_usd=None, warn_threshold=None):
    """Update configuration."""
    state = load_state()
    if "config" not in state:
        state["config"] = {}
    
    if daily_limit_usd is not None:
        state["config"]["daily_limit_usd"] = float(daily_limit_usd)
    if warn_threshold is not None:
        state["config"]["warn_threshold"] = float(warn_threshold)
    
    save_state(state)
    return state["config"]

def main():
    """CLI interface for token tracker."""
    import sys
    
    if len(sys.argv) < 2:
        print("""Token Tracker - OpenClaw Hal Stack
Usage:
  token_tracker.py check                    Check current budget status
  token_tracker.py record <in> <out> [model]  Record token usage (model defaults to auto-configured)
  token_tracker.py suggest [task] [model]  Suggest cheaper model
  token_tracker.py configure <limit> [threshold]  Configure daily limit
  token_tracker.py reset                    Reset daily usage
  token_tracker.py models                   List supported models
  token_tracker.py auto-config              Auto-configure from openclaw.json
""")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        result = check_budget()
        print(json.dumps(result, indent=2))
    
    elif command == "record":
        if len(sys.argv) < 4:
            print("Usage: token_tracker.py record <input_tokens> <output_tokens> [model]")
            print("       If model is omitted, uses auto-configured default from openclaw.json")
            sys.exit(1)
        input_tokens = int(sys.argv[2])
        output_tokens = int(sys.argv[3])
        model = sys.argv[4] if len(sys.argv) > 4 else None
        result = record_usage(input_tokens, output_tokens, model)
        print(json.dumps(result, indent=2))
    
    elif command == "suggest":
        task = sys.argv[2] if len(sys.argv) > 2 else "general"
        current = sys.argv[3] if len(sys.argv) > 3 else None
        result = suggest_cheaper_model(current, task)
        print(json.dumps(result, indent=2))
    
    elif command == "configure":
        if len(sys.argv) < 3:
            print("Usage: token_tracker.py configure <daily_limit_usd> [warn_threshold]")
            sys.exit(1)
        limit = float(sys.argv[2])
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else None
        config = configure(limit, threshold)
        print(json.dumps(config, indent=2))
    
    elif command == "reset":
        state = load_state()
        state["daily_usage"] = {}
        state["alerts_sent"] = []
        save_state(state)
        print("Token tracker state reset for today.")
    
    elif command == "models":
        print("Built-in supported models and pricing (input/output $ per million tokens):")
        for model, (input_p, output_p) in sorted(MODEL_PRICING.items()):
            if output_p:
                print(f"  {model}: ${input_p:.2f} / ${output_p:.2f}")
            else:
                print(f"  {model}: ${input_p:.2f} (special pricing)")
        
        # Show user-configured models
        user_config = load_user_models()
        if user_config.get("configured_models"):
            print("\nUser-configured models from openclaw.json:")
            for model in user_config["configured_models"]:
                is_default = " (default)" if model == user_config.get("default_model") else ""
                print(f"  - {model}{is_default}")
    
    elif command == "auto-config":
        # Import and run auto-config
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "auto_config",
            Path(__file__).parent / "auto-config.py"
        )
        auto_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auto_config)
        exit(auto_config.main())
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()

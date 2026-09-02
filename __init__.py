"""
Plugin System for Telegram Bot Manager

How to add a new plugin:
1. Create a new .py file in this folder
2. Define an async function with the signature matching a hook
3. Register it using @register_hook("hook_name")

Available hooks:
- "on_bot_added": (token, username) -> None
- "on_bot_started": (token, username) -> None  
- "on_bot_stopped": (token, username) -> None
- "on_broadcast_sent": (token, count) -> None
- "on_admin_panel": (keyboard, context) -> keyboard
- "on_export": (filepath, admin_id) -> None
- "on_user_joined": (user_id, bot_token) -> None
- "on_text_received": (update, context) -> bool (return True to stop processing)
"""
import os
import sys
import importlib
import inspect
from functools import wraps

# Global hook registry
_HOOKS = {}


def register_hook(name):
    """Decorator to register a function as a hook handler"""
    def decorator(func):
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Hook handler {func.__name__} must be async")
        _HOOKS.setdefault(name, []).append(func)
        return func
    return decorator


async def call_hook(name, *args, **kwargs):
    """Call all registered handlers for a hook"""
    results = []
    for handler in _HOOKS.get(name, []):
        try:
            result = await handler(*args, **kwargs)
            results.append(result)
        except Exception as e:
            print(f"[Plugin Error] Hook '{name}' in {handler.__name__}: {e}")
    return results


def get_hook_handlers(name):
    """Get all handlers for a specific hook"""
    return _HOOKS.get(name, [])


def load_plugins():
    """Auto-discover and load all plugins from this directory"""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    loaded = []

    for filename in os.listdir(plugin_dir):
        if filename.startswith("_") or not filename.endswith(".py"):
            continue
        module_name = filename[:-3]
        try:
            # Use importlib for proper reloading support
            spec = importlib.util.spec_from_file_location(
                f"plugins.{module_name}",
                os.path.join(plugin_dir, filename)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{module_name}"] = module
            spec.loader.exec_module(module)
            loaded.append(module_name)
            print(f"[Plugin] Loaded: {module_name}")
        except Exception as e:
            print(f"[Plugin Error] Failed to load {module_name}: {e}")

    return loaded


def get_loaded_plugins():
    """Return list of loaded plugin names"""
    return list(set(
        h.__module__.replace("plugins.", "") 
        for hooks in _HOOKS.values() 
        for h in hooks
    ))

#!/usr/bin/env python3
"""Start the lerobot async policy server with LeIsaac compatibility shim.

LeIsaac's client pickles RemotePolicyConfig with __module__ = 'lerobot.scripts.server.helpers'.
The standard lerobot server uses 'lerobot.async_inference.helpers'. This wrapper creates the
module alias so pickle deserialization works.
"""
import sys
import types

from lerobot.async_inference import helpers as real_helpers

alias = "lerobot.scripts.server.helpers"
parts = alias.split(".")
for i in range(1, len(parts) + 1):
    sub = ".".join(parts[:i])
    if sub not in sys.modules:
        mod = types.ModuleType(sub)
        sys.modules[sub] = mod
        if i > 1:
            parent = ".".join(parts[:i-1])
            setattr(sys.modules[parent], parts[i-1], mod)

sys.modules[alias].__dict__.update(real_helpers.__dict__)

from lerobot.async_inference.policy_server import serve
serve()

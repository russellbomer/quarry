Concrete Quarry Modifications for Single Session Directory Export
Based on my review of your terminal server implementation, here are the specific changes needed in Quarry to optimize it for the session directory approach:

Overview
Your terminal server already sets QUARRY_OUTPUT_DIR=/home/quarry/output/<session-id>/ in the environment. Quarry needs to respect this environment variable instead of using its internal defaults, and it needs to suppress user prompts that ask for output directory selection (since we want all output going to the single session directory).

Required Quarry Modifications
1. Environment Variable Support — QUARRY_OUTPUT_DIR
What: Quarry should check for the QUARRY_OUTPUT_DIR environment variable at startup and use it as the base output directory for ALL modes (foreman, wizard, scout).

Current Behavior (likely):

foreman mode outputs to a hardcoded path (e.g., /var/www/portfolio/foreman_tutorial)
wizard mode outputs to a relative path (e.g., ./data/out/)
User can select custom paths in some modes
Desired Behavior:

If QUARRY_OUTPUT_DIR is set, use it as the base directory for all outputs
If not set, fall back to current defaults (for backward compatibility)
All generated files (schemas, data, results) should go to this directory
Implementation Location:

In your Quarry initialization code (likely in main.py or equivalent entry point)
Before foreman/wizard/scout handlers run
Pseudo-code:
```
import os

# At startup
output_dir = os.getenv('QUARRY_OUTPUT_DIR')
if output_dir:
    # Use session directory as base for all outputs
    CONFIG.base_output_dir = output_dir
    # Foreman, wizard, scout should respect this
else:
    # Fall back to defaults
    CONFIG.base_output_dir = None  # Use existing defaults
    ```
2. Suppress User Output Path Selection Prompts
What: In wizard and other interactive modes, remove or skip the prompt that asks users "Where should I save the output?"

Current Behavior:

Wizard prompts: "Select a path for output if you desire" (optional)
User can accept default or specify custom path
Desired Behavior:

Skip the output path prompt entirely when QUARRY_OUTPUT_DIR is set
Use the environment variable value (no user input needed)
If not set, optionally show the prompt (backward compatibility)
Implementation Strategy:

In wizard/interactive mode, add a check:
```
if os.getenv('QUARRY_OUTPUT_DIR'):
    # Skip output path prompt; use env var
    output_path = os.getenv('QUARRY_OUTPUT_DIR')
else:
    # Show prompt and let user select (existing behavior)
    output_path = prompt_user_for_output_path()
```

3. Unify Output Paths Across All Modes
What: Ensure all three Quarry modes (foreman, wizard, scout) write to the same unified output directory structure.

Current Behavior (likely):

foreman: /var/www/portfolio/foreman_tutorial/ (hardcoded)
wizard: data/out/{schema_name}.jsonl (relative path)
scout: Depends on mode (web scraping output location unclear)
Desired Behavior:

All modes respect QUARRY_OUTPUT_DIR
Wizard: $QUARRY_OUTPUT_DIR/data/out/{schema_name}.jsonl
Foreman: $QUARRY_OUTPUT_DIR/foreman_output/ (or similar)
Scout: $QUARRY_OUTPUT_DIR/scout_output/ (or similar)
All intermediate files (schemas, temp files) also go to $QUARRY_OUTPUT_DIR
Implementation:

Audit each mode's output logic
Replace hardcoded/relative paths with os.path.join(output_dir, 'mode_specific_subdir')
Ensure all file writes check the env var first
4. Handle the QUARRY_SCHEMA_DIR and QUARRY_DATA_DIR Variables (Optional but Recommended)
What: For even better control, add support for granular output directory configuration.

Rationale: Your terminal server only needs one env var, but Quarry might benefit from flexibility.

Recommendation:
```
# Allow granular control for future use
schema_dir = os.getenv('QUARRY_SCHEMA_DIR') or os.path.join(
    os.getenv('QUARRY_OUTPUT_DIR', '.'),
    'schemas'
)
data_dir = os.getenv('QUARRY_DATA_DIR') or os.path.join(
    os.getenv('QUARRY_OUTPUT_DIR', '.'),
    'data/out'
)```

This way:

Terminal server sets only QUARRY_OUTPUT_DIR=/home/quarry/output/<session-id>/
Quarry automatically creates schemas/, data/out/ subdirectories
Or users can override individually if needed

5. Ensure No Hardcoded Paths
What: Audit the codebase for hardcoded paths that assume a specific file structure.

Examples to remove/refactor:

"/var/www/portfolio/foreman_tutorial" → Use env var or subdirectory
"./data/out/" → Use env var or subdirectory
Any absolute paths in config files → Make relative to output dir
Testing:

Run Quarry with QUARRY_OUTPUT_DIR=/tmp/test-session-uuid/
Verify all files end up in that directory or subdirectories
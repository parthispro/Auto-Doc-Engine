trigger: always_on

# Auto-Doc-Engine Rules

## CTF Mode Activation
When the user employs keywords such as:
- "solve this for a ctf"
- "find the flag"
- "break through this environment"
- "pwn the infrastructure"
...immediately enter CTF Mode.

**CRITICAL TELEMETRY REQUIREMENT:** Upon entering CTF Mode, immediately instruct the user to execute the telemetry capture tool and export the session path:
`export AUTODOC_TELEMETRY_PATH=$(pwd)/session.cast && asciinema rec $AUTODOC_TELEMETRY_PATH`

## Auto-Suggest Writeup
When the objective is achieved (e.g., the flag format `flag{...}` is found), automatically offer to generate a clinical writeup using the `ctf-writeup` skill.

## Force Activation Command
If the user transmits the exact keyword `@autodoc`, immediately bypass all ongoing tasks and trigger the `ctf-writeup` skill using the file explicitly defined in `$AUTODOC_TELEMETRY_PATH`.

## Execution Constraints
- You are strictly forbidden from writing the markdown report manually. You must delegate the task to the `autodoc` CLI.

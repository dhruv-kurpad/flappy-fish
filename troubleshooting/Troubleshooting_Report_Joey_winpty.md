# Troubleshooting Report

### System Specifications

**Operating System:** Windows

### Problem Description

There was a weird infinite looping issue whenever I ran the program in GitBash using the command ```py src/main.py``. The issue only happened in GitBash, any other terminal was fine.

### Problem Resolution

After research, I found that there was a weird connection issue with windows and GitBash where the programs weren't running correctly. I found that adding ```winpty``` before the command fixed the problem.

New Command: ```winpty py src/main.py```

### Sources

- Copilot


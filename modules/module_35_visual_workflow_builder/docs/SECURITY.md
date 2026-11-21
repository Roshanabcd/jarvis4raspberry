# Security Model — JARVIS Module 35 (Visual Workflow Builder)

1. **Zero Arbitrary Code Execution**: Workflow nodes (`trigger`, `transform`, `condition`, `math`, `notify`) use strictly typed declarative evaluators — never `eval()`, `exec()`, or shell subprocesses.
2. **Guaranteed Termination**: Kahn's topological sort rejects cyclic graphs (`422 WORKFLOW_CYCLE_DETECTED`) so workflows cannot enter infinite loops.
3. **Parameterized SQLite Persistence**: All graph and run records are stored using bound SQL parameters.

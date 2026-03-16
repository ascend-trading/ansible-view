Output demo.gif

Set FontSize 14
Set Width 1200
Set Height 650
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set Padding 16

# ── 1. intro ──────────────────────────────────────────────────────────────────
Type "# ansible-view — inspect any Ansible playbook from the terminal"
Sleep 1.5s
Enter
Sleep 500ms

# ── 2. tree mode — minimal example ───────────────────────────────────────────
Type "ansible-view --tree examples/minimal/site.yml"
Sleep 800ms
Enter
Sleep 2s

# ── 3. execution order — minimal example ─────────────────────────────────────
Type "ansible-view --execution examples/minimal/site.yml"
Sleep 800ms
Enter
Sleep 2s

# ── 4. tree mode — full webapp (multi-play, roles, includes) ──────────────────
Type "# multi-play webapp: import_playbook + roles + nested includes"
Sleep 1.2s
Enter
Sleep 300ms
Type "ansible-view --tree examples/webapp/site.yml"
Sleep 800ms
Enter
Sleep 3s

# ── 5. TUI — interactive two-pane view ───────────────────────────────────────
Type "# interactive TUI — navigate the tree and inspect YAML side by side"
Sleep 1.2s
Enter
Sleep 300ms
Type "ansible-view examples/minimal/site.yml"
Sleep 800ms
Enter
Sleep 3s

# navigate down through the tree
Down
Sleep 400ms
Down
Sleep 400ms
Down
Sleep 400ms
Down
Sleep 600ms

# expand a node (Enter or Right)
Right
Sleep 1s
Down
Sleep 400ms
Down
Sleep 600ms

# resize panels
Type "["
Sleep 600ms
Type "["
Sleep 600ms
Type "]"
Sleep 600ms
Type "]"
Sleep 800ms

# quit
Type "q"
Sleep 1s

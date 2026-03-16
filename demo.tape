Output demo.gif

Set FontSize 14
Set Width 1200
Set Height 650
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set Padding 16

# ── 1. --tree: minimal example ────────────────────────────────────────────────
Type "ansible-view --tree examples/minimal/site.yml"
Sleep 600ms
Enter
Sleep 2.5s

# ── 2. --execution: minimal example ──────────────────────────────────────────
Type "ansible-view --execution examples/minimal/site.yml"
Sleep 600ms
Enter
Sleep 2.5s

# ── 3. --tree: full webapp (multi-play, roles, nested includes) ───────────────
Type "ansible-view --tree examples/webapp/site.yml"
Sleep 600ms
Enter
Sleep 3s

# ── 4. TUI: interactive view of the webapp playbook ──────────────────────────
Type "ansible-view examples/webapp/site.yml"
Sleep 600ms
Enter
Sleep 3s

# --- root is visible: 3 import_playbook entries ---
# expand first import_playbook: plays/base.yml
Down
Sleep 400ms
Enter
Sleep 800ms

# expand the play inside it
Down
Sleep 400ms
Enter
Sleep 800ms

# step through pre_tasks, expand it
Down
Sleep 300ms
Down
Sleep 300ms
Enter
Sleep 600ms

# step into the task inside pre_tasks
Down
Sleep 500ms

# back out to role: common — expand it
Down
Sleep 300ms
Enter
Sleep 800ms

# expand tasks/main.yml inside role
Down
Sleep 300ms
Enter
Sleep 700ms

# drill into import_tasks: Install base packages
Down
Sleep 300ms
Enter
Sleep 700ms

# expand packages.yml inside
Down
Sleep 300ms
Enter
Sleep 700ms

# read through the leaf tasks
Down
Sleep 400ms
Down
Sleep 400ms
Down
Sleep 600ms

# collapse packages.yml back up
Enter
Sleep 500ms

# collapse the import_tasks
Up
Sleep 300ms
Enter
Sleep 500ms

# collapse tasks/main.yml
Up
Sleep 300ms
Enter
Sleep 500ms

# collapse role: common
Up
Sleep 300ms
Enter
Sleep 700ms

# --- navigate down to the second import_playbook: webservers ---
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 400ms
Enter
Sleep 800ms

# expand the webservers play
Down
Sleep 300ms
Enter
Sleep 700ms

# navigate down to the nginx role and expand it
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Enter
Sleep 800ms

# expand nginx tasks/main.yml
Down
Sleep 300ms
Enter
Sleep 700ms

# scroll through the nested install + configure tasks
Down
Sleep 300ms
Enter
Sleep 600ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 400ms

# --- switch to execution-order view ---
Type "e"
Sleep 1.5s

# --- toggle debug info on a task ---
Type "d"
Sleep 1.5s

# --- back to hierarchy view ---
Type "e"
Sleep 800ms
Type "d"
Sleep 800ms

# --- resize panels ---
Type "]"
Sleep 500ms
Type "]"
Sleep 500ms
Type "["
Sleep 500ms
Type "["
Sleep 800ms

# quit
Type "q"
Sleep 800ms

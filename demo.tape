Output demo.gif

Set FontSize 14
Set Width 1200
Set Height 650
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set Padding 16

# ── 1. Static tree — quick orientation ────────────────────────────────────────
Type "ansible-view --tree examples/webapp/site.yml"
Sleep 600ms
Enter
Sleep 3s

# ── 2. Launch interactive TUI ─────────────────────────────────────────────────
Type "ansible-view examples/webapp/site.yml"
Sleep 600ms
Enter
Sleep 3s

# Root expanded: 3 import_playbook entries visible. Cursor at root.

# ── Drill into plays/base.yml ─────────────────────────────────────────────────
Down        # → import_playbook: plays/base.yml
Sleep 400ms
Enter       # expand → lazy load → play: Base configuration
Sleep 1s

Down        # → play: Base configuration
Sleep 350ms
Enter       # expand → play sections (pre_tasks, roles, post_tasks)
Sleep 800ms

Down        # → navigate to pre_tasks
Sleep 300ms
Down        # → pre_tasks node
Sleep 300ms
Enter       # expand pre_tasks → Verify supported OS
Sleep 700ms

Down        # → Verify supported OS (right panel: assert source)
Sleep 700ms

# ── Drill into role: common → tasks/main.yml ──────────────────────────────────
Down        # → role: common
Sleep 300ms
Enter       # expand → lazy load → tasks/main.yml
Sleep 1s

Down        # → tasks/main.yml
Sleep 300ms
Enter       # expand → Install base packages, Set system timezone, Configure NTP, Ensure log dir
Sleep 800ms

# ── Drill into import_tasks: Install base packages → packages.yml ─────────────
Down        # → import_tasks: Install base packages
Sleep 350ms
Enter       # expand → lazy load → packages.yml (file node)
Sleep 900ms

Down        # → packages.yml
Sleep 350ms
Enter       # expand → leaf tasks inside packages.yml
Sleep 800ms

Down        # → Update apt cache
Sleep 500ms
Down        # → Install common packages (Debian)
Sleep 500ms
Down        # → Install common packages (RedHat)
Sleep 700ms

# ── Reset tree, navigate to plays/webservers.yml ──────────────────────────────
Type "h"
Sleep 800ms

Down        # → import_playbook: plays/base.yml
Sleep 300ms
Down        # → import_playbook: plays/webservers.yml
Sleep 400ms
Enter       # expand → lazy load → play: Configure web servers
Sleep 1s

Down        # → play: Configure web servers
Sleep 350ms
Enter       # expand → play sections (pre_tasks, roles, tasks, handlers)
Sleep 800ms

Down        # → navigate toward nginx role
Sleep 300ms
Down        # ↓
Sleep 300ms
Down        # ↓
Sleep 300ms
Down        # → role: nginx
Sleep 350ms
Enter       # expand → lazy load → tasks/main.yml
Sleep 1s

# ── Drill into nginx tasks/main.yml ───────────────────────────────────────────
Down        # → tasks/main.yml
Sleep 300ms
Enter       # expand → import_tasks: Install nginx, import_tasks: Configure nginx
Sleep 800ms

# ── Expand import_tasks: Install nginx → install.yml ─────────────────────────
Down        # → import_tasks: Install nginx
Sleep 350ms
Enter       # expand → lazy load → install.yml (file node)
Sleep 900ms

Down        # → install.yml
Sleep 350ms
Enter       # expand → 3 tasks inside install.yml
Sleep 800ms

Down        # → Install nginx package (right panel: apt task source)
Sleep 500ms
Down        # → Install nginx (RedHat)
Sleep 500ms
Down        # → Enable nginx service
Sleep 600ms

# ── Expand import_tasks: Configure nginx → configure.yml ──────────────────────
Down        # → import_tasks: Configure nginx
Sleep 400ms
Enter       # expand → lazy load → configure.yml (file node)
Sleep 900ms

Down        # → configure.yml
Sleep 350ms
Enter       # expand → 4 tasks inside configure.yml
Sleep 800ms

Down        # → Create nginx config directory
Sleep 500ms
Down        # → Deploy nginx main config (right panel: template source)
Sleep 500ms
Down        # → Deploy virtual host config
Sleep 500ms
Down        # → Remove default nginx site
Sleep 700ms

# ── Toggle execution-order view ───────────────────────────────────────────────
Type "e"
Sleep 1.5s

# ── Toggle debug metadata panel ───────────────────────────────────────────────
Type "d"
Sleep 1.5s

# ── Back to hierarchy, dismiss debug ──────────────────────────────────────────
Type "e"
Sleep 700ms
Type "d"
Sleep 700ms

# ── Resize panels ─────────────────────────────────────────────────────────────
Type "]"
Sleep 400ms
Type "]"
Sleep 400ms
Type "["
Sleep 400ms
Type "["
Sleep 600ms

# ── Quit ──────────────────────────────────────────────────────────────────────
Type "q"
Sleep 800ms

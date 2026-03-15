# ansible-view

Inspect and navigate Ansible playbook execution flow from the terminal.

```
ansible-view site.yml
```

No more opening five files to understand what a playbook actually does.
`ansible-view` resolves roles, includes, handlers, and imported playbooks
into a single navigable view — with an interactive TUI, static tree output,
and execution-order numbering.

---

## Installation

### Clone and run — no permissions required (recommended on shared systems)

The simplest path on any system, including shared or root-owned Ansible
environments. No write access to any existing Python installation needed:

```bash
git clone https://github.com/ascend-trading/ansible-view.git
cd ansible-view
./bin/ansible-view /path/to/your/playbook.yml
```

The wrapper creates a self-contained `.venv` inside the cloned directory on
first run and never touches your system Python or existing virtualenv.
Subsequent runs are instant.

Set an alias so you can call it from anywhere:

```bash
echo 'alias ansible-view="/path/to/ansible-view/bin/ansible-view"' >> ~/.bashrc
source ~/.bashrc
ansible-view site.yml
```

### Into your own virtualenv

Create a dedicated virtualenv for `ansible-view` so it doesn't conflict with
your existing Ansible installation:

```bash
python3 -m venv ~/ansible-view-env
~/ansible-view-env/bin/pip install git+https://github.com/ascend-trading/ansible-view.git
~/ansible-view-env/bin/ansible-view site.yml
```

Or alias it:
```bash
echo 'alias ansible-view="$HOME/ansible-view-env/bin/ansible-view"' >> ~/.bashrc
source ~/.bashrc
```

### Into your existing Ansible virtualenv

Only use this if your virtualenv is writable by your user. If you get a
**Permission denied** error (e.g. the venv is at `/opt/...` or owned by root),
use one of the options above instead.

```bash
source /path/to/your/ansible-venv/bin/activate
pip install git+https://github.com/ascend-trading/ansible-view.git
```

### Via pipx (if available)

[pipx](https://pipx.pypa.io) installs CLI tools in fully isolated
environments. If `pipx` isn't installed, see
[pipx installation](https://pipx.pypa.io/stable/installation/).

```bash
pipx install git+https://github.com/ascend-trading/ansible-view.git
ansible-view site.yml
```

> `ANSIBLE_CONFIG`, `ANSIBLE_ROLES_PATH`, and all other Ansible env vars
> work regardless of which install method you use — they're read from your
> shell environment at runtime.

### From a specific release

```bash
pip install https://github.com/ascend-trading/ansible-view/releases/download/v0.1.0/ansible_view-0.1.0-py3-none-any.whl
```

---

## Usage

```bash
# Interactive TUI — navigate with arrow keys
ansible-view site.yml

# Print full hierarchy to stdout
ansible-view site.yml --tree

# Numbered execution order
ansible-view site.yml --execution

# Debug metadata (conditions, vars, tags, line numbers)
ansible-view site.yml --execution --debug

# Tool version
ansible-view --version
```

See **[examples/README.md](examples/README.md)** for a full walkthrough with
sample output, all four modes explained, and ready-to-run playbooks in
`examples/minimal/` and `examples/webapp/`.

---

## TUI controls

| Key | Action |
|---|---|
| `↑` `↓` | Navigate |
| `Enter` / `Space` | Expand / collapse node |
| `e` | Toggle execution order view |
| `h` | Toggle hierarchy view |
| `d` | Toggle debug metadata panel |
| `[` / `]` | Narrow / widen the tree panel |
| `q` | Quit |

The right panel shows the selected node's type, source file, and line
number. When a file is selected, the full YAML source is displayed with
syntax highlighting and the relevant line highlighted. Press `d` to also
show per-task debug metadata (conditions, variables, tags, loop, notify).

---

## Features

- Resolves `roles`, `include_tasks`, `import_tasks`, `include_role`,
  `import_role`, `include_playbook`, `import_playbook`, and `handlers`
- Execution order with hierarchical dot-notation numbering (`1`, `1.1`, `2.1.3`)
- Debug mode: `when`, `tags`, `register`, `loop`, `notify`, `vars`,
  source file and line number
- Lazy loading — large playbooks only parse files when you expand them
- Inline error nodes for missing files and unresolved roles
- Circular include detection
- Respects `ansible.cfg`, `ANSIBLE_ROLES_PATH`, `ANSIBLE_COLLECTIONS_PATHS`,
  and all standard Ansible config sources
- Uses `ansible-core`'s config manager when available

---

## Development

```bash
make dev                  # create venv with dev dependencies
make test                 # run tests with coverage
make lint                 # ruff lint check
make format               # auto-format source files
make typecheck            # mypy type check
make check                # lint + typecheck + tests (full CI)
make clean                # remove venv and cache files
```

### CI (GitHub Actions)

Runs on every push and pull request:

- **Test matrix**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Lint & format**: ruff
- **Type check**: mypy

Releases are published to PyPI automatically on `v*.*.*` tags via trusted
publishing (no API token required — configure the `pypi` environment in
GitHub repo settings).

---

## Author

**Aime Nishimwe**

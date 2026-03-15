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

### Into your existing Ansible environment (recommended)

If you already have Ansible installed, install `ansible-view` into the same
environment so it shares the same `ansible-core` and config:

```bash
# If ansible is in a virtualenv (most common)
source /path/to/your/ansible-venv/bin/activate
pip install ansible-view

# If ansible is installed via pip at the user level
pip install --user ansible-view

# If ansible is installed via pipx
pipx inject ansible ansible-view
```

Then run it from anywhere against any playbook:

```bash
ansible-view site.yml
ansible-view /srv/ansible/playbooks/deploy.yml
```

### As an isolated tool (pipx)

[pipx](https://pipx.pypa.io) installs CLI tools in isolated environments so
they don't interfere with your system Python or existing packages:

```bash
pipx install ansible-view
ansible-view site.yml
```

> `ansible-view` requires `ansible-core` as a dependency. pipx will install
> it into the isolated environment automatically. If you want it to use your
> system Ansible config, set `ANSIBLE_CONFIG` or `ANSIBLE_ROLES_PATH` as
> you normally would — these are read from the environment regardless of
> where `ansible-view` is installed.

### Clone and run (no install at all)

For contributing or trying it out without touching your Python environment:

```bash
git clone https://github.com/aimev65/ansible-view
cd ansible-view
./bin/ansible-view examples/webapp/site.yml
```

The wrapper auto-creates a local `.venv` and installs dependencies on first
run. Subsequent runs are instant. Use `make setup` for the same result.

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

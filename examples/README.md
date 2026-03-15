# ansible-view — Quickstart Guide

`ansible-view` lets you inspect any Ansible playbook's full execution
flow without opening multiple files. This guide walks through every
mode using the examples in this directory.

---

## Setup

The quickest path — no manual venv steps:

```bash
git clone https://github.com/aimev65/ansible-view
cd ansible-view
./bin/ansible-view examples/minimal/site.yml
```

The wrapper auto-creates `.venv` and installs dependencies on first run.

Alternatively, use `make`:

```bash
make setup
source .venv/bin/activate
ansible-view examples/minimal/site.yml
```

Or install from PyPI:

```bash
pip install ansible-view
```

---

## Examples in this directory

| Path | What it demonstrates |
|---|---|
| `minimal/site.yml` | Single play — tasks, handlers, block/rescue/always, include_tasks |
| `webapp/site.yml` | Multi-play — import_playbook, roles, pre/post tasks, nested includes |

---

## Mode 1 — Interactive TUI (default)

The default mode opens a navigable terminal interface.

```bash
ansible-view examples/minimal/site.yml
```

```
PLAYBOOK: site.yml
└── play: Install and start web server
    ├── gather_facts
    ├── tasks
    │   ├── Install nginx
    │   ├── block: Deploy config with error handling
    │   │   ├── Write nginx config
    │   │   ├── Validate config
    │   │   ├── rescue
    │   │   │   └── Restore backup config
    │   │   └── always
    │   │       └── Log config status
    │   └── include_tasks: tasks/firewall.yml
    └── handlers
        ├── handler: restart nginx
        └── handler: reload nginx
```

**Navigation keys:**

| Key | Action |
|---|---|
| `↑` `↓` | Move between nodes |
| `Enter` | Expand a section |
| `Space` | Collapse a section |
| `e` | Switch to execution order view |
| `h` | Switch back to hierarchy view |
| `d` | Toggle debug metadata panel |
| `[` / `]` | Narrow / widen tree panel |
| `q` | Quit |

The right-hand panel shows the selected node's file location and type.
Press `d` to expand it into full debug metadata.

---

## Mode 2 — Tree (static output)

Prints the full hierarchy to stdout. Good for scripting, grepping, or
piping into other tools.

```bash
ansible-view examples/minimal/site.yml --tree
```

```
PLAYBOOK: site.yml
└── play: Install and start web server
    ├── gather_facts
    ├── tasks
    │   ├── Install nginx
    │   ├── block: Deploy config with error handling
    │   └── include_tasks: tasks/firewall.yml
    └── handlers
        ├── handler: restart nginx
        └── handler: reload nginx
```

Try the full webapp example to see multi-play resolution:

```bash
ansible-view examples/webapp/site.yml --tree
```

This resolves all three `import_playbook` references and walks into
each role's task files automatically.

---

## Mode 3 — Execution order

Shows tasks numbered in the exact order Ansible would run them.

```bash
ansible-view examples/minimal/site.yml --execution
```

```
PLAY 1: Install and start web server

  1 gather_facts
  2 Install nginx
  3 block: Deploy config with error handling
    3.1 Write nginx config
    3.2 Validate config
    3.3 rescue
      3.3.1 Restore backup config
    3.4 always
      3.4.1 Log config status
  4 include_tasks: tasks/firewall.yml
    4.1 Allow HTTP through firewall
    4.2 Enable UFW
```

Try it on the webapp (multiple plays with roles):

```bash
ansible-view examples/webapp/site.yml --execution
```

---

## Mode 4 — Debug metadata

Append `--debug` to any mode to reveal per-task metadata.

```bash
ansible-view examples/minimal/site.yml --execution --debug
```

```
PLAY 1: Install and start web server

  1 gather_facts

  2 Install nginx
    file: examples/minimal/site.yml:16
    module: apt
    args:
      name: nginx
      state: present
    when: ansible_os_family == "Debian"
    tags: install
    vars: ansible_os_family, package_name
    register: nginx_install
    notify: restart nginx

  3 block: Deploy config with error handling
    ...
```

Debug also works with `--tree`:

```bash
ansible-view examples/webapp/site.yml --tree --debug
```

In the **interactive TUI**, press `d` at any time to toggle the debug
panel for the currently selected node.

---

## Pointing at your own playbooks

`ansible-view` respects your existing Ansible configuration:

```bash
# Playbook in current directory — roles resolved from ./roles
ansible-view site.yml

# Playbook with a custom roles path
ANSIBLE_ROLES_PATH=/srv/ansible/roles ansible-view site.yml

# Ansible config in a non-standard location
ANSIBLE_CONFIG=/path/to/ansible.cfg ansible-view site.yml
```

Role paths, collections paths, and all standard Ansible config sources
(`ansible.cfg`, `~/.ansible.cfg`, `ANSIBLE_ROLES_PATH`) are resolved
automatically using `ansible-core`'s own config manager when available.

---

## Understanding the output

### Node types

| Symbol / label | Meaning |
|---|---|
| `play: <name>` | A play (`- name: ...  hosts: ...`) |
| `gather_facts` | Implicit gather_facts step |
| `role: <name>` | Role referenced via `roles:` or `include_role:` |
| `include_tasks: <file>` | Dynamic task include |
| `import_tasks: <file>` | Static task import |
| `block: <name>` | Block with optional rescue/always |
| `handler: <name>` | Handler (runs when notified) |
| `import_playbook: <file>` | Included playbook |
| `ERROR: ...` | File or role could not be resolved |

### Execution numbering

Numbers follow hierarchical dot notation mirroring Ansible's runtime:

```
1         ← first executable in the play
2         ← second executable
2.1       ← first child of executable 2 (e.g. a role task)
2.2       ← second child
3         ← third executable at play level
```

`section` nodes (`tasks`, `pre_tasks`, `handlers`) are structural
groupings — they don't count as executables and don't get numbers.

---

## Example structures

### minimal/

```
minimal/
├── site.yml          ← single play with tasks, block, and include_tasks
└── tasks/
    └── firewall.yml  ← included task file
```

### webapp/

```
webapp/
├── ansible.cfg
├── site.yml                    ← imports all three plays
├── plays/
│   ├── base.yml                ← common role + pre/post tasks
│   ├── webservers.yml          ← nginx role + ssl include
│   └── appservers.yml          ← app role + block/rescue
├── roles/
│   ├── common/
│   │   ├── tasks/
│   │   │   ├── main.yml        ← imports packages.yml
│   │   │   └── packages.yml
│   │   └── handlers/main.yml
│   ├── nginx/
│   │   ├── tasks/
│   │   │   ├── main.yml        ← imports install.yml, configure.yml
│   │   │   ├── install.yml
│   │   │   └── configure.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app/
│       ├── tasks/
│       │   ├── main.yml        ← imports deploy.yml, migrate.yml
│       │   ├── deploy.yml
│       │   └── migrate.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
└── tasks/
    ├── firewall.yml
    ├── ssl.yml
    └── monitoring.yml
```

---

**Author:** Aime Nishimwe

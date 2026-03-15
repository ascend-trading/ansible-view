# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.1] - 2026-03-16

### Fixed
- Resolve FQCN task actions and fallback include path to playbook root

### Changed
- Install instructions updated to use `pip install git+...` (PyPI publishing pending)
- Clarified install docs for shared/root-owned Ansible environments

## [0.1.0] - 2026-03-15

### Added
- Interactive TUI (`ansible-view site.yml`) with two-pane layout: navigable tree on the left, full YAML source with syntax highlighting and line highlighting on the right
- `[` / `]` keybindings to resize tree / detail panels at runtime
- `--tree` mode: print full playbook hierarchy to stdout
- `--execution` mode: numbered execution-order output with hierarchical dot-notation (`1`, `1.1`, `2.1.3`)
- `--debug` flag: per-node metadata (module, args, `when`, `tags`, `register`, `loop`, `notify`, `vars`, source file + line)
- Resolves `roles`, `include_tasks`, `import_tasks`, `include_role`, `import_role`, `include_playbook`, `import_playbook`, and `handlers`
- Lazy loading — files are only parsed when a node is expanded
- Circular include detection
- Inline error nodes for missing files and unresolvable roles
- Full `ansible.cfg` / `ANSIBLE_ROLES_PATH` / `ANSIBLE_COLLECTIONS_PATHS` integration; uses `ansible-core`'s config manager when available
- `bin/ansible-view` bootstrap wrapper — auto-creates `.venv` and installs on first run (zero manual setup after `git clone`)
- `Makefile` with `setup`, `dev`, `test`, `lint`, `format`, `typecheck`, `check`, `clean` targets
- Example playbooks: `examples/minimal/` (single play, block/rescue/always, include_tasks) and `examples/webapp/` (multi-play, import_playbook, roles, nested includes)
- Quickstart guide at `examples/README.md`
- GitHub Actions CI: test matrix (Python 3.9–3.13), ruff lint + format, mypy
- GitHub Actions release: build sdist + wheel, GitHub Release, PyPI trusted publishing (gated on CI passing)
- 131 tests, 100% code coverage across all 22 modules

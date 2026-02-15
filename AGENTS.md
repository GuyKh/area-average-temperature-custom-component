# AI Agent Instructions - Area Average Temperature Custom Component

This document provides guidance for AI coding agents working on this Home Assistant custom integration project.

## Project Overview

This is a Home Assistant custom component that creates sensors showing the average temperature for each configured area based on multiple temperature sensors in that area.

**Integration details:**
- **Domain:** `area_average_temperature`
- **Title:** Area Average Temperature
- **Repository:** GuyKh/area-average-temperature-custom-component

**Key directories:**
- `custom_components/area_average_temperature/` - Main integration code
- `config/` - Home Assistant configuration for local testing
- `.github/workflows/` - CI/CD workflows

## Tech Stack

- **Python**: 3.12+
- **Home Assistant**: 2025.1.4+
- **Linting**: ruff (with Home Assistant rules)
- **Type Checking**: mypy

## Code Structure

```
custom_components/area_average_temperature/
├── __init__.py          # Integration entry point (async_setup_entry, async_unload_entry)
├── const.py             # Constants and DOMAIN definitions
├── config_flow.py       # UI configuration flow
├── coordinator.py       # DataUpdateCoordinator - manages temperature calculations
├── data.py              # Shared data types and ConfigEntry
├── entity.py            # Base entity class
├── sensor.py            # Sensor platform
└── translations/        # Translation files
    └── en.json
```

## Local Development

**Always use the project's scripts** — do NOT craft your own `hass`, `pip`, or similar commands. The scripts handle environment setup correctly.

**Setup:**
```bash
./scripts/setup  # Install dependencies
```

**Start Home Assistant:**
```bash
./scripts/develop  # Start HA development environment
```

**Debugging:**
Enable debug logging in `config/configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.area_average_temperature: debug
```

**Reading logs:**
- Terminal where `./script/develop` runs
- `config/home-assistant.log`

## Workflow

### Starting New Work

**When starting a new task, always ask the user first:**
- Should I switch to `main` branch and rebase?
- Or should I work from the current branch?

Then checkout a new feature branch before beginning work. Never work directly on `main` or stale branches.

### Branch Naming Convention
- Features: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`

## Code Style

**Python:**
- 4 spaces indentation
- 120 character lines
- Double quotes for strings
- Full type hints (mypy strict)
- Async for all I/O operations
- Follow ruff rules from `.ruff.toml`

**Validation commands:**
```bash
./scripts/lint        # Run ruff linter (auto-fixes where possible)
./scripts/typecheck   # Run mypy type checker
```

## Key Patterns

### Integration Setup
- Uses `ConfigEntry` for UI-based configuration
- Supports multiple area configurations (one entry per installation)
- Registers `PLATFORMS`: `sensor`

### Coordinator Pattern
- `AreaAverageTemperatureCoordinator` extends `DataUpdateCoordinator`
- Calculates average temperatures from multiple sensors
- Uses state change listeners instead of polling (`update_interval=None`)
- Manages sensor subscription lifecycle
- Entities → Coordinator → State Listeners (never skip layers)
- Data structure: `{"Area Name": average_temperature_value}`

### Entity Pattern
- Base `AreaAverageTemperatureEntity` class in `entity.py`
- Entities inherit from `CoordinatorEntity[AreaAverageTemperatureCoordinator]`
- Read from `coordinator.data`, never query state directly
- Use entity descriptions for static metadata

### Config Flow
- Implement in `config_flow.py`
- Support user setup with area/sensor selection
- Options flow for reconfiguration
- Always set `unique_id` for entries
- **Current Issue**: Options flow uses JSON input which needs improvement

## Project-Specific Rules

### Temperature Averaging Concepts
- **Areas**: Named spaces (e.g., "Living Room", "Bedroom")
- **Temperature Sensors**: Any sensor with `device_class: temperature`
- **Average Calculation**: Simple arithmetic mean of valid temperature values
- **State Tracking**: Updates immediately when any sensor changes (no polling)

### Constants (from `const.py`)
- `DOMAIN = "area_average_temperature"`
- `CONF_AREAS = "areas"`

### Data Storage
- Config stored in `config_entry.data` and `config_entry.options`
- Format: `{"areas": {"Area Name": ["sensor.id1", "sensor.id2"]}}`
- Runtime data in `entry.runtime_data` (AreaAverageTemperatureData)

## Common Tasks

### Adding a New Sensor Type
1. Add constants to `const.py` if needed
2. Add sensor logic in `sensor.py`
3. Follow existing sensor patterns
4. Add full type annotations (mypy strict)

### Modifying Config Flow
1. Update `config_flow.py`
2. Ensure backward compatibility with existing entries
3. Add translations in `translations/en.json`
4. Test both initial setup and options flow

### Handling Sensor State Changes
1. Sensors are tracked via `async_track_state_change_event`
2. Updates trigger coordinator refresh
3. Coordinator calculates new averages
4. Entities update automatically via coordinator callback

## Validation

**Before committing, run:**
```bash
./scripts/lint        # Auto-format and fix linting issues
./scripts/typecheck   # Type checking
```

**Configured tools:**
- **Ruff** - Fast Python linter and formatter
- **mypy** - Static type checker (strict mode)

### Error Recovery Strategy

**When first attempt validation fails:**
1. **First attempt** - Fix the specific error reported by the tool
2. **Second attempt** - If it fails again, reconsider your approach
3. **Third attempt** - If still failing, stop and ask for clarification

**After ~10 file reads, you must either:**
- Proceed with implementation based on available context
- Ask the developer specific questions about what's unclear

## Testing

Tests are run via GitHub Actions workflows:
- `.github/workflows/lint.yml` - Ruff linting
- `.github/workflows/validate.yml` - Full validation (ruff + mypy)

### Manual Testing
1. Add mock temperature sensors (see `mock_sensors.yaml`)
2. Configure areas through the UI
3. Verify sensors are created and update when source sensors change

## Breaking Changes

**Always warn the developer before making changes that:**
- Change entity IDs or unique IDs (users' automations will break)
- Modify config entry data structure (existing installations will fail)
- Change state values or attributes format (dashboards affected)
- Remove or rename config options

**How to warn:**
> "This change will modify the entity ID format. Existing users' automations and dashboards will break. Should I proceed, or would you prefer a migration path?"

## Quality Standards

**Follow Home Assistant patterns:**
- Use type annotations (mypy strict)
- Follow ruff rules
- Add docstrings to public functions
- Use Home Assistant constants from `homeassistant.const`
- Implement proper error handling
- Use `async_redact_data()` for sensitive data in diagnostics

## Additional Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [mypy Configuration](https://mypy.readthedocs.io/)
- [Config Entries](https://developers.home-assistant.io/docs/config_entries_index)
- [Entity Selectors](https://developers.home-assistant.io/docs/selector)

# PRODUCT-SPEC — Asimov Sim Lab

    ## One-line thesis
    Turn the public Asimov v1 MuJoCo release into a serious developer-facing inspection, validation, and capture tool before any controller or policy work begins.

    ## Product shape
    CLI-first Python package with MuJoCo viewer integration and optional local UI panels.

    ## Repo strategy
    uv-managed Python package with CLI commands for inspect/validate/open/capture, schema-backed preset data, and CI-grade contract validation.

    ## Primary source assets
    - `sim-model/xmls/asimov.xml`
- `sim-model/assets/meshes/*.STL`
- `sim-model/README.md`

    ## Users
    - robotics developers and contributors working around the public Asimov release
    - technical evaluators who need proof that the project is grounded in real upstream assets
    - future collaborators who need stable contracts before they write code

    ## MVP promise
    - the repo should define a truthful, testable, implementation-ready contract
    - the repo should not overstate what is already built
    - the first implementation should stay narrow and evidence-producing

    ## Phase-2 lock note
    This document captures the full product direction. It is not the same thing as the next implementation slice.

    The currently locked implementation truth lives in:
    - `docs/spec/MANIFEST-CONTRACT.md`
    - `docs/spec/RESULT-SCHEMA-CONTRACT.md`
    - `docs/spec/CLI-COMMAND-SPEC.md`
    - `docs/spec/PROFILE-CONTRACT.md`
    - `docs/spec/FIRST-THREE-SCENARIOS-BUILD-PACK.md`

    In plain terms:
    - `open` and `capture` remain product-direction commands
    - the next implementation pass is work pack 1 only, starting with `doctor` and asset-manifest truth

    ## Non-goals for this phase
    - no premature full product implementation
    - no marketing-site fluff
    - no fake benchmark/demo theater
    - no claims that exceed upstream data quality or scope

    ## Demo target
    Open the Asimov model locally, print a model contract, validate presets, and emit reproducible screenshots.

    ## Risks to manage early
    - upstream source assets can drift
    - licensing / attribution and redistribution boundaries must stay explicit
    - UI scope can explode if contracts are not locked first
    - the repo must remain useful even before secondary UX surfaces exist

    ## Acceptance criteria for phase 1
    - repo exists privately on GitHub
    - local clone exists
    - uv project scaffold is coherent
    - product/spec docs exist and agree with each other
    - RFC set covers architecture, contracts, validation, evidence, and release posture
    - implementation plan is concrete enough that coding becomes mostly mechanical

    ## Upstream PRD snapshot

    ```md
    # PRD: Asimov Sim Lab

## Summary

Asimov Sim Lab is an external developer tool and showcase for inspecting, validating, and experimenting with the Asimov v1 MuJoCo model. It provides a one-command local environment, model contract reports, joint sliders, preset poses, screenshots, and small control examples built around `sim-model/xmls/asimov.xml`.

The product should help robotics developers understand the public simulation model before writing controllers or training policies.

## Problem

The Asimov v1 repository includes a MuJoCo model and mesh assets, but a user still needs to manually inspect the XML or open the viewer to understand the model:

- Joint names, actuator names, torque ranges, sensors, and mesh references are not surfaced as a contract.
- Users need quick ways to inspect joint limits, axis signs, passive joints, and default poses.
- Screenshots or reproducible issue reports require manual setup.
- Beginners may not know whether their local MuJoCo environment loaded the model correctly.
- Contributors need a focused harness for validating simulator-facing changes.

## Goals

- Provide a one-command local launch path for the Asimov v1 MuJoCo model.
- Generate a model contract report from MJCF.
- Provide an interactive joint control UI.
- Provide preset poses for quick inspection.
- Capture screenshots or short videos for issues, docs, and demos.
- Validate mesh references, joint references, actuators, and sensors.
- Keep the tool useful without requiring policy training infrastructure.

## Non-Goals

- Do not train a locomotion policy in MVP.
- Do not claim physical fidelity beyond the upstream model.
- Do not modify the upstream MJCF automatically.
- Do not implement a full robotics simulator platform.
- Do not require GPU acceleration for the base inspection workflow.

## Target Users

- Robotics developers exploring Asimov v1.
- Contributors validating MJCF and mesh changes.
- Policy researchers preparing control experiments.
- Community users creating screenshots, demos, or bug reports.

## Source Assets

Primary inputs:

- `sim-model/xmls/asimov.xml`
- `sim-model/assets/meshes/*.STL`
- `sim-model/README.md`

Optional generated inputs:

- `model_contract.json`
- screenshot outputs
- pose preset files
- rendered preview thumbnails

## Product Requirements

### One-Command Launch

Status:
- product direction, not phase-3 day-one scope

- Provide a CLI command:

```bash
asimov-sim-lab open
```

- It should:
  - locate the Asimov v1 sim assets
  - verify mesh references
  - open the MuJoCo viewer
  - print a short model summary

### Model Contract Report

- Parse the MJCF and output:
  - model name
  - mesh count
  - body count
  - joint count
  - actuator count
  - sensor count
  - joint names and ranges
  - actuator names, joint refs, and control ranges
  - passive joints
  - missing files or invalid references

- Support:

```bash
asimov-sim-lab inspect --json
asimov-sim-lab inspect --markdown
```

### Joint Inspector UI

- Provide an interactive UI with:
  - joint sliders
  - limit markers
  - neutral/reset action
  - preset pose selector
  - body and actuator metadata panel
- Sliders must clamp to MJCF joint ranges.
- Passive joints should be visually distinguished from motorized joints.

### Preset Poses

MVP preset poses:

- neutral
- crouch
- left arm raise
- right arm raise
- toe flex
- seated inspection pose, if physically plausible in the model

Each preset should be stored as data, not hardcoded only in UI logic.

### Capture Tools

Status:
- deferred beyond the first implementation slice

- Capture screenshot from a named camera.
- Save image output with model commit metadata.
- Later: record short videos of preset transitions.

Example:

```bash
asimov-sim-lab capture --camera side_camera --pose neutral --output neutral-side.png
```

### Validation

The tool must validate:

- all MJCF mesh files exist
- all actuator joint refs exist
- all sensor refs exist where applicable
- all joint ranges are parseable
- all preset poses reference existing joints
- all preset values stay within joint limits

## UX Requirements

- First screen should show the loaded robot, joint controls, and model status.
- Use dense, developer-oriented panels rather than a landing page.
- Make model status obvious:
  - loaded
  - missing mesh
  - invalid actuator reference
  - preset out of range
- Use clear labels matching MJCF joint and actuator names.
- Provide copyable reports for GitHub issues.

## Data Model

```python
@dataclass
class JointInfo:
    name: str
    joint_type: str
    range: tuple[float, float] | None
    axis: tuple[float, float, float] | None
    body: str
    passive: bool

@dataclass
class ActuatorInfo:
    name: str
    joint: str
    ctrlrange: tuple[float, float] | None

@dataclass
class ModelContract:
    model_name: str
    meshes: list[str]
    joints: list[JointInfo]
    actuators: list[ActuatorInfo]
    sensors: list[str]
```

## Technical Architecture

Recommended stack:

- Python package for CLI, MJCF parsing, validation, and MuJoCo launch.
- `mujoco` Python package for simulation and viewer launch.
- Optional Streamlit, NiceGUI, or lightweight local web UI for joint sliders.
- `pytest` for parser, validator, and preset tests.
- GitHub Actions with a headless validation path.

Repository structure:

```text
asimov-sim-lab/
├── src/
│   └── asimov_sim_lab/
│       ├── cli.py
│       ├── assets.py
│       ├── inspect.py
│       ├── presets.py
│       ├── validation.py
│       └── viewer.py
├── presets/
│   ├── neutral.json
│   ├── crouch.json
│   └── arm_raise.json
├── tests/
└── README.md
```

## MVP Scope

1. CLI package with `doctor`, `inspect`, and `validate`.
2. Asset locator that supports a local `asimov-v1` checkout path.
3. Model contract generation.
4. Mesh, actuator, sensor, and preset validation.
5. Basic preset pose files.
6. README with one-command launch and validation examples.

## First implementation slice

Before the broader MVP lands, the next shipped slice is narrower:

1. asset-root resolution
2. manifest-backed `doctor`
3. tiny synthetic fixtures proving typed failures

`open` and `capture` are intentionally deferred until the source-contract path is stable.

## V1 Scope

- `open` command for local viewer launch.
- Joint slider UI.
- Screenshot capture by camera and pose.
- Short video capture of pose transitions.
- Web-hosted report viewer for `model_contract.json`.
- GitHub issue bundle generation with contract report and screenshot.

## Success Metrics

- A user can validate the model in one command.
- A user can inspect all joints and actuators without reading the MJCF manually.
- Preset poses are validated against joint limits in CI.
- Missing mesh and invalid joint references produce clear actionable errors.
- A screenshot for a named camera can be generated reproducibly.

## Validation Plan

- Unit test MJCF parsing against the current Asimov XML.
- Unit test missing mesh and invalid actuator fixtures.
- Unit test preset values against joint ranges.
- Run `asimov-sim-lab inspect --json` in CI.
- Run a headless MuJoCo model load test if the CI environment supports it.
- Keep viewer launch as a local smoke test when headless rendering is unavailable.

## Risks

- MuJoCo viewer behavior can vary by OS and graphics stack.
- Headless rendering may require extra CI dependencies.
- Users may interpret preset poses as validated physical motions.
- The upstream model may change joint names or ranges.
- Bundling mesh assets directly may create large external releases.

## Open Questions

- Should the first release require a local clone of `asimov-v1`, or download release assets automatically?
- Should the UI be desktop-native, browser-based, or CLI-first?
- Should screenshots use MuJoCo cameras only, or also custom camera presets?
- Should model reports include mass/inertia summaries in MVP?
    ```

# PyMix - Elixir Dependency Automation Tool

<p align="center">
  <img src="PyMix_NoBg.png" alt="PyMix Logo" width="250">
</p>


**PyMix** is a lightweight command-line tool designed to simplify the **management of dependencies** in Elixir projects using Mix. While Mix handles version resolution and dependency conflicts, PyMix enhances automation, making it easier to **add, remove, and fetch** dependency information **without manual edits**.

## Features
- Fetch detailed information on **Hex packages**
- Add new dependencies to `mix.exs` effortlessly
- Remove dependencies cleanly from `mix.exs` and the deps directory
- Automatically run `mix deps.get` and `mix deps.clean` when necessary

## Installation
Ensure you have **Python 3.8+** installed. Clone the repository and navigate to the directory:

```sh
# Clone the repository
git clone https://github.com/yourusername/pymix.git
cd pymix
```

## Usage

> Make sure you are in the `root dir` of your Elixir project & `mix.exs` exists on the same level.

- PyMix needs an Elixir project with `mix.exs` to work.
- PyMix can be added to the system path for easy access.

### Fetch Package Info
Retrieve information about one or more Hex packages:
```sh
python pymix.py --pkg-info ecto
python pymix.py --pkg-info ecto_sql postgrex
```

### Add Dependencies
Add dependencies to `mix.exs` (automatically fetching the latest version unless specified):
```sh
python pymix.py --pkg-add ecto ecto_sql
python pymix.py --pkg-add postgrex=0.20.0
```

### Remove Dependencies
Remove dependencies from `mix.exs` and clean them from the project:
```sh
python pymix.py --pkg-rm ecto ecto_sql
```

## How It Works
1. **Validates** `mix.exs` before making any modifications.
2. **Prevents duplicates** when adding dependencies.
3. **Edits `mix.exs`** to insert or remove dependencies.
4. **Runs Mix commands**:
   - `mix deps.get` after adding dependencies.
   - `mix deps.clean <package>` when removing dependencies.

## Why Use PyMix?
- Eliminates the need to manually edit `mix.exs`
- Reduces errors when managing dependencies
- Saves time with automation

## License
PyMix is open-source under the MIT License. Contributions welcome!

---
_Enhance your Elixir workflow with PyMix!_
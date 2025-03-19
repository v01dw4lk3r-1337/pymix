import subprocess
import argparse
import os
import sys
import re
import threading
from visuals import *  # Import colors & loader

MIX_FILE = "mix.exs"  # Path to the mix.exs file

def check_mix_file():
    """Ensure mix.exs exists and is error-free."""
    if not os.path.exists(MIX_FILE):
        print(f"{BOLD}{RED}ERROR:{RESET} mix.exs not found.", file=sys.stderr)
        sys.exit(1)
    
    try:
        subprocess.run(["mix", "compile", "--dry-run"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        print(f"{BOLD}{RED}ERROR:{RESET} mix is errored:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def fetch_pkg_info(pkg):
    """Fetch package info using `mix hex.info <pkg>` and return parsed details."""
    stop_event = threading.Event()
    loader_thread = threading.Thread(target=spinning_cursor, args=(stop_event,))
    loader_thread.start()

    try:
        result = subprocess.run(["mix", "hex.info", pkg], capture_output=True, text=True, check=True)
        output = result.stdout.strip()

        stop_event.set()
        loader_thread.join()

        if not output:
            print(f"{BOLD}{RED}ERROR:{RESET} No information found for '{pkg}'", file=sys.stderr)
            return None

        # Extract details
        config = re.search(r"Config: ({.*?})", output)
        releases_match = re.search(r"Releases:\s*(.*)", output)
        licenses = re.search(r"Licenses:\s*(.*)", output)
        github = re.search(r"GitHub:\s*(https://[^\s]+)", output)

        # Handle cases where no releases are found
        all_versions = []
        valid_versions = []
        if releases_match:
            all_versions = [v.strip() for v in releases_match.group(1).split(",")] if releases_match.group(1) else []
            valid_versions = [v for v in all_versions if "(retired)" not in v]

        latest_version = valid_versions[0] if valid_versions else None

        return {
            "description": output.split("\n")[0],
            "config": config.group(1) if config else None,
            "latest_version": latest_version,
            "all_versions": valid_versions,  # Return all versions
            "license": licenses.group(1) if licenses else None,
            "github": github.group(1) if github else None,
        }
    
    except subprocess.CalledProcessError:
        stop_event.set()
        loader_thread.join()
        print(f"{BOLD}{RED}ERROR:{RESET} Package '{pkg}' not found.", file=sys.stderr)
        return None

def get_pkg_info(packages):
    """Display package details for each package in `packages`."""
    for pkg in packages:
        print(f"\n{BOLD}{CYAN}Fetching info for package: {pkg}{RESET}\n")
        pkg_info = fetch_pkg_info(pkg)
        if not pkg_info:
            continue

        print(f"{BOLD}{YELLOW}Description:{RESET} {pkg_info['description']}")
        if pkg_info["config"]:
            print(f"{BOLD}{YELLOW}Config:{RESET} {pkg_info['config']}")
        if pkg_info["latest_version"]:
            print(f"{BOLD}{YELLOW}Latest Release:{RESET} {pkg_info['latest_version']}")
        if pkg_info["all_versions"]:
            print(f"{BOLD}{YELLOW}All Releases:{RESET} {', '.join(pkg_info['all_versions']) if pkg_info['all_versions'] else 'None'}")
        if pkg_info["license"]:
            print(f"{BOLD}{YELLOW}License:{RESET} {pkg_info['license']}")
        if pkg_info["github"]:
            print(f"{BOLD}{YELLOW}GitHub Repo:{RESET} {pkg_info['github']}")

        print("\n" + "=" * 50)

def read_existing_deps():
    """Read existing dependencies from mix.exs."""
    try:
        with open(MIX_FILE, "r") as f:
            content = f.read()
        return set(re.findall(r"\{:(\w+),", content))  # Extract package names
    except FileNotFoundError:
        return set()

def add_dependency_to_mix(pkg, version):
    """Add a dependency to mix.exs in the correct format."""
    existing_deps = read_existing_deps()
    if pkg in existing_deps:
        print(f"{BOLD}{YELLOW}✓ Skipping:{RESET} {pkg} is already in mix.exs")
        return
    
    try:
        with open(MIX_FILE, "r") as f:
            lines = f.readlines()

        # Find the `defp deps do` section
        deps_start = next(i for i, line in enumerate(lines) if "defp deps do" in line)

        # Build the new dependency line
        dep_entry = f"      {{:{pkg}, \"~> {version}\"}},\n"

        # Find where to insert it (before the closing `]`)
        insert_pos = next(i for i, line in enumerate(lines[deps_start:], start=deps_start) if "]" in line)

        # Insert the dependency
        lines.insert(insert_pos, dep_entry)

        # Write back to the file
        with open(MIX_FILE, "w") as f:
            f.writelines(lines)

        print(f"{BOLD}{GREEN}✓ Added:{RESET} {pkg} ~> {version} to mix.exs")
    except Exception as e:
        print(f"{BOLD}{RED}ERROR:{RESET} Could not modify mix.exs - {e}", file=sys.stderr)

def add_packages(packages):
    """Process packages, add them to mix.exs, and run `mix deps.get`."""
    print(f"\n{BOLD}{CYAN}Adding dependencies to mix.exs...{RESET}\n")

    added_any = False

    for pkg_def in packages:
        if "=" in pkg_def:
            pkg, version = pkg_def.split("=")
        else:
            pkg = pkg_def
            pkg_info = fetch_pkg_info(pkg)
            version = pkg_info["latest_version"] if pkg_info else None

        if version:
            add_dependency_to_mix(pkg, version)
            added_any = True

    # Run `mix deps.get` only if at least one package was added
    if added_any:
        print(f"\n{BOLD}{CYAN}Fetching dependencies with mix deps.get...{RESET}")

        stop_event = threading.Event()
        loader_thread = threading.Thread(target=spinning_cursor, args=(stop_event,))
        loader_thread.start()

        try:
            # Suppress intermediate output by redirecting stdout
            result = subprocess.run(["mix", "deps.get"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError:
            print(f"{BOLD}{RED}ERROR:{RESET} Failed to run mix deps.get", file=sys.stderr)

        stop_event.set()
        loader_thread.join()

        print(f"\n{BOLD}{GREEN}✓ Dependencies installed successfully!{RESET}")

def remove_dependency_from_mix(pkg):
    """Remove a dependency from mix.exs."""
    try:
        with open(MIX_FILE, "r") as f:
            lines = f.readlines()

        # Remove the dependency line if it exists
        new_lines = [line for line in lines if not re.search(rf"\{{:{pkg},", line)]

        if len(new_lines) == len(lines):
            print(f"{BOLD}{YELLOW}✓ Skipping:{RESET} {pkg} not found in mix.exs")
            return False

        # Write back the modified file
        with open(MIX_FILE, "w") as f:
            f.writelines(new_lines)

        print(f"{BOLD}{GREEN}✓ Removed:{RESET} {pkg} from mix.exs")
        return True
    except Exception as e:
        print(f"{BOLD}{RED}ERROR:{RESET} Could not modify mix.exs - {e}", file=sys.stderr)
        return False

def remove_packages(packages):
    """Remove packages from mix.exs and uninstall dependencies."""
    print(f"\n{BOLD}{CYAN}Removing dependencies from mix.exs...{RESET}\n")

    removed_any = False

    for pkg in packages:
        if remove_dependency_from_mix(pkg):
            removed_any = True

    # Run `mix deps.unlock` and `mix deps.clean` only if at least one package was removed
    if removed_any:
        print(f"\n{BOLD}{CYAN}Unlocking dependencies from mix.lock...{RESET}")
        try:
            subprocess.run(["mix", "deps.unlock"] + packages, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError:
            print(f"{BOLD}{RED}ERROR:{RESET} Failed to run mix deps.unlock", file=sys.stderr)

        print(f"\n{BOLD}{CYAN}Cleaning dependencies from deps directory...{RESET}")
        try:
            subprocess.run(["mix", "deps.clean"] + packages, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError:
            print(f"{BOLD}{RED}ERROR:{RESET} Failed to run mix deps.clean", file=sys.stderr)

        print(f"\n{BOLD}{GREEN}✓ Dependencies fully removed!{RESET}")

def main():
    parser = argparse.ArgumentParser(
        description="Manage Elixir dependencies using PyMix",
        epilog="""
Examples:

  # Fetch package info
  py pymix.py --pkg-info ecto
  py pymix.py --pkg-info ecto_sql postgrex

  # Add dependencies (latest version)
  py pymix.py --pkg-add ecto ecto_sql

  # Add a dependency with a specific version
  py pymix.py --pkg-add postgrex=0.20.0
  
  # Remove dependencies
  py pymix.py --pkg-rm ecto ecto_sql
""",
        formatter_class=argparse.RawTextHelpFormatter  # Keeps newlines in the epilog
    )

    parser.add_argument("--pkg-info", nargs="+", help="Fetch package information")
    parser.add_argument("--pkg-add", nargs="+", help="Add dependencies to mix.exs (latest or specific version)")
    parser.add_argument("--pkg-rm", nargs="+", help="Remove dependencies from mix.exs")

    args = parser.parse_args()

    if args.pkg_info:
        get_pkg_info(args.pkg_info)
    
    if args.pkg_add:
        add_packages(args.pkg_add)

    if args.pkg_rm:
        remove_packages(args.pkg_rm)

if __name__ == "__main__":
    check_mix_file()
    main()
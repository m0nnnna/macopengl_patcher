#!/usr/bin/env python3
import os
import shutil
import sys
import subprocess
from datetime import datetime

# Configurable app list: {path: {name, flags, executable, method}}
# method: "patch" (in-bundle wrapper) or "script" (external script + wrapper app)
APPS_TO_PATCH = {
    "/Applications/Google Chrome.app": {
        "name": "Google Chrome",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/Google Chrome",
        "method": "patch"
    },
    "/Applications/Discord.app": {
        "name": "Discord",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/Discord",
        "method": "patch"  # Worked with old method
    },
    "/Applications/Spotify.app": {
        "name": "Spotify",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/Spotify",
        "method": "script"  # Requires external script
    },
    "/Applications/Visual Studio Code.app": {
        "name": "Visual Studio Code",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/Visual Studio Code",
        "method": "patch"
    },
    "/Applications/Slack.app": {
        "name": "Slack",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/Slack",
        "method": "patch"
    },
    "/Applications/Microsoft Teams.app": {
        "name": "Microsoft Teams",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/Microsoft Teams",
        "method": "patch"
    },
    "/Applications/OBS.app": {
        "name": "OBS Studio",
        "flags": ["--use-gl=desktop"],
        "executable": "Contents/MacOS/OBS",
        "method": "patch"
    }
}

INSTALL_DIR = "/usr/local/bin"
WRAPPER_DIR = os.path.expanduser("~/Applications")

def backup_file(file_path):
    """Create a timestamped backup of the original file."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False
    backup_dir = os.path.dirname(file_path) + "/Backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/{os.path.basename(file_path)}.backup_{timestamp}"
    shutil.copy(file_path, backup_path)
    print(f"Backup created: {backup_path}")
    return True

def resign_app(app_path, app_name):
    """Deep resign the app and remove quarantine attribute."""
    print(f"Resigning {app_name} at {app_path}...")
    try:
        subprocess.run(["codesign", "--deep", "-f", "-s", "-", app_path], check=True)
        print(f"Successfully resigned {app_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to resign {app_name}: {e}")
        return False

    print(f"Removing quarantine attribute for {app_name}...")
    try:
        subprocess.run(["xattr", "-r", "-d", "com.apple.quarantine", app_path], check=True)
        print(f"Quarantine attribute removed for {app_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to remove quarantine attribute: {e}")
    return True

def patch_in_bundle(app_path, app_info):
    """Patch the app by replacing its executable with a wrapper script."""
    app_name = app_info["name"]
    flags = app_info["flags"]
    executable_path = f"{app_path}/{app_info['executable']}"
    print(f"Patching {app_name} in-bundle at {executable_path} with flags: {' '.join(flags)}...")

    if not os.path.exists(executable_path):
        print(f"Skipping {app_name}: Executable not found.")
        return False

    original_executable = f"{executable_path}.orig"
    if not os.path.exists(original_executable):
        if not backup_file(executable_path):
            return False
        shutil.move(executable_path, original_executable)
    else:
        print(f"Original executable already backed up at {original_executable}.")

    wrapper_script = f"""#!/bin/bash
# Launch {app_name} with OpenGL flags
echo "$(date): Launching {app_name} with flags: {' '.join(flags)}" >> ~/Library/Logs/{app_name}_wrapper.log
exec "{original_executable}" {' '.join(f'"{flag}"' for flag in flags)} "$@"
"""
    try:
        with open(executable_path, "w") as f:
            f.write(wrapper_script)
        os.chmod(executable_path, 0o755)
        print(f"Wrapper script created for {app_name}.")
    except PermissionError:
        print(f"Permission denied. Please run with sudo: 'sudo python3 {sys.argv[0]}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error writing wrapper for {app_name}: {e}")
        return False

    if not resign_app(app_path, app_name):
        print(f"Restoring original executable for {app_name} due to signing failure...")
        shutil.move(original_executable, executable_path)
        return False
    return True

def create_script_and_wrapper(app_path, app_info):
    """Create an external launch script and wrapper app."""
    app_name = app_info["name"]
    flags = app_info["flags"]
    executable_path = f"{app_path}/{app_info['executable']}"
    script_name = f"{app_name.lower().replace(' ', '_')}_opengl.sh"
    script_path = f"{INSTALL_DIR}/{script_name}"
    wrapper_app_path = f"{WRAPPER_DIR}/{app_name} OpenGL.app"

    if not os.path.exists(executable_path):
        print(f"Skipping {app_name}: Executable not found.")
        return False

    # Revert any prior in-bundle patch
    original_executable = f"{executable_path}.orig"
    if os.path.exists(original_executable):
        print(f"Reverting prior patch for {app_name}...")
        shutil.move(original_executable, executable_path)

    # Create the launch script
    script_content = f"""#!/bin/bash
# Launch {app_name} with OpenGL flags
echo "$(date): Launching {app_name} with flags: {' '.join(flags)}" >> ~/Library/Logs/{app_name}_launch.log
exec "{executable_path}" {' '.join(f'"{flag}"' for flag in flags)} "$@"
"""
    print(f"Creating launch script for {app_name} at {script_path}...")
    try:
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"Launch script created for {app_name}.")
    except PermissionError:
        print(f"Permission denied. Please run with sudo: 'sudo python3 {sys.argv[0]}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating launch script for {app_name}: {e}")
        return False

    # Create the wrapper app
    os.makedirs(f"{wrapper_app_path}/Contents/MacOS", exist_ok=True)
    os.makedirs(f"{wrapper_app_path}/Contents/Resources", exist_ok=True)

    wrapper_script = f"""#!/bin/bash
{script_path}
"""
    wrapper_executable = f"{wrapper_app_path}/Contents/MacOS/{app_name} OpenGL"
    try:
        with open(wrapper_executable, "w") as f:
            f.write(wrapper_script)
        os.chmod(wrapper_executable, 0o755)
    except Exception as e:
        print(f"Error creating wrapper executable for {app_name}: {e}")
        return False

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{app_name} OpenGL</string>
    <key>CFBundleIdentifier</key>
    <string>com.{app_name.lower().replace(' ', '.')}.opengl</string>
    <key>CFBundleName</key>
    <string>{app_name} OpenGL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
"""
    with open(f"{wrapper_app_path}/Contents/Info.plist", "w") as f:
        f.write(plist_content)

    # Copy icon (optional)
    icon_path = f"{app_path}/Contents/Resources/{app_name}.icns"
    if os.path.exists(icon_path):
        shutil.copy(icon_path, f"{wrapper_app_path}/Contents/Resources/")
    print(f"Created wrapper app for {app_name} at {wrapper_app_path}.")
    return True

def reset_launch_services():
    """Reset the Launch Services database to refresh Dock/Finder."""
    print("Resetting Launch Services database...")
    try:
        subprocess.run([
            "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister",
            "-kill", "-r", "-domain", "local", "-domain", "system", "-domain", "user"
        ], check=True)
        print("Launch Services reset complete. Restarting Dock...")
        subprocess.run(["killall", "Dock"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to reset Launch Services: {e}")

def main():
    print("Patching applications for OpenGL rendering (hybrid method)...")
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR, exist_ok=True)
    if not os.path.exists(WRAPPER_DIR):
        os.makedirs(WRAPPER_DIR, exist_ok=True)

    for app_path, app_info in APPS_TO_PATCH.items():
        method = app_info.get("method", "patch")  # Default to patch if unspecified
        if method == "patch":
            success = patch_in_bundle(app_path, app_info)
            if success:
                print(f"{app_info['name']} patched successfully (in-bundle). Launch normally.")
            else:
                print(f"Fallback: Could not patch {app_info['name']} in-bundle.")
        elif method == "script":
            success = create_script_and_wrapper(app_path, app_info)
            if success:
                print(f"{app_info['name']} set up successfully (external script). Use '~/Applications/{app_info['name']} OpenGL.app'.")
            else:
                print(f"Failed to set up {app_info['name']} with external script.")

    reset_launch_services()
    print("Setup complete. For 'patch' apps, launch normally. For 'script' apps, use '~/Applications/<App Name> OpenGL.app' or '<app_name>_opengl.sh'.")

if __name__ == "__main__":
    main()
import subprocess
import os
import sys
import inquirer
import argparse
import re
import shutil
import logging
import hashlib
import importlib.metadata
from inquirer.render.console import ConsoleRender
from modules.server_management import load_exclusions, view_exclusions

# Configure basic logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Check python-inquirer version
def check_inquirer_version():
    """Check if python-inquirer is installed and log its version."""
    try:
        inquirer_version = importlib.metadata.version("python-inquirer")
        logging.info(f"Using python-inquirer version {inquirer_version}")
        return True
    except importlib.metadata.PackageNotFoundError:
        logging.warning("Could not detect python-inquirer version. Assuming it is installed.")
        try:
            import inquirer
            logging.info("python-inquirer module is importable, proceeding.")
            return True
        except ImportError:
            logging.error("python-inquirer is not installed. Please install it with 'pip install python-inquirer'.")
            print("Error: python-inquirer is not installed. Install it with 'pip install python-inquirer'.")
            return False

class CustomRender(ConsoleRender):
    """Custom renderer to visually distinguish excluded servers."""
    def render_choice(self, choice, pointer=False):
        exclusions = load_exclusions()
        excluded_names = {ex["name"] for ex in exclusions["exclusions"]}
        if choice in excluded_names:
            return f"\033[90m{choice} (excluded)\033[0m"  # Gray text
        return choice

def create_dedicated_user(username):
    try:
        subprocess.run(["id", username], check=True)
        print(f"User {username} already exists.")
    except subprocess.CalledProcessError:
        subprocess.run(["useradd", "-m", "-s", "/bin/bash", username], check=True)
        print(f"User {username} created.")
    subprocess.run(["usermod", "-aG", "sudo", username], check=True)
    print(f"User {username} added to sudo group.")
    sudoers_line = f"{username} ALL=(ALL) NOPASSWD: /bin/systemctl start sing-box.service, /bin/systemctl stop sing-box.service, /bin/systemctl restart sing-box.service"
    with open("/etc/sudoers.d/singbox", "w") as sudoers_file:
        sudoers_file.write(sudoers_line)
    print(f"Sudoers file for {username} created.")

def set_directory_permissions(username, directories):
    for directory in directories:
        subprocess.run(["chown", "-R", f"{username}:{username}", directory], check=True)
        print(f"Permissions set for {directory}.")

def create_virtualenv(path):
    venv_path = os.path.join(path, "venv")
    if not os.path.exists(venv_path):
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print(f"Virtual environment created at {venv_path}")
    else:
        print(f"Virtual environment already exists at {venv_path}")
    return venv_path

def activate_virtualenv(venv_path):
    activate_script = os.path.join(venv_path, "bin", "activate")
    activate_command = f"source {activate_script}"
    subprocess.run(activate_command, shell=True, executable="/bin/bash")

def get_file_hash(file_path):
    """Compute SHA-256 hash of a file."""
    if not os.path.exists(file_path):
        return None
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def copy_files_to_installation_path(source_files, destination_path):
    """Copy files to destination, overwriting if contents differ."""
    for file in source_files:
        destination_file = os.path.join(destination_path, os.path.basename(file))
        source_hash = get_file_hash(file)
        dest_hash = get_file_hash(destination_file)
        if source_hash != dest_hash:
            shutil.copy(file, destination_file)
            print(f"Copied {file} to {destination_file} (updated or new)")
        else:
            print(f"File {destination_file} is unchanged, skipping copy.")

    modules_source = "modules"
    modules_destination = os.path.join(destination_path, "modules")
    if not os.path.exists(modules_destination):
        shutil.copytree(modules_source, modules_destination)
        print(f"Copied {modules_source} to {modules_destination}")
    else:
        # Recursively compare and update module files
        for root, _, files in os.walk(modules_source):
            rel_path = os.path.relpath(root, modules_source)
            dest_dir = os.path.join(modules_destination, rel_path)
            os.makedirs(dest_dir, exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                src_hash = get_file_hash(src_file)
                dest_hash = get_file_hash(dest_file)
                if src_hash != dest_hash:
                    shutil.copy(src_file, dest_file)
                    print(f"Copied {src_file} to {dest_file} (updated or new)")
                else:
                    print(f"File {dest_file} is unchanged, skipping copy.")

def get_server_list(url):
    """Fetch server list using update_singbox.py -l."""
    logging.info(f"Fetching server list using URL: {url}")
    try:
        result = subprocess.run(
            ["sudo", "-E", "./update_singbox.py", "-u", url, "-l"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to fetch server list. Return code: {e.returncode}, Output: {e.stderr}")
        print(f"Error: Failed to fetch server list. Check URL or network connectivity.")
        return []
    lines = result.stdout.splitlines()
    if len(lines) <= 2:
        logging.warning("No servers found in the fetched list.")
        print("Error: No servers found in the fetched list.")
        return []
    server_list = []
    seen_names = set()
    for line in lines[2:]:  # Skip header lines
        parts = line.split("|")
        if len(parts) > 1:
            name = parts[1].strip()
            # Clean up name: remove redundant prefixes and special characters
            name = re.sub(r'➔.*$', '', name).strip()
            name = re.sub(r'^\W+', '', name)  # Remove leading emojis/non-word chars
            if name and name not in seen_names:
                server_list.append(name)
                seen_names.add(name)
    return server_list

def get_server_list_with_exclusions(url):
    """Fetch server list and mark exclusions."""
    if not check_inquirer_version():
        return []
    server_list = get_server_list(url)
    exclusions = load_exclusions()
    excluded_names = {ex["name"] for ex in exclusions["exclusions"]}
    # Format choices with exclusion markers
    return [
        f"\033[90m{name} (excluded)\033[0m" if name in excluded_names else name
        for name in server_list
    ]

def parse_arguments():
    parser = argparse.ArgumentParser(description="Installation Wizard for Update Singbox")
    parser.add_argument("-p", "--path", default="/opt/update_singbox/", help="Installation path")
    parser.add_argument("-u", "--url", default="https://default.link", help="Installation link")
    parser.add_argument("-s", "--silent", action="store_true", help="Silent installation mode")
    parser.add_argument("-t", "--timer", default="15min", help="Timer frequency")
    parser.add_argument("-d", type=int, choices=range(3), default=1, help="Service verbosity level (0-2)")
    return parser.parse_args()

def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def ensure_install_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created installation path: {path}")
    else:
        print(f"Installation path already exists: {path}")

def setup_systemd_service(install_path, timer_frequency, service_verbosity, install_link):
    service_path = "/etc/systemd/system/update_singbox.service"
    timer_path = "/etc/systemd/system/update_singbox.timer"
    service_content = f"""
[Unit]
Description=Update Singbox Service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=oneshot
WorkingDirectory={install_path}
Environment="SINGBOX_DEBUG={service_verbosity}"
Environment="SINGBOX_URL={install_link}"
ExecStart={install_path}/venv/bin/python {install_path}/update_singbox.py
Restart=no
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
"""
    with open(service_path, "w") as service_file:
        service_file.write(service_content)
    print(f"Systemd service created or updated at {service_path}")
    timer_content = f"""
[Unit]
Description=Run Update Singbox every {timer_frequency}

[Timer]
OnBootSec={timer_frequency}
OnUnitActiveSec={timer_frequency}
Unit=update_singbox.service

[Install]
WantedBy=timers.target
"""
    with open(timer_path, "w") as timer_file:
        timer_file.write(timer_content)
    print(f"Systemd timer created or updated at {timer_path}")
    # Reload systemd and reset failed state
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "reset-failed", "update_singbox.service"], check=True)
    subprocess.run(["systemctl", "enable", "update_singbox.timer"], check=True)
    subprocess.run(["systemctl", "start", "update_singbox.timer"], check=True)
    print("Systemd timer enabled and started.")

def run_installation_wizard():
    args = parse_arguments()
    main_menu = [
        inquirer.List(
            "action",
            message="Select an action",
            choices=["Get Config", "Install", "Manage Exclusions", "Exit"],
        )
    ]

    while True:
        answers = inquirer.prompt(main_menu)
        if not answers:
            continue
        if answers["action"] == "Exit":
            print("Exiting wizard.")
            break

        elif answers["action"] == "Get Config":
            config_questions = [
                inquirer.Text("install_link", message="Enter subscription URL", default=args.url, validate=lambda _, x: validate_url(x)),
                inquirer.List("server_type", message="Select installation type", choices=["Single Server", "Multi-Server"]),
            ]
            config_answers = inquirer.prompt(config_questions)
            if not config_answers:
                continue

            install_link = config_answers["install_link"]
            server_type = config_answers["server_type"]
            server_list = get_server_list_with_exclusions(install_link)
            if not server_list:
                print("Error: No servers available.")
                continue

            if server_type == "Single Server":
                server_question = [
                    inquirer.List("server", message="Select server", choices=server_list, carousel=True)
                ]
            else:
                server_question = [
                    inquirer.Checkbox("servers", message="Select servers", choices=server_list, carousel=True)
                ]
            server_answers = inquirer.prompt(server_question, render=CustomRender())
            if not server_answers:
                continue

            # Map selected servers to indices, ignoring "(excluded)" suffix
            all_servers = get_server_list(install_link)
            if server_type == "Single Server":
                selected_server = re.sub(r'\s*\(excluded\)$', '', server_answers["server"])
                if selected_server in [re.sub(r'\s*\(excluded\)$', '', s) for s in server_list if "(excluded)" in s]:
                    print(f"Error: Cannot select excluded server: {selected_server}")
                    continue
                selected_indices = [all_servers.index(selected_server)]
            else:
                selected_servers = [
                    re.sub(r'\s*\(excluded\)$', '', server)
                    for server in server_answers["servers"]
                ]
                selected_indices = []
                for server in selected_servers:
                    if server in [re.sub(r'\s*\(excluded\)$', '', s) for s in server_list if "(excluded)" in s]:
                        print(f"Warning: Skipping excluded server: {server}")
                        continue
                    selected_indices.append(all_servers.index(server))

            if not selected_indices:
                print("Error: No valid servers selected.")
                continue

            # Run update_singbox.py with selected indices
            cmd = ["sudo", "-E", "./update_singbox.py", "-u", install_link, "-i", ",".join(map(str, selected_indices))]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"Configuration applied successfully at /etc/sing-box/config.json")
                print("Sing-box service restarted.")
                logging.info(f"Get Config: Applied configuration with indices {selected_indices}")
                if result.stdout:
                    print("Output:", result.stdout)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to apply configuration: {e.stderr}")
                print(f"Error: Failed to apply configuration. Details: {e.stderr}")

        elif answers["action"] == "Install":
            install_questions = [
                inquirer.Text("install_path", message="Installation path", default=args.path),
                inquirer.Text("install_link", message="Subscription URL", default=args.url, validate=lambda _, x: validate_url(x)),
                inquirer.Text("timer_frequency", message="Timer frequency", default=args.timer),
                inquirer.List("debug_level", message="Debug level", choices=[
                    ("Minimal", 0), ("Detailed", 1), ("Verbose", 2)
                ], default=1, carousel=True),
                inquirer.List("server_type", message="Installation type", choices=["Single Server", "Multi-Server"], default="Single Server"),
            ]
            install_answers = inquirer.prompt(install_questions)
            if not install_answers:
                continue

            install_path = install_answers["install_path"]
            install_link = install_answers["install_link"]
            timer_frequency = install_answers["timer_frequency"]
            debug_level = install_answers["debug_level"]
            server_type = install_answers["server_type"]

            server_list = get_server_list_with_exclusions(install_link)
            if not server_list:
                print("Error: No servers available.")
                continue
            if server_type == "Single Server":
                server_question = [
                    inquirer.List("server", message="Select server", choices=server_list, carousel=True)
                ]
            else:
                server_question = [
                    inquirer.Checkbox("servers", message="Select servers", choices=server_list, carousel=True)
                ]
            server_answers = inquirer.prompt(server_question, render=CustomRender())
            if not server_answers:
                continue

            ensure_install_path(install_path)
            copy_files_to_installation_path(["update_singbox.py", "config.template.json", "logging_setup.py"], install_path)
            venv_path = create_virtualenv(install_path)
            activate_virtualenv(venv_path)
            subprocess.run([os.path.join(venv_path, "bin", "pip"), "install", "-r", "requirements.txt"], check=True)
            setup_systemd_service(install_path, timer_frequency, debug_level, install_link)
            print("Installation completed.")

        elif answers["action"] == "Manage Exclusions":
            exclusion_menu = [
                inquirer.List(
                    "exclusion_action",
                    message="Manage exclusions",
                    choices=["View Exclusions", "Add Exclusions", "Remove Exclusions", "Back"],
                )
            ]
            exclusion_answers = inquirer.prompt(exclusion_menu)
            if not exclusion_answers or exclusion_answers["exclusion_action"] == "Back":
                continue
            if exclusion_answers["exclusion_action"] == "View Exclusions":
                view_exclusions()
            elif exclusion_answers["exclusion_action"] in ["Add Exclusions", "Remove Exclusions"]:
                url_question = [
                    inquirer.Text("install_link", message="Subscription URL", default=args.url, validate=lambda _, x: validate_url(x))
                ]
                url_answers = inquirer.prompt(url_question)
                if not url_answers:
                    continue
                server_list = get_server_list(url_answers["install_link"])
                if not server_list:
                    print("Error: No servers available.")
                    continue
                server_question = [
                    inquirer.Checkbox("servers", message="Select servers to exclude", choices=server_list, carousel=True)
                ]
                server_answers = inquirer.prompt(server_question)
                if not server_answers:
                    continue
                exclude_args = server_answers["servers"] if exclusion_answers["exclusion_action"] == "Add Exclusions" else [f"-{s}" for s in server_answers["servers"]]
                try:
                    subprocess.run(["sudo", "-E", "./update_singbox.py", "-u", url_answers["install_link"], "-e"] + exclude_args, check=True)
                    print("Exclusions updated successfully.")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to manage exclusions: {e.stderr}")
                    print(f"Error: Failed to manage exclusions. Details: {e.stderr}")

if __name__ == "__main__":
    run_installation_wizard()
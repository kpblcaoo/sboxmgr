import subprocess
import os
import sys
import inquirer
import argparse
import re
import shutil

# Function to create a dedicated user

def create_dedicated_user(username):
    try:
        # Check if user already exists
        subprocess.run(["id", username], check=True)
        print(f"User {username} already exists.")
    except subprocess.CalledProcessError:
        # Create user if it doesn't exist
        subprocess.run(["useradd", "-m", "-s", "/bin/bash", username], check=True)
        print(f"User {username} created.")

    # Grant necessary permissions
    subprocess.run(["usermod", "-aG", "sudo", username], check=True)
    print(f"User {username} added to sudo group.")

    # Allow user to control sing-box service without password
    sudoers_line = f"{username} ALL=(ALL) NOPASSWD: /bin/systemctl start sing-box.service, /bin/systemctl stop sing-box.service, /bin/systemctl restart sing-box.service"
    with open("/etc/sudoers.d/singbox", "w") as sudoers_file:
        sudoers_file.write(sudoers_line)
    print(f"Sudoers file for {username} created.")

# Function to set permissions for necessary directories

def set_directory_permissions(username, directories):
    for directory in directories:
        subprocess.run(["chown", "-R", f"{username}:{username}", directory], check=True)
        print(f"Permissions set for {directory}.")

# Function to create a virtual environment

def create_virtualenv(path):
    venv_path = os.path.join(path, "venv")
    if not os.path.exists(venv_path):
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print(f"Virtual environment created at {venv_path}")
    else:
        print(f"Virtual environment already exists at {venv_path}")
    return venv_path

# Function to activate the virtual environment

def activate_virtualenv(venv_path):
    activate_script = os.path.join(venv_path, "bin", "activate")
    activate_command = f"source {activate_script}"
    subprocess.run(activate_command, shell=True, executable="/bin/bash")

# Function to retrieve server list using the `-l` option

def get_server_list(url):
    print(f"Debug: Fetching server list using URL: {url}")  # Debug statement
    result = subprocess.run(["sudo", "-E", "./update_singbox.py", "-u", url, "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Failed to fetch server list. Return code: {result.returncode}")
        return []
    lines = result.stdout.splitlines()
    if len(lines) <= 2:
        print("Error: No servers found in the fetched list.")
        return []
    server_list = []
    for line in lines[2:]:  # Skip header lines
        parts = line.split("|")
        if len(parts) > 1:
            server_list.append(parts[1].strip())
    return server_list

# Function to parse command-line arguments

def parse_arguments():
    parser = argparse.ArgumentParser(description="Installation Wizard for Update Singbox")
    parser.add_argument("-p", "--path", default="/opt/update_singbox/", help="Installation path")
    parser.add_argument("-u", "--url", default="https://default.link", help="Installation link")
    parser.add_argument("-s", "--silent", action="store_true", help="Silent installation mode")
    parser.add_argument("-t", "--timer", default="1min", help="Timer frequency")
    parser.add_argument("-d", type=int, choices=range(3), default=1, help="Service verbosity level (0-2)")
    return parser.parse_args()

# Function to validate URL format
def validate_url(url):
    # Simple regex to validate URL format
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(regex, url) is not None

# Function to copy necessary files to the installation path

def copy_files_to_installation_path(source_files, destination_path):
    for file in source_files:
        destination_file = os.path.join(destination_path, os.path.basename(file))
        if not os.path.exists(destination_file):
            shutil.copy(file, destination_file)
            print(f"Copied {file} to {destination_file}")
        else:
            print(f"File {destination_file} already exists, skipping copy.")

    # Copy entire modules directory
    modules_source = "modules"
    modules_destination = os.path.join(destination_path, "modules")
    if not os.path.exists(modules_destination):
        shutil.copytree(modules_source, modules_destination)
        print(f"Copied {modules_source} to {modules_destination}")
    else:
        print(f"Modules directory already exists at {modules_destination}, skipping copy.")

# Main installation wizard

def run_installation_wizard():
    args = parse_arguments()

    # Debug print to verify URL argument
    print(f"Debug: URL argument received: {args.url}")

    # Ensure the URL is correctly passed to the wizard
    install_link = args.url

    # Debug print to verify URL in prompt
    default_url = install_link
    print(f"Debug: URL in prompt default: {default_url}")

    if args.silent:
        # Silent installation using command-line arguments
        install_path = args.path
        timer_frequency = args.timer
        service_verbosity = args.d
        server_installation = "Single Server"  # Default to single server for silent mode
        single_server = "Default Server"  # Placeholder for actual server selection logic
        multi_servers = []
        proceed = True
    else:
        # Interactive installation with command-line defaults
        # Retrieve server list using existing modules
        server_list = get_server_list(args.url)

        # Interactive prompts for installation options
        questions = [
            inquirer.Text("install_path", message=f"Enter installation path (default: {args.path})", default=args.path),
            inquirer.Text("install_link", message=f"Enter installation link (default: {default_url})", default=default_url),
            inquirer.List("server_installation", message="Select installation type", choices=["Single Server", "Multi-Server"], default="Single Server")
        ]
        answers = inquirer.prompt(questions)

        install_path = answers["install_path"]
        install_link = answers["install_link"]
        server_installation = answers["server_installation"]

        # Debug print to verify URL after prompt
        print(f"Debug: URL after prompt: {install_link}")

        # Validate the URL if a function exists
        if not validate_url(install_link):
            print("Error: Invalid URL provided.")
            return

        # Handle server selection based on installation type
        if server_installation == "Single Server":
            single_server_question = [
                inquirer.List("single_server", message="Select a server for single-server installation", choices=server_list, default=server_list[0])
            ]
            single_server_answer = inquirer.prompt(single_server_question)
            single_server = single_server_answer["single_server"]
            multi_servers = []
        else:
            multi_servers_question = [
                inquirer.Checkbox("multi_servers", message="Select servers for multi-server installation", choices=server_list)
            ]
            multi_servers_answer = inquirer.prompt(multi_servers_question)
            multi_servers = multi_servers_answer["multi_servers"]
            single_server = None

        # Continue with other installation options
        questions = [
            inquirer.Text("timer_frequency", message=f"Enter timer frequency (default: {args.timer})", default=args.timer),
            inquirer.List("service_verbosity", message=f"Select service verbosity level (0-2, default: {args.d})", choices=[0, 1, 2], default=args.d),
            inquirer.Confirm("view_config", message="Do you want to view the installed configuration?", default=True)
        ]
        answers = inquirer.prompt(questions)

        timer_frequency = answers["timer_frequency"]
        service_verbosity = answers["service_verbosity"]
        view_config = answers["view_config"]

        if view_config:
            print("Installed configuration:")
            print(f"Installation path: {install_path}")
            print(f"Installation link: {install_link}")
            print(f"Server installation type: {server_installation}")
            if server_installation == "Single Server":
                print(f"Selected server: {single_server}")
            else:
                print(f"Selected servers: {', '.join(multi_servers)}")
            print(f"Timer frequency: {timer_frequency}")
            print(f"Service verbosity: {service_verbosity}")

        # Ask if the user wants to proceed with the installation
        proceed_question = [
            inquirer.Confirm("proceed", message="Do you want to proceed with the installation?", default=True)
        ]
        proceed_answer = inquirer.prompt(proceed_question)
        proceed = proceed_answer["proceed"]

    if not proceed:
        print("Installation aborted by user.")
        return

    # Ensure installation path
    ensure_install_path(install_path)

    # Copy necessary files to the installation path
    source_files = ["update_singbox.py", "config.template.json", "logging_setup.py"]  # Add other necessary files here
    copy_files_to_installation_path(source_files, install_path)

    # Create virtual environment
    venv_path = create_virtualenv(install_path)

    # Activate virtual environment
    activate_virtualenv(venv_path)

    # Install dependencies in the virtual environment
    subprocess.run([os.path.join(venv_path, "bin", "pip"), "install", "-r", "requirements.txt"], check=True)

    # Setup systemd service and timer
    setup_systemd_service(install_path, timer_frequency, service_verbosity, install_link)

    print("Installation completed.")

# Function to create systemd service and timer

def setup_systemd_service(install_path, timer_frequency, service_verbosity, install_link):
    service_path = "/etc/systemd/system/update_singbox.service"
    timer_path = "/etc/systemd/system/update_singbox.timer"

    # Create or update the systemd service file
    service_content = f"""
    [Unit]
    Description=Update Singbox Service

    [Service]
    WorkingDirectory={install_path}
    Environment="SINGBOX_DEBUG={service_verbosity}"
    Environment="SINGBOX_URL={install_link}"
    ExecStart={install_path}/update_singbox.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    """
    with open(service_path, "w") as service_file:
        service_file.write(service_content)
    print(f"Systemd service created or updated at {service_path}")

    # Create or update the systemd timer file
    timer_content = f"""
    [Unit]
    Description=Run Update Singbox every {timer_frequency}

    [Timer]
    OnBootSec={timer_frequency}
    OnUnitActiveSec={timer_frequency}

    [Install]
    WantedBy=timers.target
    """
    with open(timer_path, "w") as timer_file:
        timer_file.write(timer_content)
    print(f"Systemd timer created or updated at {timer_path}")

    # Enable and start the service
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "update_singbox.service"], check=True)
    subprocess.run(["systemctl", "start", "update_singbox.service"], check=True)
    print("Systemd service enabled and started.")

# Function to check and create installation path

def ensure_install_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created installation path: {path}")
    else:
        print(f"Installation path already exists: {path}")

if __name__ == "__main__":
    run_installation_wizard() 
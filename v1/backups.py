import PySimpleGUI as sg
import subprocess
import os
import json
from datetime import datetime

# Define the path for the configuration file
config_file = os.path.expanduser('~/.config/backup_config.json')

def load_backup_directory():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config.get('backup_directory', '')
    return ''

def save_backup_directory(directory):
    config = {'backup_directory': directory}
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f)

def run_command_and_write_output(command, output_file):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        with open(output_file, 'w') as f:
            f.write(result.stdout)
    except subprocess.CalledProcessError as e:
        sg.popup_error(f"Failed to execute {command}: {e}")

def list_python_packages(backup_directory):
    run_command_and_write_output(['pip', 'freeze'], os.path.join(backup_directory, 'python_packages.txt'))

def list_zypper_packages(backup_directory):
    run_command_and_write_output(['zypper', 'search', '--installed-only', '--type', 'package'], os.path.join(backup_directory, 'zypper_packages.txt'))

def list_flatpaks(backup_directory):
    run_command_and_write_output(['flatpak', 'list', '--columns=application'], os.path.join(backup_directory, 'flatpak_packages.txt'))

def list_snaps(backup_directory):
    run_command_and_write_output(['snap', 'list', '--all'], os.path.join(backup_directory, 'snap_packages.txt'))

def list_appimages(appimage_dir, backup_directory):
    files = [f for f in os.listdir(appimage_dir) if os.path.isfile(os.path.join(appimage_dir, f))]
    with open(os.path.join(backup_directory, 'appimage_list.txt'), 'w') as f:
        for file in files:
            if file.endswith('.AppImage'):
                f.write(file + '\n')

def list_npm_packages(backup_directory):
    run_command_and_write_output(['npm', 'list', '--global', '--depth=0'], os.path.join(backup_directory, 'npm_packages.txt'))

def create_installation_script(backup_directory):
    script_path = os.path.join(backup_directory, 'install_packages.sh')
    with open(script_path, 'w') as script:
        script.write("#!/bin/bash\n\n")
        script.write("echo Installing Python packages...\n")
        script.write("pip install -r python_packages.txt\n\n")
        
        script.write("echo Installing Zypper packages...\n")
        script.write("xargs -a zypper_packages.txt sudo zypper install -y\n\n")
        
        script.write("echo Installing Flatpak packages...\n")
        script.write("xargs -a flatpak_packages.txt flatpak install -y\n\n")
        
        script.write("echo Installing Snap packages...\n")
        script.write("xargs -a snap_packages.txt sudo snap install\n\n")
        
        script.write("echo Installing NPM packages...\n")
        script.write("xargs -a npm_packages.txt npm install --global\n\n")

# GUI Layout
layout = [
    [sg.Text('Package List Generator Utility', font=('Helvetica', 16), justification='center')],
    [sg.Text('This utility generates lists of installed packages on an OpenSUSE system.\n'
             'It is intended to expedite system reinstallations by documenting current installations.\n'
             'Note: This tool does not back up any packages or data.', size=(60, 3))],
    [sg.Text('Select AppImages Directory')],
    [sg.InputText(key='-APPDIR-', enable_events=True), sg.FolderBrowse()],
    [sg.Text('Select Backup Directory')],
    [sg.InputText(default_text=load_backup_directory(), key='-BACKUPDIR-', enable_events=True), sg.FolderBrowse()],
    [sg.Button('Generate Lists'), sg.Button('Exit')]
]

window = sg.Window('Package List Generator', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Generate Lists':
        backup_directory = values['-BACKUPDIR-']
        save_backup_directory(backup_directory)

        timestamp_folder_name = datetime.now().strftime('%d%m%y')
        timestamped_backup_dir = os.path.join(backup_directory, 'packages', timestamp_folder_name)
        os.makedirs(timestamped_backup_dir, exist_ok=True)

        list_python_packages(timestamped_backup_dir)
        list_zypper_packages(timestamped_backup_dir)
        list_flatpaks(timestamped_backup_dir)
        list_snaps(timestamped_backup_dir)
        list_npm_packages(timestamped_backup_dir)

        appimage_dir = values['-APPDIR-']
        if appimage_dir:
            list_appimages(appimage_dir, timestamped_backup_dir)

        create_installation_script(timestamped_backup_dir)
        
        sg.popup('Lists and installation script generated successfully!')

window.close()
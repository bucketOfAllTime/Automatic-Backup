from datetime import datetime
import os
import zipfile
import shutil
import sys
import json

# ==========================================
# DYNAMIC CONFIGURATION LOADING (JSON)
# ==========================================

# 1. Dynamically find the folder where the script/executable is running
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# 2. Build the full path to your config.json file
config_path = os.path.join(application_path, "AutomaticBackupConfig.json")

# 3. Open and read the JSON file
try:
    with open(config_path, "r", encoding="utf-8") as json_file:
        config_data = json.load(json_file)
except FileNotFoundError:
    print(f"Error: Could not find config.json at {config_path}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: config.json has a formatting mistake or typo!")
    sys.exit(1)

# 4. Save JSON data to corresponding variables
root_directory = config_data["root_directory"]
backup_age = config_data["backup_age"]
sources = config_data["sources"]

# ==========================================
# MAIN BACKUP PROCESS
# ==========================================

# Timestamp generation month-day-year_hour-minute-second
timestamp_format = "%m-%d-%Y_%H-%M-%S"
time = datetime.now()
timestamp = time.strftime(timestamp_format)

# directory creation
backup_directory = os.path.join(root_directory, timestamp)
os.makedirs(backup_directory, exist_ok=True)

# The main copying and compressing backup loop
for source_directory in sources:
    # Double-check that the source folder actually exists before scanning it
    if not os.path.exists(source_directory):
        print(f"Skipping missing source folder: {source_directory}")
        continue

    for root, dirs, files in os.walk(source_directory):
        for file in files:
            # 1. Absolute source file path
            source_file = os.path.join(root, file)
            
            # 2. Get relative path to mimic layout
            rel_path = os.path.relpath(source_file, source_directory)
            
            # 3. Create target zip path
            backup_zip_path = os.path.join(backup_directory, rel_path) + ".zip"
            
            # 4. Make matching nested subfolders on backup drive
            os.makedirs(os.path.dirname(backup_zip_path), exist_ok=True)
            
            # 5. Compress it
            with zipfile.ZipFile(backup_zip_path, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(source_file, arcname=file)

# ==========================================
# PRUNING OF OLD BACKUPS
# ==========================================
all_items = os.listdir(root_directory)
for item_name in all_items:
    full_item_path = os.path.join(root_directory, item_name)
    if os.path.isdir(full_item_path):
        try:
            # Parse the folder name string back into a real datetime object
            folder_date = datetime.strptime(item_name, "%m-%d-%Y_%H-%M-%S")
            
            # Calculate file age
            age_difference = datetime.now() - folder_date
            
            # Delete if it's too old
            if age_difference.days > backup_age:
                shutil.rmtree(full_item_path)
        except ValueError:
            # Skips folders that aren't named using our date pattern (like your program folder!)
            continue

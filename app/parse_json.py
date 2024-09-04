import os
import json


def consolidate_json_files(folder_path, output_file):
    # Check if the output file already exists and remove it
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed existing file: {output_file}")

    # Create a dictionary to hold combined data
    consolidated_data = {}

    # Get a sorted list of JSON filenames in the directory
    json_filenames = sorted(
        [f for f in os.listdir(folder_path) if f.endswith('.json')]
    )

    # Iterate over each file in the directory
    for filename in json_filenames:
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)

            # Open and read the JSON file
            with open(file_path, 'r') as json_file:
                try:
                    data = json.load(json_file)
                    if isinstance(data, dict):
                        # Merge the data into the consolidated_data dictionary
                        consolidated_data.update(data)
                    else:
                        print(
                            f"Skipping file {filename}: JSON top-level structure is not a dictionary.")
                except ValueError as e:
                    print(f"Error reading {filename}: {e}")

    # Write the consolidated data to the output file
    with open(output_file, 'w') as json_file:
        json.dump(consolidated_data, json_file, indent=4)

    print(f"Consolidation complete. Data written to {output_file}")

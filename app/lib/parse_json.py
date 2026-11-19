import os
import json
import tempfile


def consolidate_json_files(folder_path, output_file):
    """Merge every *.json dict in folder_path into output_file.

    The output is replaced atomically, and only when its content changes, so a
    reader (another worker, or a test running next to an app being built) never
    finds the file missing or half written.
    """
    output_name = os.path.basename(output_file)
    consolidated_data = {}
    for filename in sorted(f for f in os.listdir(folder_path) if f.endswith('.json') and f != output_name):
        with open(os.path.join(folder_path, filename), 'r') as json_file:
            try:
                data = json.load(json_file)
            except ValueError as e:
                print(f"Error reading {filename}: {e}")
                continue
        if isinstance(data, dict):
            consolidated_data.update(data)
        else:
            print(f"Skipping file {filename}: JSON top-level structure is not a dictionary.")

    content = json.dumps(consolidated_data, indent=4)
    try:
        with open(output_file, 'r') as existing:
            if existing.read() == content:
                return
    except OSError:
        pass

    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(output_file) or '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as json_file:
            json_file.write(content)
        os.replace(tmp_path, output_file)
    except BaseException:
        os.unlink(tmp_path)
        raise
    print(f"Consolidation complete. Data written to {output_file}")

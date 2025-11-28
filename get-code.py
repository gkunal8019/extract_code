import os
import shutil
#from google.colab import files

def py_to_single_txt_with_paths(input_path, output_txt, user_ignore_paths=None):
    """
    Finds all .py files in input_path (folder or file),
    ignores any file whose path includes '.venv', 'Lib', or 'site-packages',
    or is included in user_ignore_paths (can be file or folder),
    writes: folder path, filename, and code to one output txt file.
    """
    py_files = []
    IGNORE_STRS = ['.venv', 'Lib', 'site-packages']
    user_ignore_paths = user_ignore_paths or []

    def is_user_ignored(path):
        # Ignore if path matches or is inside any ignored file/folder
        for ig in user_ignore_paths:
            ig_abs = os.path.abspath(ig)
            path_abs = os.path.abspath(path)
            if path_abs == ig_abs or path_abs.startswith(ig_abs + os.sep):
                return True
        return False

    if os.path.isfile(input_path):
        ignore = any(x in input_path for x in IGNORE_STRS) or is_user_ignored(input_path)
        if input_path.endswith('.py') and not ignore:
            py_files.append(input_path)
    else:
        for root, dirs, files_ in os.walk(input_path):
            # Exclude dirs that should not be traversed or are in user_ignore_paths
            dirs[:] = [
                d for d in dirs 
                if all(x not in os.path.join(root, d) for x in IGNORE_STRS) and 
                not is_user_ignored(os.path.join(root, d))
            ]
            for f in files_:
                full_path = os.path.join(root, f)
                ignore = any(x in full_path for x in IGNORE_STRS) or is_user_ignored(full_path)
                if f.endswith('.py') and not ignore:
                    py_files.append(full_path)

    with open(output_txt, 'w', encoding='utf-8') as fout:
        for py_file in py_files:
            folder_path = os.path.dirname(py_file)
            filename = os.path.basename(py_file)
            with open(py_file, 'r', encoding='utf-8') as fin:
                code = fin.read()
            fout.write(f"Folder Path: {folder_path}\n")
            fout.write(f"File Name: {filename}\n\n")
            fout.write(code)
            fout.write("\n" + ("=" * 80) + "\n\n")  # separator

# --------- Usage Example ---------
input_path = 'Ranjeet-1/KRBL_Backup'
output_txt = 'Ranjeet-1/KRBL_Backup/all_files_details.txt'
user_ignore_paths = ['/data/Ranjeet/Ranjeet-1/KRBL_Backup/ultralytics',"/data/Ranjeet/Ranjeet-1/KRBL_Backup/test_tanuj_nms (1).py"]  # you can set these

py_to_single_txt_with_paths(input_path, output_txt, user_ignore_paths)
# shutil.make_archive('/content/all_files_details', 'zip', '/content', 'all_files_details.txt')
# files.download('/content/all_files_details.zip')

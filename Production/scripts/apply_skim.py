import os
import shutil
from concurrent.futures import ThreadPoolExecutor

from RunKit.run_tools import ps_call

def process_file(file_idx, path, file, input_dir, output_dir, n_files_str_len, n_files, config, setup):
  rel_path = os.path.join(path, file)
  input_file = os.path.join(input_dir, path, file)
  output_file = os.path.join(output_dir, path, file)
  label = f"({file_idx + 1:>{n_files_str_len}}/{n_files}) {rel_path}"
  if os.path.exists(output_file):
    print(f"{label}: exists")
    return

  output_file_dir = os.path.join(output_dir, path)
  output_file_tmp = os.path.join(output_file_dir, f".{file}")
  print(f"{label}: processing...")
  os.makedirs(output_file_dir, exist_ok=True)
  if os.path.exists(output_file_tmp):
    os.remove(output_file_tmp)
  ps_call([ 'RunKit/skim_tree.py', '--input', input_file, '--output', output_file_tmp,
            '--config', config, '--setup', setup, '--verbose', '0' ], verbose=1)
  shutil.move(output_file_tmp, output_file)
  print(f"{label}: done")
  return

def apply_skim(input_dir, output_dir, config, setup, n_parallel):
  root_files = []

  for dirpath, _, filenames in os.walk(input_dir):
    for file in filenames:
      if file.endswith('.root'):
        path = os.path.relpath(dirpath, input_dir)
        root_files.append((path, file))

  n_files = len(root_files)
  n_files_str_len = len(str(n_files))
  print(f"Found {n_files} root files")
  with ThreadPoolExecutor(max_workers=n_parallel) as executor:
    for file_idx, (path, file) in enumerate(root_files):
      executor.submit(process_file, file_idx, path, file, input_dir, output_dir, n_files_str_len, n_files, config,
                      setup)
    # executor.shutdown(wait=True)
  print("All files processed.")

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description='Apply skim recursively.')
  parser.add_argument('--input', required=True, type=str, help="input directory")
  parser.add_argument('--output', required=True, type=str, help="output directory")
  parser.add_argument('--config', required=True, type=str, help="Configuration with the skim setup.")
  parser.add_argument('--setup', required=True, type=str,
                      help="Name of the setup descriptor in the configuration file.")
  parser.add_argument('--n-parallel', required=False, type=int, default=4, help="Number of threads.")
  args = parser.parse_args()

  apply_skim(args.input, args.output, args.config, args.setup, args.n_parallel)

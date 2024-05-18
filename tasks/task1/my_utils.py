import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
import matplotlib.pyplot as plt
import numpy as np

def listRightIndex(alist, value):
    return len(alist) - alist[-1::-1].index(value) -1

def parse_champsim_output(text):
  text = text.decode("utf-8").split()
  mpki_idx = text.index('MPKI:')
  bc_idx = text.index('BRANCH_CONDITIONAL:')
  ipc_idx = listRightIndex(text, 'IPC:')

  l2c_idx = text.index('cpu0_L2C')
  assert text[l2c_idx + 1] == 'TOTAL'
  
  # IPC, TOTAL_MPKI, BRANCH_CONDITIONAL_MPKI, L2C_access, L2C_hit
  return float(text[ipc_idx+1]), float(text[mpki_idx+1]), float(text[bc_idx+1]), float(text[l2c_idx+3]), float(text[l2c_idx+5])

def obtain_perf_metrics(traces_path, cwd, config):
  # PREPARATION
  subprocess.run(f"./config.sh {config}", cwd=cwd, shell=True, check=True)
  subprocess.run("make -j8", cwd=cwd, shell=True, check=True)

  # GET LIST OF TRACES
  traces = list(map(lambda x: os.path.join(traces_path, x), os.listdir(traces_path)))
  metrics = {}

  # WRAPPER FOR PARALLEL LAUNCH
  launcher = lambda trace: subprocess.run(f"bin/champsim --warmup_instructions 5000000 --simulation_instructions 20000000 {trace}", cwd=cwd, capture_output=True, shell=True, check=True)

  with ThreadPoolExecutor() as executor:
    running_tasks = [(executor.submit(launcher, trace), trace) for trace in traces]
    for sub_res, trace in running_tasks:
      sub_res = sub_res.result()
      metrics[os.path.basename(trace)] = parse_champsim_output(sub_res.stdout)
  return metrics

def plot_metric(metrics_s, metric_id, title, labels):
  # Extracting test names
  test_names = list(metrics_s[0].keys())

  # Extracting metric values
  exp_values_s = []
  for m in metrics_s:
    exp_values_s.append([m[test][metric_id] for test in test_names])

  # Number of tests
  num_tests = len(test_names)

  # Creating bar width
  bar_width = 0.2

  # Set positions of bars on X axis
  r_s = [np.arange(num_tests)]
  for i in range(len(exp_values_s) - 1):
    r = [x + bar_width for x in r_s[i]]
    r_s.append(r)

  # Creating the bar chart
  plt.figure(figsize=(10, 5))

  colors = ['b', 'g', 'r']
  for i ,(r, exp_values, label) in enumerate(zip(r_s, exp_values_s, labels)):
    plt.bar(r, exp_values, color=colors[i % len(colors)], width=bar_width, edgecolor='grey', label=label)

  # Adding labels
  plt.title(title)
  plt.xlabel('Test Names', fontweight='bold')
  plt.ylabel(title, fontweight='bold')
  plt.xticks([r + bar_width for r in range(num_tests)], test_names, rotation=90)

  # Adding legend
  plt.legend()

  # Display the plot
  plt.show()
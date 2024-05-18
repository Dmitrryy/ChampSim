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
  
  # IPC, TOTAL_MPKI, BRANCH_CONDITIONAL_MPKI
  return float(text[ipc_idx+1]), float(text[mpki_idx+1]), float(text[bc_idx+1])

def obtain_perf_metrics(traces_path, cwd, config):
  # PREPARATION
  subprocess.run(f"./config.sh {config}", cwd=cwd, shell=True, check=True)
  subprocess.run("make -j8", cwd=cwd, shell=True, check=True)

  # GET LIST OF TRACES
  traces = map(lambda x: os.path.join(cwd, x), os.listdir(traces_path))
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
  exp1_values = [metrics_s[0][test][metric_id] for test in test_names]
  exp2_values = [metrics_s[1][test][metric_id] for test in test_names]
  exp3_values = [metrics_s[2][test][metric_id] for test in test_names]

  # Number of tests
  num_tests = len(test_names)

  # Creating bar width
  bar_width = 0.2

  # Set positions of bars on X axis
  r1 = np.arange(num_tests)
  r2 = [x + bar_width for x in r1]
  r3 = [x + bar_width for x in r2]

  # Creating the bar chart
  plt.figure(figsize=(10, 5))

  plt.bar(r1, exp1_values, color='b', width=bar_width, edgecolor='grey', label=labels[0])
  plt.bar(r2, exp2_values, color='g', width=bar_width, edgecolor='grey', label=labels[1])
  plt.bar(r3, exp3_values, color='r', width=bar_width, edgecolor='grey', label=labels[2])

  # Adding labels
  plt.title(title)
  plt.xlabel('Test Names', fontweight='bold')
  plt.ylabel(title, fontweight='bold')
  plt.xticks([r + bar_width for r in range(num_tests)], test_names, rotation=90)

  # Adding legend
  plt.legend()

  # Display the plot
  plt.show()
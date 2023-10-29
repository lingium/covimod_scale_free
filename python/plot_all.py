# this file aims to run all scripts in folder plot_scripts
# and generate all plots to figures folder

import os
from pathlib import Path

args = {}
args['main'] = Path(__file__).resolve()
args['cwd'] = args['main'].parent.parent
args['plot_scripts'] = args['cwd'] / 'python' / 'plot_scripts'

os.chdir(args['plot_scripts'])
# get all scripts in plot_scripts started with data_
scripts = [x for x in os.listdir()]
# run all scripts
for script in scripts:
    os.system(f'python {script}')
    print(f'python {script} finished')

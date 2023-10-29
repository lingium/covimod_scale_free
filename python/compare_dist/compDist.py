import os
import numpy as np
import pandas as pd
from pathlib import Path

import arviz as az
az.style.use("arviz-doc")
# az.rcParams["plot.backend"] = "bokeh"
az.rcParams["plot.backend"] = "matplotlib"
az.output_notebook()

args = {}
args['seed'] = 1234
current_file = Path(__file__).resolve()
args['main'] = str(current_file)
args['name'] = current_file.stem
args['root'] = current_file.parent.parent.parent
args['derived_dir'] = args['root'] / "data" / 'derived'
args['stan_dir'] = current_file.parent / args['name']
args['sample_args'] = {"iter_warmup": 500, "iter_sampling": 500, "chains": 2, "seed": args['seed'], "show_console": True}
args['stanc_args'] = {"include-paths": [str(args['root'] / 'src')]}
args['hpp'] = args['root'] / 'src' / 'cpp' / 'bnb.hpp'

import sys
sys.path.append(os.path.join(args['root'], 'src', 'python'))
from utils import stan_model


df = pd.read_csv(os.path.join(args['derived_dir'], 'df_full.csv'))
df_f1 = df.loc[df["rp_nb"] == 1,:].drop(columns=["rp_nb"])

data = df_f1[['nhh_nct']]
stan_data = {
    "N": len(data),
    "y": data['nhh_nct']+1,
}
stan_data_0 = {
    "N": len(data),
    "y": data['nhh_nct'],
}

models = {}
for m in ['zipf_global', 'zipfmoe_global', 'zipfpe_global', 'zipfpl_global', ]:
    print(m)
    args[m] = os.path.join(args['stan_dir'], m + '.stan')
    models[m] = stan_model(args[m])
    models[m].compile()
    models[m].sample(stan_data, **args['sample_args'])
    models[m].save()

for m in ['zipfpss_global', 'nb_global', 'poi_global']:
    print(m)
    args[m] = os.path.join(args['stan_dir'], m + '.stan')
    models[m] = stan_model(args[m])
    models[m].compile()
    models[m].sample(stan_data_0, **args['sample_args'])
    models[m].save()

for m in ['bnb_global']:
    print(m)
    args[m] = os.path.join(args['stan_dir'], m + '.stan')
    models[m] = stan_model(args[m])
    models[m].compile(user_header=args['hpp'], stanc_options=args['stanc_args'])
    models[m].sample(stan_data_0, **args['sample_args'])
    models[m].save()


comp_df = az.compare({name: model.az_data for name, model in models.items()}, ic="loo")
comp_df
az.plot_compare(comp_df[0:-1], insample_dev=True, plot_ic_diff=True, 
                backend='matplotlib', figsize=(8, 3))





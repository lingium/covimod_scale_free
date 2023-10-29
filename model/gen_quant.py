import os
import numpy as np
import pandas as pd
from pathlib import Path
from cmdstanpy import CmdStanModel

args = {}
args['seed'] = 1234
args['main'] = Path(__file__).resolve()
args['cwd'] = args['main'].parent.parent
args['stan_dir'] = args['cwd'] / 'model' / 'bnb'
args['derived_dir'] = args['cwd'] / "data" / 'derived'
args['output_dir'] = args['cwd'] / "data" / 'output'
args['fig_dir'] = args['cwd'] / "figures"
args['stanc_args'] = {"include-paths": [str(args['cwd'] / 'src')]}
args['hpp'] = args['cwd'] / 'src' / 'cpp' / 'bnb.hpp'

import sys
sys.path.append(os.path.join(args['cwd'], 'src', 'python'))
from utils import stan_model, merge_hdi, make_fitting_data

stan_data_0 = make_fitting_data(args['derived_dir'] / 'df_full.csv')
args['bnb_gp_awgtr'] = args['stan_dir'] / 'bnb_gp_awgtr.stan'
bnb_model = stan_model(args['bnb_gp_awgtr'], recover=True, 
                            stan_data=stan_data_0, stan_save_dir=args['output_dir'] / 'bnb_gp_awgtr_save')


# when calling external C++ code, Stan requires
# the name of the corresponding namespace should be modified to the model file name
tmp =  stan_model(args['stan_dir'] / 'gen_quant.stan')
for file in Path(args['hpp'].parent / 'bnb').rglob('*.hpp'):
    tmp.change_namespace(file)
del tmp

model_gen = CmdStanModel(stan_file=args['stan_dir'] / 'gen_quant.stan', 
                         compile=False, stanc_options=args['stanc_args'])
model_gen.compile(user_header=args['hpp'], )
new_quantities = model_gen.generate_quantities(data=stan_data_0, 
                                               previous_fit=bnb_model.fit,
                                               gq_output_dir=args['output_dir'] / 'bnb_gp_awgtr_gen',
                                               show_console=True,
                                               seed=args['seed'])

sample_gen = new_quantities.draws_xr(inc_sample=False)
sample_gen.to_netcdf(args['output_dir'] / 'bnb_gp_awgtr_gen.nc')

# sample_plus = new_quantities.draws_xr(inc_sample=True)
# sample_plus.to_netcdf(args['output_dir'] / 'bnb_gp_awgtr_all.nc')
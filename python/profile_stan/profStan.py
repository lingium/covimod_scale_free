import os
from pathlib import Path

args = {}
args['seed'] = 1234
current_file = Path(__file__).resolve()
args['main'] = str(current_file)
args['name'] = current_file.stem
args['cwd'] = current_file.parent.parent.parent.resolve()
args['stan_dir'] = current_file.parent / args['name']
args['sample_args'] = {"iter_warmup": 500, "iter_sampling": 500, "chains": 1, "show_console": True, "seed": args['seed']}
args['stanc_args'] = {"include-paths": [str(args['cwd'] / 'src')]}
args['hpp'] = args['cwd'] / 'src' / 'cpp' / 'bnb.hpp'

import sys
sys.path.append(os.path.join(args['cwd'], 'src', 'python'))
from utils import stan_model, bnb_mle_fit, beta_negative_binomial_rng



samples = beta_negative_binomial_rng(r=6, alpha=2, beta=0.5, size=10000, seed=args['seed'])
samples.mean()
samples.var()
bnb_mle_fit(samples)

stan_data_0 = {
    'N': len(samples),
    'y': samples,
}

models = {}

args['BNB_cpp'] = os.path.join(args['stan_dir'], 'BNB_cpp.stan')
BNB_cpp = stan_model(args['BNB_cpp'], )
BNB_cpp.compile(user_header=args['hpp'], stanc_options=args['stanc_args'])
BNB_cpp.sample(stan_data_0, **args['sample_args'])
models['BNB_cpp'] = BNB_cpp
BNB_cpp.az_data.posterior.mean(dim=["chain", "draw"])

# rename the csv file to avoid overwriting
profile_cpp = os.path.abspath(os.path.join(os.path.dirname(__file__), 'profile.csv'))
os.rename(profile_cpp, 'profile_cpp.csv')

args['BNB_stan'] = os.path.join(args['stan_dir'], 'BNB_stan.stan')
BNB_stan = stan_model(args['BNB_stan'], )
BNB_stan.compile(user_header=args['hpp'], stanc_options=args['stanc_args'])
BNB_stan.sample(stan_data_0, **args['sample_args'])
models['BNB_stan'] = BNB_stan
BNB_stan.az_data.posterior.mean(dim=["chain", "draw"])

profile_stan = os.path.abspath(os.path.join(os.path.dirname(__file__), 'profile.csv'))
os.rename(profile_stan, 'profile_stan.csv')
import sys
from pathlib import Path

args = {}
args['seed'] = 1234
args['main'] = Path(__file__).resolve()
args['cwd'] = args['main'].parent.parent.resolve()
args['stan_dir'] = args['main'].parent / 'bnb'
args['derived_dir'] = args['cwd'] / "data" / 'derived'
args['output_dir'] = args['cwd'] / "data" / 'output'
args['stanc_args'] = {"include-paths": [str(args['cwd'] / 'src')]}
args['hpp'] = args['cwd'] / 'src' / 'cpp' / 'bnb.hpp'

sys.path.append(str(args['cwd'] / 'src' / 'python'))
from utils import stan_model, make_fitting_data

stan_data_0 = make_fitting_data(args['derived_dir'] / 'df_full.csv')

args['bnb_gp_awgtr'] = args['stan_dir'] / 'bnb_gp_awgtr.stan'
bnb_model = stan_model(args['bnb_gp_awgtr'])
bnb_model.compile(user_header=args['hpp'], stanc_options=args['stanc_args'])
bnb_model.sample(stan_data_0, 
                 **{"chains": 4, "iter_warmup": 1000, "iter_sampling": 1000, 
                    "show_console": True, "seed": args['seed'], "refresh": 10})
bnb_model.save(args['output_dir'] / 'bnb_gp_awgtr_save')
print(bnb_model.fit.diagnose())


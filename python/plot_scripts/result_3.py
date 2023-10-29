import os
import numpy as np
import pandas as pd
import arviz as az
import xarray as xr
from pathlib import Path
import plotly.express as px


args = {}
args['main'] = Path(__file__).resolve()
args['cwd'] = args['main'].parent.parent.parent
args['stan_dir'] = args['cwd'] / 'model' / 'bnb'
args['derived_dir'] = args['cwd'] / "data" / 'derived'
args['output_dir'] = args['cwd'] / "data" / 'output'
args['fig_dir'] = args['cwd'] / "figures"

import sys
sys.path.append(os.path.join(args['cwd'], 'src', 'python'))
from utils import merge_hdi


# -------------------------- bnb_mu --------------------------

xr_data = xr.open_dataset(args['output_dir'] / 'bnb_gp_awgtr_gen.nc')
data = merge_hdi(xr_data, 'bnb_mu')
data = data.rename(columns={'bnb_mu_dim_0':'gender', 'bnb_mu_dim_1':'age', 'bnb_mu_dim_2':'wave'})
data['wave'] = data['wave'] + 1


data.min()
data.max()
# find row with max median
data.loc[data['median'].idxmax()]
data.loc[data['median'].idxmin()]


data_tmp = data[data['gender'].isin([0])]
data_tmp1 = data_tmp.pivot(index='wave', columns='age', values='median')
data_tmp = data[data['gender'].isin([1])]
data_tmp2 = data_tmp.pivot(index='wave', columns='age', values='median')
# make a 3d np array
data_tmp = np.stack([data_tmp1, data_tmp2], axis=0)
fig = px.imshow(data_tmp,facet_col = 0, facet_col_wrap=1,
                y=[str(i) for i in range(1,34)],
                labels=dict(x="Age", y="Wave"),
                color_continuous_scale='Portland',)
# add x labels
fig.update_xaxes(dtick="5",)
fig.update_yaxes(dtick="5",)
fig.update_layout(height=550, width=700, )

def waveGroupPolicy(text):
    if text == 'facet_col=1':
        return 'Male'
    elif text == 'facet_col=0':
        return 'Female'

fig.for_each_annotation(lambda a: a.update(text=waveGroupPolicy(a.text)))
fig.write_image(args['fig_dir'] / 'results' / "mean_heatmap.pdf")



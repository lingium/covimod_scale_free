import os
import numpy as np
import pandas as pd
import arviz as az
import xarray as xr
from pathlib import Path
from cmdstanpy import CmdStanModel

import plotly.express as px
import plotly.graph_objs as go
import plotly.offline as pyo
from plotly.subplots import make_subplots

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



# -------------------------- variance component coutour --------------------------

xr_data = xr.open_dataset(args['output_dir'] / 'bnb_gp_awgtr_gen.nc')
data_all = merge_hdi(xr_data, 'vars')

data_all = data_all.rename(columns={'vars_dim_0':'age', 'vars_dim_1':'gender', 'vars_dim_2':'wave', 'vars_dim_3':'repeat', 'vars_dim_4':'type'})
data_all['wave'] = data_all['wave'] + 1
data_all['age'] = data_all['age'].map({0:20, 1:40, 2:60, 3:80})
data_all['gender'] = data_all['gender'].map({0:'Female', 1:'Male'})
data_all['varname'] = data_all['type'].map({0:'Randomness', 1:'Liability', 2:'Proneness', 3:'Total'})

def compute_normalized_values(grouped_data):
    type3_values = grouped_data[grouped_data['type'] == 3][['median', 'higher', 'lower']].iloc[0]
    grouped_data['median_n'] = grouped_data['median'] / type3_values['median']
    grouped_data['higher_n'] = grouped_data['higher'] / type3_values['higher']
    grouped_data['lower_n'] = grouped_data['lower'] / type3_values['lower']
    return grouped_data


ages = data_all['age'].unique()
for age in ages:
    data = data_all[data_all['age'] == age]

    normalized_data = data.groupby(['gender', 'wave', 'repeat']).apply(compute_normalized_values)
    normalized_data = normalized_data.reset_index(drop=True)

    normalized_data = normalized_data[normalized_data['type'] != 3]
    genders = ['Male', 'Female']
    types = normalized_data['type'].unique()

    # Create subplots with facetting for gender and type
    fig = make_subplots(rows=len(types), cols=len(genders),
                        column_titles=['Male', 'Female'],
                        row_titles=['Randomness', 'Liability', 'Proneness'],
                        shared_yaxes=True,
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        horizontal_spacing=0.02)

    # Loop through each gender and type to add contour plots
    for row, t in enumerate(types, start=1):
        for col, g in enumerate(genders, start=1):
            subset = normalized_data[(normalized_data['type'] == t) & (normalized_data['gender'] == g)]
            matrix = subset.pivot(index='repeat', columns='wave', values='median_n')
            show_colorbar = True if row == len(types) else False
            fig.add_trace(go.Contour(z=matrix.values, x=matrix.columns, y=matrix.index, 
                                    showscale=False,
                                            contours=dict(
                coloring ='heatmap',
                showlabels = True, # show labels on contours
                labelfont = dict( # label font properties
                    size = 10,
                    color = 'white',
                )
            )), row=row, col=col)

    # Update layout and show the plot
    fig.update_layout(height=1000, width=800,)
    fig.for_each_xaxis(lambda x: x.update(title = ''))
    fig.for_each_yaxis(lambda y: y.update(title = ''))
    fig.add_annotation(x=-0.08,y=0.5,textangle=-90,showarrow=False, font=dict(size=16),
                        text="Repeats",
                        xref="paper", yref="paper")
    fig.add_annotation(x=0.5,y=-0.07, textangle=0,showarrow=False, font=dict(size=16),
                        text="Wave",
                        xref="paper", yref="paper")
    fig.update_xaxes(dtick=5)

    # fig.show()
    fig.write_image(args['fig_dir'] / 'data' / ('varcomponents_contour_'+ str(age) +'.pdf'))



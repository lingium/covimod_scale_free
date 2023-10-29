import os
import numpy as np
import pandas as pd
import arviz as az
import xarray as xr
import itertools
from pathlib import Path
from cmdstanpy import CmdStanModel

import plotly.express as px
import plotly.graph_objs as go
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



# -------------------------- variance components line plot --------------------------
xr_data = xr.open_dataset(args['output_dir'] / 'bnb_gp_awgtr_gen.nc')
data = merge_hdi(xr_data, 'vars')


data = data.rename(columns={'vars_dim_0':'age', 'vars_dim_1':'gender', 'vars_dim_2':'wave', 'vars_dim_3':'repeat', 'vars_dim_4':'var'})
data['wave'] = data['wave'] + 1
data['age'] = data['age'].map({0:20, 1:40, 2:60, 3:80})
data['gender'] = data['gender'].map({0:'Female', 1:'Male'})
data['varname'] = data['var'].map({0:'Randomness', 1:'Liability', 2:'Proneness', 3:'Total'})
data = data[data['repeat'] == 0]


color_palette = px.colors.qualitative.Plotly
ages = data['age'].unique()
fig = make_subplots(
    rows=12,  # Three rows for each age group
    cols=2,
    specs=[[{'rowspan': 2},{'rowspan': 2}],[None,None],[{},{}]] *4,
    shared_xaxes=True,
    shared_yaxes=True,
    vertical_spacing=0.015,
    horizontal_spacing=0.05,
    column_titles=['Male','Female'],
    row_titles=list(itertools.chain(*[[f'Age {age}', None] for age in ages]))
)

# For each unique age value, plot the lines and confidence intervals
for i, age in enumerate(ages, start=1):
    age_df = data[(data['age'] == age) & (data['var'] <= 2)]
    
    # Full subplot for all var values
    for idx, var in enumerate(age_df['var'].unique()):
        subset = age_df[age_df['var'] == var]
        color = color_palette[idx % len(color_palette)]
        rgba = 'rgba' + str(px.colors.hex_to_rgb(color))[:-1] + ', 0.3)'
        varname = {0:'Randomness', 1:'Liability', 2:'Proneness', 3:'Total'}[var]

        for g,gender in enumerate(['Male','Female'],start=1):
            gender_subset = subset[subset['gender'] == gender]
            line_dash = 'solid' if gender == 'Female' else 'solid'

            # Plot the median
            fig.append_trace(go.Scatter(
                x=gender_subset['wave'],
                y=gender_subset['median'],
                name=f'{varname}',
                line=dict(dash=line_dash, color=color),
                legendgroup=f'Var {var}',
                showlegend=True if (age == ages[0]) and (gender=='Male') else False
            ), row=3*i-2, col=g)

            # Plot intervals
            fig.append_trace(go.Scatter(
                x=gender_subset['wave'].tolist() + gender_subset['wave'][::-1].tolist(),
                y=gender_subset['higher'].tolist() + gender_subset['lower'][::-1].tolist(),
                fill='toself',
                fillcolor=rgba,
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                legendgroup=f'Var {var}'
            ), row=3*i-2, col=g)

    # Smaller subplot for var == 0
    subset = age_df[age_df['var'] == 0]
    for g,gender in enumerate(['Male','Female'],start=1):
        gender_subset = subset[subset['gender'] == gender]
        line_dash = 'solid' if gender == 'Female' else 'solid'
        color = color_palette[0]
        rgba = 'rgba' + str(px.colors.hex_to_rgb(color))[:-1] + ', 0.3)'

        # Plot the median
        fig.append_trace(go.Scatter(
            x=gender_subset['wave'],
            y=gender_subset['median'],
            name=f'Randomness-{gender}',
            line=dict(dash=line_dash, color=color),
            showlegend=False,
        ), row=3*i, col=g)

        # Plot intervals
        fig.append_trace(go.Scatter(
            x=gender_subset['wave'].tolist() + gender_subset['wave'][::-1].tolist(),
            y=gender_subset['higher'].tolist() + gender_subset['lower'][::-1].tolist(),
            fill='toself',
            fillcolor=rgba,
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False,
        ), row=3*i, col=g)

# Update layout
fig['layout'].update(height=1200, width=800, xaxis_title="Wave", yaxis_title="Median")
fig['layout'].update(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.11,
    xanchor="left",
    x=0,
    font=dict(size=14),itemwidth=30
))

fig.add_vrect(
    x0="1", x1="2",
    y0=0, y1=1,
    fillcolor="rgba(145, 150, 149, 1)", opacity=0.3,
    layer="below", line_width=0,
)

fig.add_vrect(
    x0="13", x1="20",
    y0=0, y1=1,
    fillcolor="rgba(145, 150, 149, 1)", opacity=0.3,
    layer="below", line_width=0,
)

fig.add_vrect(
    x0="26", x1="33",
    y0=0, y1=1,
    fillcolor="rgba(194, 194, 194, 0.7)", opacity=0.3,
    layer="below", line_width=0,
)


fig.for_each_xaxis(lambda x: x.update(title = ''))
fig.for_each_yaxis(lambda y: y.update(title = ''))
fig.add_annotation(x=-0.08,y=0.5,textangle=-90,showarrow=False, font=dict(size=16),
                    text="Variance",
                    xref="paper", yref="paper")
fig.add_annotation(x=0.5,y=-0.05, textangle=0,showarrow=False, font=dict(size=16),
                    text="Wave",
                    xref="paper", yref="paper")


fig.update_xaxes(dtick="5",)

# fig.update_yaxes(matches='y')
fig.update_yaxes(range=[0, 150], row=1, col=2)
fig.update_yaxes(range=[0, 150], row=1, col=1)
fig.update_yaxes(range=[0, 150], row=4, col=2)
fig.update_yaxes(range=[0, 150], row=4, col=1)
fig.update_yaxes(range=[0, 150], row=7, col=2)
fig.update_yaxes(range=[0, 150], row=7, col=1)

fig.write_image(args['fig_dir'] / 'results' / "variance_components_linegraph.pdf")
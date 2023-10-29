import os
import numpy as np
import pandas as pd
import arviz as az
import xarray as xr
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

df = pd.read_csv(args['derived_dir'] / 'df_full.csv')

df_pop = pd.read_csv(os.path.join(args['cwd']/"data"/"population"/"germany-population-2011.csv"))
df_pop = df_pop[df_pop['age']<=85]
grouped_sum = df_pop.groupby(['gender'])['pop'].transform('sum')
df_pop['pop_pct'] = df_pop['pop'] / grouped_sum

# -------------------------- prop 0,1,2,4,9 --------------------------
xr_data = xr.open_dataset(args['output_dir'] / 'bnb_gp_awgtr_gen.nc')
data = merge_hdi(xr_data, 'prop')
data = data.rename(columns={'prop_dim_0':'gender', 'prop_dim_1':'age', 'prop_dim_2':'wave', 'prop_dim_3':'y',})
data['wave'] = data['wave'] + 1
data['gender'] = data['gender'].map({0:'Female', 1:'Male'})
data['age'] = data['age']
data['y'] = data['y'].map({0:0, 1:1, 2:2, 3:4, 4:9})



# Weighted according to age-sex for each wave
df_prt = df.groupby(['wave','pt_age','pt_sex']).size().reset_index().rename(columns={0:'count'})
df_prt = df_prt.rename(columns={'pt_sex':'gender', 'pt_age':'age', 'count':'part'})
grouped_sum = df_prt.groupby(['wave','gender'])['part'].transform('sum')
df_prt['part_pct'] = df_prt['part'] / grouped_sum

df_weight = pd.merge(df_prt, df_pop, 'left', on=['gender','age']).sort_values(['wave','gender','age'])
df_weight['weight'] = df_weight['pop_pct'] / df_weight['part_pct']

all_combinations = pd.DataFrame({
    'wave': data['wave'].unique().tolist() * 86 * 2,
    'age': list(range(86)) * len(data['wave'].unique()) * 2,
    'gender': ['Male'] * 86 * len(data['wave'].unique()) + ['Female'] * 86 * len(data['wave'].unique())
})
df_weight = pd.merge(all_combinations, df_weight, on=['wave', 'age', 'gender'], how='left')
df_weight['weight'].fillna(1, inplace=True)

# check
df_weight.groupby(['wave','gender']).sum()
df_weight['weight'].hist(bins=200)
df_weight = df_weight.drop(columns=['pop','pop_pct','part','part_pct'])

# merge df_weight with data
data_w = pd.merge(data, df_weight, 'left', on=['wave','gender','age'])
data_w.groupby(['gender','wave','y']).sum('weight')

def weighted_average(df, data_col, weight_col):
    return (df[data_col] * df[weight_col]).sum() / df[weight_col].sum()

data_w = data_w.groupby(['gender', 'wave', 'y']).apply(lambda x: pd.Series({
    'median_w': weighted_average(x, 'median', 'weight'),
    'higher_w': weighted_average(x, 'higher', 'weight'),
    'lower_w': weighted_average(x, 'lower', 'weight')
})).reset_index()


color_palette = px.colors.qualitative.Plotly
df_tmp = data[(data['age'] == 40) & (data['gender'].isin(['Male','Female']))]
df_tmp = data_w
fig = make_subplots(rows=1, cols=2, 
                    shared_yaxes=True, 
                    horizontal_spacing=0.05,
                    subplot_titles=['Male','Female'])
# For each unique repeat value
for y in df_tmp['y'].unique():
    subset = df_tmp[df_tmp['y'] == y]
    for c, gender in enumerate(['Male','Female'],start=1):
        gender_subset = subset[subset['gender'] == gender]
        
        line_dash = 'solid' #if gender == 'Male' else 'dash'
        color = color_palette[y % len(color_palette)]
        rgba = 'rgba' + str(px.colors.hex_to_rgb(color))[:-1] + ', 0.3)'
        # varname = {0:'Randomness', 1:'Liability', 2:'Proneness', 3:'Total'}[repeat]

        # Plot the median
        fig.append_trace(go.Scatter(
            x=gender_subset['wave'],
            y=gender_subset['median_w'],
            # name=r'$P(Y_i)>{}$'.format(y),
            name='>{}'.format(y),
            line=dict(dash=line_dash, color=color),
            legendgroup=f'Var {y}',
            showlegend=True if gender == 'Male' else False
        ), row=1, col=c)

        fig.append_trace(go.Scatter(
            x=gender_subset['wave'].tolist() + gender_subset['wave'][::-1].tolist(),
            y=gender_subset['higher_w'].tolist() + gender_subset['lower_w'][::-1].tolist(),
            fill='toself',
            fillcolor=rgba,
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False,
            legendgroup=f'Var {y}'
        ), row=1, col=c)

fig.update_layout(height=500, width=900, 
                  yaxis_title="Fraction of population",)

fig['layout'].update(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.3,
    xanchor="left",
    x=0,
    font=dict(size=14)
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
    fillcolor="rgba(194, 194, 194, 0.7)", opacity=0.4,
    layer="below", line_width=0,
)
fig.for_each_xaxis(lambda x: x.update(title = ''))
fig.add_annotation(x=0.5,y=-0.2, textangle=0,showarrow=False, font=dict(size=14),
                    text="Wave",
                    xref="paper", yref="paper")
fig.update_xaxes(dtick=5)
# fig.show()
fig.write_image(args['fig_dir'] / 'results' / "prop01249_weight.pdf")



import os
import xarray as xr
from pathlib import Path

import plotly
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


# -------------------------- Propotion of participants with 0 contacts --------------------------

xr_data = xr.open_dataset(args['output_dir'] / 'bnb_gp_awgtr_gen.nc')
data = merge_hdi(xr_data, 'zero')
data = data.rename(columns={'zero_dim_0':'gender', 'zero_dim_1':'age', 'zero_dim_2':'wave', 'zero_dim_3':'repeat',})
data['wave'] = data['wave'] + 1
data['gender'] = data['gender'].map({0:'Female', 1:'Male'})
data['age'] = data['age'].map({0:20, 1:40, 2:60, 3:80})


from plotly.colors import n_colors
color_palette = n_colors('rgb(5, 200, 200)', 'rgb(200, 10, 10)', 9, colortype='rgb')
ages = data['age'].unique()
fig = make_subplots(rows=2, cols=4, 
                    shared_yaxes=True, 
                    shared_xaxes=True,
                    horizontal_spacing=0.01,
                    vertical_spacing=0.03,
                    row_titles=['Male','Female'],
                    column_titles=['Age 20','Age 40','Age 60', 'Age 80'],
                    )

for i, age in enumerate(ages, start=1):
    age_df = data[(data['age'] == age)]    
    for repeat in age_df['repeat'].unique():
        subset = age_df[age_df['repeat'] == repeat]
        for c, gender in enumerate(['Male','Female'],start=1):
            gender_subset = subset[subset['gender'] == gender]
            
            line_dash = 'solid' #if gender == 'Male' else 'dash'
            color = color_palette[repeat % len(color_palette)]
            rgba = 'rgba' + str(color)[3:-1] + ', 0.075)'

            # Plot the median
            fig.append_trace(go.Scatter(
                x=gender_subset['wave'],
                y=gender_subset['median'],
                name=f'{repeat}-{gender}',
                line=dict(dash=line_dash, color=color),
                legendgroup=f'Var {repeat}',
                # showlegend=True if age == ages[0] else False
                showlegend=False,
            ), row=c, col=i)

            fig.append_trace(go.Scatter(
                x=gender_subset['wave'].tolist() + gender_subset['wave'][::-1].tolist(),
                y=gender_subset['higher'].tolist() + gender_subset['lower'][::-1].tolist(),
                fill='toself',
                fillcolor=rgba,
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                legendgroup=f'Var {repeat}'
            ), row=c, col=i)

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

fig.update_layout(height=800, width=1400, )
fig.for_each_xaxis(lambda x: x.update(title = ''))
fig.for_each_yaxis(lambda y: y.update(title = ''))
fig.add_annotation(x=-0.04,y=0.5,textangle=-90,showarrow=False, font=dict(size=16),
                    text="Fraction of participants with 0 contacts",
                    xref="paper", yref="paper")
fig.add_annotation(x=0.5,y=-0.07, textangle=0,showarrow=False, font=dict(size=16),
                    text="Wave",
                    xref="paper", yref="paper")

fig.update_xaxes(dtick="5",)


dummy_heatmap = go.Scatter(x=[None], y=[None], mode='markers',
                           marker=dict(
                               colorscale=color_palette, 
                               colorbar=dict(
                                   title='Repeat', x=0.5, y=-0.1, len=0.5, 
                                   thickness=20, xanchor='center', yanchor='top', orientation='h'
                               ),
                               cmin=1, cmax=9, colorbar_nticks=9
                           ), showlegend=False, hoverinfo='none')
fig.add_trace(dummy_heatmap)


fig.write_image(args['fig_dir'] / 'results' / "fatigue_fraction0.pdf")
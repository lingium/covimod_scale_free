import os
import numpy as np
import pandas as pd
import arviz as az
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
from utils import stan_model, make_fitting_data


stan_data_0 = make_fitting_data(args["derived_dir"] / "df_full.csv")
args["bnb_gp_awgtr"] = args["stan_dir"] / "bnb_gp_awgtr.stan"
bnb_model = stan_model(args["bnb_gp_awgtr"], recover=True, 
                            stan_data=stan_data_0, stan_save_dir=args["output_dir"] / 'bnb_gp_awgtr_save')


# -------------------------- trace plot with min R-hat --------------------------
def get_trace(fit, name, position=None):
    az_data = fit.draws_xr(name)
    dims = len(az_data.dims) - 2
    index = [name+'_dim_'+str(i) for i in range(dims)]
    data = az_data.to_dataframe().reset_index()
    if position is None:
        return data
    for i, pos in enumerate(position):
        data = data[data[index[i]]==pos].drop(columns=[index[i]])
    return data

variables = ['gp_a_l', 'gp_w_sigma', 'gp_a_l', 'gp_a_l', 'gp_a_sigma',]
params = [('gp_a_l', [1,2]), ('gp_w_sigma', None), ('gp_a_l', [1,3]), ('gp_a_l', [0,4]), ('gp_a_sigma', [0,4])]

traces = [get_trace(bnb_model.fit, k[0], k[1]) for k in params]

color_palette = px.colors.qualitative.Plotly
fig = make_subplots(rows=5, cols=2, 
                    horizontal_spacing=0.05,
                    vertical_spacing=0.03,
                    # subplot_titles=[f"Trace {i+1}" if j == 1 else f"Histogram {i+1}" for i in range(5) for j in range(2)],
                    column_titles=['Trace Plot', 'Histogram'])

# Load each dataset and create plots
for i,data in enumerate(traces):
    # Load the dataset
    variable = variables[i]
    
    # Create a trace plot for the left column
    for c,chain in enumerate(data['chain'].unique()):
        color = color_palette[c]
        print(color)
        fig.add_trace(go.Scatter(x=data[data['chain'] == chain]['draw'], 
                                 y=data[data['chain'] == chain][variable], 
                                 mode='lines', 
                                 name=f'Chain {chain}', 
                                 legendgroup=f'Chain {chain}',
                                 line=dict(color=color),
                                 showlegend=(i == 0)), # Only show legend for the first plot
                    row=i+1, col=1)

        fig.add_trace(go.Histogram(x=data[data['chain'] == chain][variable], 
                                   histnorm='probability density',
                                   showlegend=False,
                                   opacity=0.5,
                                    marker=dict(color=color), # set color to same as trace
                                   ), row=i+1, col=2)

# Update layout
fig['layout'].update(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.1,
    xanchor="left",
    x=0,
    font=dict(size=12)
))
fig.update_layout(height=1200, width=900)
fig.update_xaxes(title_text="Draw", row=5, col=1)
fig.update_xaxes(title_text="Parameter", row=5, col=2)
fig.update_layout(barmode='overlay')

fig.update_yaxes(title_text=r"$l_{3,M}$", row=1, col=1)
fig.update_yaxes(title_text=r"$\sigma_{T}$", row=2, col=1)
fig.update_yaxes(title_text=r"$l_{4,M}$", row=3, col=1)
fig.update_yaxes(title_text=r"$l_{5,F}$", row=4, col=1)
fig.update_yaxes(title_text=r"$\sigma_{5,F}$", row=5, col=1)

# fig.show()
fig.write_image(args['fig_dir'] / 'results' / "traceplot.pdf")
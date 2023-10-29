import os
import numpy as np
import pandas as pd
import scipy.stats as stats
import powerlaw
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from pathlib import Path
args = {}
args['cwd'] = Path(__file__).resolve().parent.parent.parent
args['data'] = args['cwd'] / "data"
args['csv_dir'] = args['data'] / 'covimod'
args['derived_dir'] = args['data'] / 'derived'
args['fig_dir'] = args['cwd'] / "figures"

import sys
sys.path.append(os.path.join(args['cwd'], 'src', 'python'))
from utils import poi_mle_fit, nb_mle_fit, bnb_mle_fit, beta_neg_binomial_cdf, zipf_cdf

# Load Data
df_full = pd.read_csv(args['derived_dir'] / "df_full.csv")

wave_group_levels = ["1-2", "3-12", "13-20", "21-25", "26-33"]


# -------------------------- loglog plot --------------------------

# Create subplots
fig = make_subplots(rows=1, cols=2, subplot_titles=("Linear Scale", "Log10 Scale"))
cols = px.colors.qualitative.Plotly

for i, wg in enumerate(wave_group_levels):
    for sex, linestyle in zip(["Male", "Female"], ["solid", "dash"]):
        data = df_full.loc[(df_full['wave_grp'] == wg) & (df_full['pt_sex'] == sex), "nhh_nct"]
        fig.add_trace(go.Scatter(x=sorted(data), y=np.arange(len(data), 0, -1) / len(data),
                                mode='lines', name=wg, line=dict(color=cols[i], dash=linestyle),
                                showlegend=(sex == "Male")), row=1, col=1)
        fig.add_trace(go.Scatter(x=sorted(data), y=np.arange(len(data), 0, -1) / len(data),
                                mode='lines', name=wg, line=dict(color=cols[i], dash=linestyle),
                                showlegend=False), row=1, col=2)

# Add legends for sex
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="male", line=dict(color="black")), row=1, col=1)
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="female", line=dict(color="black", dash="dash")), row=1, col=1)

# Linear plot details
fig.update_xaxes(title_standoff=0, row=1, col=1)
fig.update_yaxes(title_text='Fraction of participants reporting more contacts', title_standoff=0, row=1, col=1)

# Logarithmic plot details
fig.update_xaxes(type="log", title_standoff=0, row=1, col=2)
fig.update_yaxes(type="log", title_standoff=0, row=1, col=2)
fig.update_layout(width=1000, height=500, legend_title_text='Wave/Gender')

fig.for_each_xaxis(lambda x: x.update(title=''))
fig.add_annotation(x=0.5, y=-0.15, textangle=0, showarrow=False, font=dict(size=14),
                   text="Number of non-household contacts",
                   xref="paper", yref="paper")

fig.write_image(args['fig_dir'] / 'data' / "fig_8_1.pdf")



x_arr = np.linspace(1, 200, dtype=int)

fig = go.Figure()
for i,wg in enumerate(wave_group_levels):
    cols = px.colors.qualitative.Plotly
    data = df_full.loc[df_full['wave_grp']==wg, "nhh_nct"]
    fig.add_trace(go.Scatter(x=sorted(data), y=np.arange(len(data), 0, -1)/len(data), 
                            mode='lines', name=wg, line=dict(color=cols[i],),))
    poi_params = poi_mle_fit(data)
    nb_params = nb_mle_fit(data)
    fig.add_trace(go.Scatter(x=x_arr, y=1-stats.poisson.cdf(x_arr, poi_params),
                            mode='lines', name='Poisson', line=dict(color=cols[i], dash='dot'),
                            showlegend=False))
    fig.add_trace(go.Scatter(x=x_arr, y=1-stats.nbinom.cdf(x_arr, *nb_params),
                            mode='lines', name='NegBinom', line=dict(color=cols[i], dash='dash'),
                            showlegend=False))

fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="Data", line=dict(color="black")))
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="NegBinom", line=dict(color="black", dash="dash")))
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="Poisson", line=dict(color="black", dash="dot")))
fig.update_xaxes(type="log")
fig.update_yaxes(type="log")
fig.update_xaxes(title_text='', title_standoff = 0)
fig.update_yaxes(title_text='', title_standoff = 0)
fig.update_layout(width=500, height=500,)
fig.update_layout(legend_title_text='')
# make legend at bottom
fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.4,
    xanchor="left",
    x=0
))

fig.write_image(args['fig_dir'] / 'data' / "fig_8_2.pdf")





fig = go.Figure()
for i,wg in enumerate(wave_group_levels):
    cols = px.colors.qualitative.Plotly
    data = df_full.loc[df_full['wave_grp']==wg, "nhh_nct"]
    fig.add_trace(go.Scatter(x=sorted(data), y=np.arange(len(data), 0, -1)/len(data), 
                            mode='lines', name=wg, line=dict(color=cols[i],),))
    bnb_params = bnb_mle_fit(data)
    print(wg, bnb_params)
    zipf = powerlaw.Fit(data+1, discrete=True, xmin=1, xmax=np.Inf, fit_method='Likelihood')
    fig.add_trace(go.Scatter(x=x_arr, y=1-beta_neg_binomial_cdf(x_arr, *bnb_params),
                            mode='lines', name='BetaNegBinom', line=dict(color=cols[i], dash='dash'),
                            showlegend=False))
    fig.add_trace(go.Scatter(x=x_arr, 
                            y=1-zipf_cdf(x_arr, zipf.alpha, None),  #zipf.power_law.ccdf(x_arr),
                            mode='lines', name='Zipf', line=dict(color=cols[i], dash='dot'),
                            showlegend=False))
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="Data", line=dict(color="black")))
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="BetaNegBinom", line=dict(color="black", dash="dash")))
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name="Zipf", line=dict(color="black", dash="dot")))
fig.update_xaxes(type="log")
fig.update_yaxes(type="log")
fig.update_xaxes(title_text='', title_standoff = 0)
fig.update_yaxes(title_text='', title_standoff = 0)
fig.update_layout(width=500, height=500,)
fig.update_layout(legend_title_text='')
fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.4,
    xanchor="left",
    x=0
))

fig.write_image(args['fig_dir'] / 'data' / "fig_8_3.pdf")






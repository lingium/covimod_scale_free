import os
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objs as go
import plotly.offline as pyo
from plotly.subplots import make_subplots
from plotly.express.colors import sample_colorscale

from pathlib import Path
args = {}
args['cwd'] = Path(__file__).resolve().parent.parent.parent
args['data'] = args['cwd'] / "data"
args['csv_dir'] = args['data'] / 'covimod'
args['derived_dir'] = args['data'] / 'derived'
args['fig_dir'] = args['cwd'] / "figures"


# -------------------------- show BNB changes with parameters --------------------------

def beta_neg_binomial_pmf_vec(r, a, b, y_max):
    from scipy.special import gammaln, betaln
    y = np.arange(y_max + 1)
    lprobs = betaln(r+y,a+b) - betaln(r,a) + gammaln(y+b) - gammaln(y+1) - gammaln(b)
    return np.exp(lprobs)


y_max = 20
y_max_loglog = 200
N = 20
color_scale = sample_colorscale('jet', list(np.linspace(0, 1, N)))

fig = make_subplots(rows=1, cols=2, subplot_titles=("Linear Scale", "Log-Log Scale"))
a = 10
b = 5
r_values = np.linspace(1, 20, N)

# Left Panel: Linear scale
for i, r in enumerate(r_values):
    probs = beta_neg_binomial_pmf_vec(r, a, b, y_max)
    fig.add_trace(go.Scatter(x=np.arange(y_max + 1), y=probs, mode='lines', 
                            name=f'r={r:.2f}', line=dict(color=color_scale[i])), row=1, col=1)

# Right Panel: Log-Log scale
for i, r in enumerate(r_values):
    probs = beta_neg_binomial_pmf_vec(r, a, b, y_max_loglog)
    fig.add_trace(go.Scatter(x=np.arange(y_max_loglog + 1), y=probs, mode='lines', 
                            line=dict(color=color_scale[i]), showlegend=False), row=1, col=2)

fig.update_yaxes(type="log", row=1, col=2)
fig.update_xaxes(type="log", row=1, col=2)

# Add color bar to the right subplot
dummy_heatmap = go.Scatter(x=[None], y=[None], mode='markers', 
                           marker=dict(colorscale='jet', colorbar=dict(title='r values', x=1.03),
                                       cmin=r_values[0], cmax=r_values[-1], colorbar_nticks=len(r_values)))
fig.add_trace(dummy_heatmap)

fig.update_layout(height=500, width=1000,
                  showlegend=False,)
# fig.show()
fig.write_image(args['fig_dir'] / 'background' / "BNB_change_r.pdf")


y_max = 20
y_max_loglog = 200
N = 20
color_scale = sample_colorscale('jet', list(np.linspace(0, 1, N)))

fig = make_subplots(rows=1, cols=2, subplot_titles=("Linear Scale", "Log-Log Scale"))
r = 10
b = 5
a_values = np.linspace(5, 24, N)

# Left Panel: Linear scale
for i, a in enumerate(a_values):
    probs = beta_neg_binomial_pmf_vec(r, a, b, y_max)
    fig.add_trace(go.Scatter(x=np.arange(y_max + 1), y=probs, mode='lines', 
                              name=f'a={a:.2f}', line=dict(color=color_scale[i])), row=1, col=1)

# Right Panel: Log-Log scale
for i, a in enumerate(a_values):
    probs = beta_neg_binomial_pmf_vec(r, a, b, y_max_loglog)
    fig.add_trace(go.Scatter(x=np.arange(y_max_loglog + 1), y=probs, mode='lines', 
                              line=dict(color=color_scale[i]), showlegend=False), row=1, col=2)

fig.update_yaxes(type="log", row=1, col=2)
fig.update_xaxes(type="log", row=1, col=2)

# Add color bar to the right subplot
dummy_heatmap = go.Scatter(x=[None], y=[None], mode='markers', 
                           marker=dict(colorscale='jet', colorbar=dict(title='a values', x=1.03),
                                       cmin=a_values[0], cmax=a_values[-1], colorbar_nticks=len(a_values)))
fig.add_trace(dummy_heatmap)

fig.update_layout(height=500, width=1000,
                  showlegend=False,)
# # fig.show()
fig.write_image(args['fig_dir'] / 'background' / "BNB_change_a.pdf")
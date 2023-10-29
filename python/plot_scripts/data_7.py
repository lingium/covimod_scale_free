import os
import numpy as np
import pandas as pd
import plotly.express as px

from pathlib import Path
args = {}
args['cwd'] = Path(__file__).resolve().parent.parent.parent
args['data'] = args['cwd'] / "data"
args['csv_dir'] = args['data'] / 'covimod'
args['derived_dir'] = args['data'] / 'derived'
args['fig_dir'] = args['cwd'] / "figures"

# load files
df = pd.read_csv(args['derived_dir'] / "df_septypes.csv")

# -------------------------- Substantial overdispersion --------------------------

df_plot = df.groupby(['wave', 'pt_sex']).agg({'nhh_nct': ['mean', 'var']}).reset_index()
df_plot.columns = df_plot.columns.droplevel()
df_plot.columns = ['wave', 'pt_sex', 'mean', 'var']
df_plot['var_mean_ratio'] = df_plot['var'] / df_plot['mean']

fig = px.bar(df_plot, x='wave', y='var_mean_ratio', color='pt_sex',
             labels={'var_to_mean': 'Variance-to-Mean Ratio', 'wave': 'Wave'},
             color_discrete_map={'Male': 'blue', 'Female': 'red'},
             barmode='group',)
fig.update_layout(barmode='group', 
                  xaxis_title="Wave", yaxis_title="Variance-mean ratio")
fig.update_xaxes(dtick=1, tickangle=45)
fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.3,
    xanchor="left",
    x=0,
    title='Gender'
))
fig.update_traces(opacity=0.8)
fig.update_layout(height=450, width=900,)
# fig.show()
fig.write_image(args['fig_dir'] / 'data' / "fig_7.pdf")
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
df_part = pd.read_csv(args['csv_dir'] / "part_data.csv")
df = pd.read_csv(args['derived_dir'] / "df_septypes.csv")
df_full = pd.read_csv(args['derived_dir'] / "df_full.csv")



# -------------------------- repeated sampling structure --------------------------

df_rpnb = df[['wave','rp_nb']].groupby(['wave','rp_nb']).size().reset_index(name='count')
total_counts = df_rpnb.groupby('wave')['count'].sum()
df_rpnb['proportion'] = df_rpnb.apply(lambda row: row['count'] / total_counts[row['wave']], axis=1)

df_rpnb['text'] = df_rpnb['rp_nb'].where(df_rpnb['proportion'] > 0.10, '')

fig = px.bar(df_rpnb, x='wave', y='proportion', color='rp_nb', 
             text='text',
             labels={'wave':'Wave', 'proportion':'Proportion of repeated participants', 'rp_nb':'Repeats'},
             color_continuous_scale=["rgb(22,150,210)", "rgb(219,43,39)", "rgb(253,191,17)", "magenta"],
            )

fig.update_xaxes(dtick=1, tickangle=0)
fig.update_layout(height=600, width=1000, 
                coloraxis_colorbar=dict(dtick=2))
fig.update_traces(textposition="inside")
fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
# fig.show()
fig.write_image(args['fig_dir'] / 'data' / "fig_2.pdf")
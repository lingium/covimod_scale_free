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

df = pd.read_csv(args['derived_dir'] / "df_septypes.csv")

# -------------------------- Mean of contact counts for each repeated sampling number --------------------------


df_rpnb = df.groupby('rp_nb')[['hh_nct', 'nhh_nct', 'grp_nct']].mean().reset_index()
df_rpnb['text'] = df.groupby('rp_nb')['hh_nct'].size().reset_index(name='size')['size']
df_rpnb = pd.melt(df_rpnb, id_vars=['rp_nb', 'text'], value_vars=['hh_nct', 'nhh_nct', 'grp_nct'],
                    var_name='contact_type', value_name='mean_contact_count')
# keep text only for nhh_nct type
df_rpnb['text'] = df_rpnb['text'].where(df_rpnb['contact_type'] == 'nhh_nct', '')


fig = px.bar(df_rpnb, x='rp_nb', y='mean_contact_count', color='contact_type',
                text='text', 
                barmode='overlay',
                labels={'hh_nct':'Household contact', 'nhh_nct':'Non-household contacts', 'rp_nb':'Repeats'},
                )
fig.update_xaxes(dtick=1, tickangle=0)
fig.update_layout(height=500, width=800,
                  yaxis_title="Mean of reported contacts",)
fig.for_each_trace(lambda t: t.update(name=t.name.replace("nhh_nct", "Non-household").replace("hh_nct", "Household").replace("grp_nct", "Group")))
fig.update_layout(legend_title_text='Contact type',
                  height=500, width=900,)
fig.update_traces(textposition="outside")
fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0, ))
# fig.show()
fig.write_image(args['fig_dir'] / 'data' / "fig_6.pdf")
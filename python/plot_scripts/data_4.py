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

df_part = pd.read_csv(args['csv_dir'] / "part_data.csv")
df = pd.read_csv(args['derived_dir'] / "df_septypes.csv")
df_full = pd.read_csv(args['derived_dir'] / "df_full.csv")



# -------------------------- Histograms for reported contact frequency  --------------------------
# add wave_grp col from df_full to df
df['wave_grp'] = df_full['wave_grp']
data = df[['wave_grp', 'hh_nct', 'nhh_nct', 'grp_nct', 'pt_age', 'pt_sex', ]]


df_long = pd.melt(data, id_vars=['pt_age', 'pt_sex', 'wave_grp'], value_vars=['hh_nct', 'nhh_nct', 'grp_nct'],
                  var_name='contact_type', value_name='contact_count')


fig = px.histogram(df_long, x="pt_age", y="contact_count",
                   color="contact_type", facet_col="pt_sex", facet_row="wave_grp",
                   barmode="overlay",
                   category_orders={"pt_sex": ["Male", "Female"], "contact_type": ["hh_nct", "nhh_nct", "grp_nct"]},
                   labels={"pt_age": "Age", 
                          "pt_sex": "Gender", 
                          "wave_grp": "Wave Group", 
                          "contact_type": "Contact Type",
                          "count": "Count"},
                )


fig.update_layout(height=1000, width=800,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="left", x=0))
fig.update_traces(marker={"opacity": 0.7})
# modify legend entries
fig.for_each_trace(lambda t: t.update(name=t.name.replace("nhh_nct", "Non-household")
                                                 .replace("hh_nct", "Household")
                                                 .replace("grp_nct", "Group")))
fig.for_each_xaxis(lambda x: x.update(title = ''))
fig.for_each_yaxis(lambda y: y.update(title = ''))
fig.add_annotation(x=-0.08,y=0.5,textangle=-90,showarrow=False, font=dict(size=14),
                    text="Frequency",
                    xref="paper", yref="paper")
fig.add_annotation(x=0.5,y=-0.05, textangle=0,showarrow=False, font=dict(size=14),
                    text="Participant age",
                    xref="paper", yref="paper")


df_tmp = df.groupby(['wave_grp','pt_sex']).agg({"hh_nct": "sum", "nhh_nct": "sum", "grp_nct":"sum"}).reset_index()
df_tmp['total_nct'] = df_tmp['hh_nct'] + df_tmp['nhh_nct'] + df_tmp['grp_nct']
df_tmp = pd.pivot(df_tmp, index='pt_sex', columns='wave_grp', values='total_nct').reset_index(drop=True).T

for row, row_figs in enumerate(fig._grid_ref):
    row = row+1
    for col, col_fig in enumerate(row_figs):
        col = col+1
        # print(row, col)
        fig.add_annotation(x=60,y=630, textangle=0, showarrow=False, font=dict(size=12),
                    text="Reported contacts: {}".format(df_tmp.iloc[row-1, col-1]),
                    xref="paper", yref="paper",
                    row=len(fig._grid_ref)+1-row, col=col)

def waveGroupPolicy(text):
    if "Wave Group=" in text:
        wave_grp = text.split("=")[1]
        if wave_grp == '1-2':
            return "1st lockdown (1-2)"
        elif wave_grp == '3-12':
            return "1st easing (3-12)"
        elif wave_grp == '13-20':
            return "2nd lockdown (13-20)"
        elif wave_grp == '21-25':
            return "2nd easing (21-25)"
        elif wave_grp == '26-33':
            return "Vaccination check (26-33)"
        else:
            return ""
    if "Gender=" in text:
        return text.split("=")[1]
    else:
        return text

fig.for_each_annotation(lambda a: a.update(text=waveGroupPolicy(a.text)))

fig.write_image(args['fig_dir'] / 'data' / "fig_4.pdf")

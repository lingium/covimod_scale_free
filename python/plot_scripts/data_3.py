import os
import numpy as np
import pandas as pd
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

# Load Data
df_part = pd.read_csv(args['csv_dir'] / "part_data.csv")
df = pd.read_csv(args['derived_dir'] / "df_septypes.csv")
df_full = pd.read_csv(args['derived_dir'] / "df_full.csv")
df_f1 = df.loc[df["rp_nb"] == 1,].drop(columns=["rp_nb"])

wave_group_levels = ["1-2", "3-12", "13-20", "21-25", "26-33"]

df_wavegrp_time = df_full[['wave_grp','date']].drop_duplicates() \
    .rename(columns={"wave_grp": "wave"})
df_wavegrp_time["date"] = pd.to_datetime(df_wavegrp_time["date"], format="%Y-%m-%d")
df_wavegrp_time = df_wavegrp_time.groupby("wave").agg({"date": [np.min, np.max]})
df_wavegrp_time.columns = df_wavegrp_time.columns.droplevel(0)
df_wavegrp_time = df_wavegrp_time.rename(columns={"amin": "start_date", "amax": "end_date"})
df_wavegrp_time = df_wavegrp_time.reset_index()

df_pop = pd.read_csv(os.path.join(args['data'], "population", "germany-population-2011.csv"))
df_pop = df_pop.rename(columns={"age": "pt_age", "gender": "pt_sex"})
grouped_sum = df_pop.groupby(['pt_sex'])['pop'].transform('sum')
df_pop['pop_pct'] = df_pop['pop'] / grouped_sum


# -------------------------- age-sex structure of participants --------------------------

data = df_full[['wave_grp','pt_age', 'pt_sex']].groupby(['wave_grp','pt_age', 'pt_sex']).size().reset_index(name='count')
# calculate the count percentage
grouped_sum = data.groupby(['wave_grp', 'pt_sex'])['count'].transform('sum')
data['count_pct'] = data['count'] / grouped_sum

# Verify that the sum is 1
data.groupby(['wave_grp', 'pt_sex'])[['count_pct']].transform('sum')
df_pop.groupby([ 'pt_sex'])[['pop_pct']].transform('sum')

subplotTitles = ["First lockdown (waves 1-2)", 
                "First easing (waves 3-12)", 
                "Second lockdown (waves 13-20)", 
                "Second easing (waves 21-25)", 
                "Vaccination check (waves 26-33)"]

# create title for each subplot like 1st lockdown (1-2) <br> N=1881, 06/11 to 06/22/2020
subplotTitles = ["{} <br><sup> N={}, {} to {}<sup> ".format(subplotTitles[i],
                data[data['wave_grp']==wave_grp]['count'].sum(),
                df_wavegrp_time[df_wavegrp_time['wave']==wave_grp]['start_date'].iloc[0].strftime("%m/%d/%Y"),
                df_wavegrp_time[df_wavegrp_time['wave']==wave_grp]['end_date'].iloc[0].strftime("%m/%d/%Y"))
                    for i, wave_grp in enumerate(wave_group_levels)]


for i, wave_grp in enumerate(wave_group_levels):

    fig = px.bar(
        data[data['wave_grp']==wave_grp],
        y="pt_age",
        x="count_pct",
        facet_col="pt_sex",
        facet_col_spacing=10 ** -9,
        color="pt_sex",
        color_discrete_sequence=['rgb(99, 110, 250)', 'rgb(239, 85, 59)'],
        orientation='h',
        labels={"pt_age": "Age", "pt_sex": "Gender",},
        barmode="overlay",
        opacity=1,
    )

    fig.update_layout(
        yaxis2={"side": "right", "matches": None, "showticklabels": False},
        yaxis={"showticklabels": True},
        xaxis={ "nticks": 5, "range":[0.055,0],}, #"autorange": "reversed",
        xaxis2={"matches": None, "nticks": 5, "range":[0, 0.055],},
        showlegend=False,
        title_text=subplotTitles[i],
        title_x=0.11,
        title_y=0.95, 
    )

    for ax, sex in zip([('x','y'),('x2','y2')], ["Male","Female"]):
        fig.add_trace(
            go.Bar(x=df_pop[df_pop['pt_sex']==sex]['pop_pct'], 
                    y=df_pop['pt_age'], 
                    orientation='h',
                    opacity=0.7,
                    marker=dict(color='rgba(58, 71, 80, 0)',
                                line=dict(color='rgba(58, 71, 80, 0.7)', width=1),),
                    xaxis=ax[0], yaxis=ax[1]),)

    def changeAnnotation(text):
        if "Gender=" in text:
            return text.split("=")[1]
        else:
            return text

    fig.for_each_annotation(lambda a: a.update(text=changeAnnotation(a.text)))

    # change xaxis tick format to percent with 0 decimal
    fig.update_xaxes(tickformat=".0%")

    fig.for_each_xaxis(lambda x: x.update(title = ''))
    fig.add_annotation(x=0.5,y=-0.15, textangle=0,showarrow=False, font=dict(size=14),
                        text="Percent",
                        xref="paper", yref="paper")
    
    fig.update_layout(#margin=dict(l=10, r=10, t=10, b=10),
                      height=450, width=550,)

    # fig.show()
    fig.write_image(args['fig_dir'] / 'data' / "fig_4_{}.pdf".format(i+1))



fig = px.bar(
    data,
    y="pt_age",
    x="count_pct",
    facet_col="pt_sex",
    facet_col_spacing=10 ** -9,
    color="pt_sex",
    color_discrete_sequence=['rgb(99, 110, 250)', 'rgb(239, 85, 59)'],
    orientation='h',
    labels={"pt_age": "Age", "pt_sex": "Gender",},
    barmode="overlay",
    opacity=1,
)

fig.update_layout(
    yaxis2={"side": "right", "matches": None, "showticklabels": False},
    yaxis={"showticklabels": True},
    xaxis={ "nticks": 5, "range":[0.055,0],}, #"autorange": "reversed",
    xaxis2={"matches": None, "nticks": 5, "range":[0, 0.055],},
    showlegend=False,
    title_text="Total (waves 1-33) <br><sup> N=59414, 04/30 to 12/31/2021<sup>",
    title_x=0.11,
    title_y=0.95, 
)

for ax, sex in zip([('x','y'),('x2','y2')], ["Male","Female"]):
    fig.add_trace(
        go.Bar(x=df_pop[df_pop['pt_sex']==sex]['pop_pct'], 
                y=df_pop['pt_age'], 
                orientation='h',
                opacity=0.7,
                marker=dict(color='rgba(58, 71, 80, 0)',
                            line=dict(color='rgba(58, 71, 80, 0.7)', width=1),),
                xaxis=ax[0], yaxis=ax[1]),)

def changeAnnotation(text):
    if "Gender=" in text:
        return text.split("=")[1]
    else:
        return text

fig.for_each_annotation(lambda a: a.update(text=changeAnnotation(a.text)))

# change xaxis tick format to percent with 0 decimal
fig.update_xaxes(tickformat=".0%")

fig.for_each_xaxis(lambda x: x.update(title = ''))
fig.add_annotation(x=0.5,y=-0.15, textangle=0,showarrow=False, font=dict(size=14),
                    text="Percent",
                    xref="paper", yref="paper")

fig.update_layout(#margin=dict(l=10, r=10, t=10, b=10),
                    height=450, width=550,)

# fig.show()
fig.write_image(args['fig_dir'] / 'data' / "fig_4_6.pdf")

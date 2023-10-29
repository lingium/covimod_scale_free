import os
import numpy as np
import pandas as pd
import plotly.graph_objs as go

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

# -------------------------- waves and time mapping --------------------------
df_waves_time = df_part[['wave_0','date']].drop_duplicates() \
    .rename(columns={"wave_0": "wave"})
df_waves_time["date"] = pd.to_datetime(df_waves_time["date"], format="%Y-%m-%d")
df_waves_time = df_waves_time.groupby("wave").agg({"date": [np.min, np.max]})
df_waves_time.columns = df_waves_time.columns.droplevel(0)
df_waves_time = df_waves_time.rename(columns={"amin": "start_date", "amax": "end_date"})
df_waves_time = df_waves_time.reset_index()
df_waves_time.to_csv(args['derived_dir'] / 'waves_time.csv', index=False)

df_wavegrp_time = df_full[['wave_grp','date']].drop_duplicates() \
    .rename(columns={"wave_grp": "wave"})
df_wavegrp_time["date"] = pd.to_datetime(df_wavegrp_time["date"], format="%Y-%m-%d")
df_wavegrp_time = df_wavegrp_time.groupby("wave").agg({"date": [np.min, np.max]})
df_wavegrp_time.columns = df_wavegrp_time.columns.droplevel(0)
df_wavegrp_time = df_wavegrp_time.rename(columns={"amin": "start_date", "amax": "end_date"})
df_wavegrp_time = df_wavegrp_time.reset_index()


# -------------------------- cases, deaths and stringency index data --------------------------
df_strict = pd.read_csv(os.path.join(args['data'], "population", "OxCGRT_timeseries_StringencyIndex_v1.csv"))
df_strict = df_strict[df_strict['CountryName']=='Germany']
df_strict = df_strict.iloc[:,7:]
df_strict = pd.melt(df_strict, id_vars=[], var_name='date', value_name='strictness_index')
df_strict = df_strict.dropna()
df_strict['date'] = pd.to_datetime(df_strict['date'], format='%d%b%Y')


df_cases = pd.read_csv(os.path.join(args['data'], "population", "time_series_covid19_confirmed_global.csv"))
df_deaths = pd.read_csv(os.path.join(args['data'], "population", "time_series_covid19_deaths_global.csv"))
df_cases = df_cases[df_cases['Country/Region']=='Germany']
df_deaths = df_deaths[df_deaths['Country/Region']=='Germany']
df_cases = df_cases.drop(columns=['Province/State', 'Country/Region', 'Lat', 'Long'])
df_deaths = df_deaths.drop(columns=['Province/State', 'Country/Region', 'Lat', 'Long'])
df_cases = pd.melt(df_cases, id_vars=[], var_name='date', value_name='cum_cases')
df_deaths = pd.melt(df_deaths, id_vars=[], var_name='date', value_name='cum_deaths')
df_cases['date'] = pd.to_datetime(df_cases['date'], format="%m/%d/%y")
df_deaths['date'] = pd.to_datetime(df_deaths['date'], format="%m/%d/%y")
df_cases_deaths = pd.merge(df_cases, df_deaths, on=['date'])
df_cases_deaths['daily_cases'] = df_cases_deaths['cum_cases'].diff().fillna(0).astype(int)
df_cases_deaths['daily_deaths'] = df_cases_deaths['cum_deaths'].diff().fillna(0).astype(int)
df_cases_deaths = pd.merge(df_cases_deaths, df_strict, on=['date'], how='left')


df_pop = pd.read_csv(os.path.join(args['data'], "population", "germany-population-2011.csv"))
df_pop = df_pop.rename(columns={"age": "pt_age", "gender": "pt_sex"})
grouped_sum = df_pop.groupby(['pt_sex'])['pop'].transform('sum')
df_pop['pop_pct'] = df_pop['pop'] / grouped_sum



# -------------------------- daily cases & cum deaths --------------------------

# only keep the data until 2022-02-01
data = df_cases_deaths[df_cases_deaths['date']<='2022-01-10']

# Create color list for waves
color_list = ['lightgrey', 'lightblue', 'lightgreen', 'lightyellow', 'lightpink']

# Add color to df_waves_time
df_waves_time['color'] = df_waves_time['wave'].apply(lambda x: color_list[0] if x <= 2 else 
                                               color_list[1] if x <= 12 else 
                                               color_list[2] if x <= 20 else 
                                               color_list[3] if x <= 25 else 
                                               color_list[4])


fig = go.Figure()

fig.update_layout(
    xaxis=dict(
        anchor='y3', 
    ),
    yaxis= dict(
        anchor='x', side="left", 
        domain=[0.52, 1.0],
        title_text="Daily Cases", nticks=10,
        ),
    yaxis2=dict(
        anchor='x',
        overlaying='y',
        side='right',
        # position=0.15,
        range=[0, 110],
        title_text="Strictness Index (%)", nticks=10,
        
    ),
    yaxis3=dict(
        anchor="x",
        side="left",
        domain=[0.0, 0.48],
        title_text="Cumulative Deaths", nticks=10,
    ),
    yaxis4=dict(
        anchor="x",
        overlaying="y3",
        side="right",
        range=[0, 110],
        title_text="Strictness Index (%)", nticks=10,
    ),
)

# Add daily_cases bar plot to the first subplot
fig.add_trace(
    go.Bar(x=data["date"], y=data["daily_cases"], 
           name="Daily Cases", marker_color='rgb(252, 36, 3)', 
            xaxis='x', yaxis="y"),
    # row=1, col=1
)

# Add 7-day moving average of daily_cases line to the first subplot
fig.add_trace(
    go.Scatter(x=data["date"], y=data['daily_cases'].rolling(7).mean(), 
               mode="lines", name="Endpoints Line (Daily Cases)",
               line=dict(color='rgb(100,100,100)', width=1.5), 
            xaxis='x', yaxis="y"),
    # row=1, col=1
)

# Add strictness_index line to the first subplot
fig.add_trace(
    go.Scatter(x=data["date"], y=data["strictness_index"], 
               mode="lines", name="Strictness Index",
               line=dict(color='rgb(0,128,255)', width=1.5), 
            xaxis='x', yaxis="y2",),
    # row=1, col=1,
)

# Add cum_deaths bar plot to the second subplot
fig.add_trace(
    go.Bar(x=data["date"], y=data["cum_deaths"], 
           name="Cumulative Deaths", marker_color='rgb(252, 186, 3)', 
            xaxis='x', yaxis="y3"),
    # row=2, col=1
)

# Add strictness_index line to the 2nd subplot
fig.add_trace(
    go.Scatter(x=data["date"], y=data["cum_deaths"], 
               mode="lines", name="Cumulative Deaths",
               line=dict(color='rgb(100,100,100)', width=1.5), 
            xaxis='x', yaxis="y3",),
    # row=1, col=1,
)

# Add strictness_index line to the second subplot
fig.add_trace(
    go.Scatter(x=data["date"], y=data["strictness_index"], 
               mode="lines", name="Strictness Index",
               line=dict(color='rgb(0,128,255)', width=1.5), 
            xaxis='x', yaxis="y4",),
    # ),row=2, col=1
)

anno_list = [1,3,13,21,26,33]
for _, row in df_waves_time.iterrows():
    fig.add_vrect(
        x0=row['start_date'], x1=row['end_date'], 
        fillcolor=row['color'], opacity=0.3,
        line_width=0,
        row=1, col="all",
        annotation = dict(
            # appear when the wave in anno_list
            visible=True if row['wave'] in anno_list else False,
            text="{}".format(row['wave']),),
        xanchor="x",
        # annotation_position="inside",
        # annotation_textangle=-90,
    )

# Update xaxis properties
fig.update_xaxes(
    tickangle=-45,
    title_text="Date",
    dtick="M1",
    tickformat="%b %y",
)

# Update layout
fig.update_layout(height=600, width=900, 
                  showlegend=False,
                  bargap=0)

for shape in fig.layout.shapes:
    shape["yref"]="paper"


# # fig.show()
fig.write_image(args['fig_dir'] / 'data' / "fig_1.pdf")
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import plotly.graph_objs as go

args = {}
args["seed"] = 1234
args["main"] = Path(__file__).resolve()
args["cwd"] = args["main"].parent.parent.parent
args["stan_dir"] = args["cwd"] / "model" / "bnb"
args["derived_dir"] = args["cwd"] / "data" / "derived"
args["fig_dir"] = args["cwd"] / "figures"

sys.path.append(os.path.join(args["cwd"], "src", "python"))
from utils import stan_model, merge_hdi, make_fitting_data

stan_data_0 = make_fitting_data(args["derived_dir"] / "df_full.csv")
args["bnb_gp_awgtr"] = args["stan_dir"] / "bnb_gp_awgtr.stan"
bnb_model = stan_model(args["bnb_gp_awgtr"], recover=True, stan_data=stan_data_0)


# -------------------------- Posterior distribution of ρ_r --------------------------

df_rho = pd.DataFrame(bnb_model.fit.stan_variable("bnb_rho"))
df_rho = df_rho.stack().reset_index()
df_rho.columns = ["sample", "rp_nb", "bnb_rho"]

from plotly.colors import n_colors

categories = df_rho["rp_nb"].unique()
colors = n_colors("rgb(5, 200, 200)", "rgb(200, 10, 10)", 26, colortype="rgb")

fig = go.Figure()
for cat, color in zip(categories, colors):
    data_line = df_rho[df_rho["rp_nb"] == cat]["bnb_rho"]
    fig.add_trace(go.Violin(y=data_line, line_color=color, points=False, orientation="v", side="negative", width=1.8))

fig.update_layout(
    height=550,
    width=900,
    showlegend=False,
    yaxis_title=r"$\rho_{r}$",
    xaxis_title="Repeats",
)

# change x axis tick labels
fig.update_xaxes(ticktext=[str(i) for i in range(1, 27)], tickvals=[i for i in range(0, 27)])
fig.write_image(args["fig_dir"] / "results" / "param_rho.pdf", format="pdf")


# -------------------------- Posterior time effect f(t) --------------------------

data = merge_hdi(bnb_model.fit, "gp_w_f")
data = data.rename(columns={"gp_w_f_dim_0": "wave"})
data["wave"] = data["wave"] + 1


# get the middle data for each wave from start_date and end_date
df_waves_time = pd.read_csv(args["derived_dir"] / "waves_time.csv")
df_waves_time["start_date"] = pd.to_datetime(df_waves_time["start_date"])
df_waves_time["end_date"] = pd.to_datetime(df_waves_time["end_date"])
df_waves_time["middle_date"] = (
    df_waves_time["start_date"] + (df_waves_time["end_date"] - df_waves_time["start_date"]) / 2
)
df_waves_time["middle_date"] = df_waves_time["middle_date"].dt.date
data = pd.merge(data, df_waves_time[["wave", "middle_date"]], how="left", on="wave")


fig = go.Figure()
fig.add_trace(
    go.Scatter(x=data["middle_date"], y=data["median"], mode="markers+lines", name="posterior", showlegend=False)
)
fig.add_trace(
    go.Scatter(
        x=data["middle_date"].tolist() + data["middle_date"][::-1].tolist(),
        y=data["higher"].tolist() + data["lower"].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.3)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
    ),
)

fig.add_vrect(
    x0=df_waves_time["middle_date"][0],
    x1=df_waves_time["middle_date"][1],
    line_width=0,
    fillcolor="rgba(145, 150, 149, 1)",
    opacity=0.5,
)

fig.add_vrect(
    x0=df_waves_time["middle_date"][12],
    x1=df_waves_time["middle_date"][19],
    line_width=0,
    fillcolor="rgba(145, 150, 149, 1)",
    opacity=0.5,
)

fig.add_vrect(
    x0=df_waves_time["middle_date"][25],
    x1=df_waves_time["middle_date"][32],
    line_width=0,
    fillcolor="rgba(194, 194, 194, 0.7)",
    opacity=0.5,
    name="Lockdown",
)

fig.update_xaxes(
    tickangle=-45,
    title_text="Date",
    dtick="M1",
    tickformat="%b %y",
)

fig.update_layout(
    height=550,
    width=900,
    showlegend=False,
    yaxis_title=r"$f(t)$",
    xaxis_title="Wave",
)
fig.write_image(args["fig_dir"] / "results" / "param_f_t.pdf", format="pdf")

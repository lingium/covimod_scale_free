import re
import os
import numpy as np
import pandas as pd


args = {}
args['seed'] = 1234
args['cwd'] = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) # current root working directory
args['csv_dir'] = os.path.join(args['cwd'], "data", 'covimod')
args['derived_dir'] = os.path.join(args['cwd'], "data", 'derived')

# load csv files
df_hh = pd.read_csv(os.path.join(args['csv_dir'], "hh_data.csv"))
df_nhh = pd.read_csv(os.path.join(args['csv_dir'], "non_hh_data.csv"))
df_part = pd.read_csv(os.path.join(args['csv_dir'], "part_data.csv"))

# -------------------------- process non-household data --------------------------
tlb_nhh = df_nhh.loc[:, ["wave", "new_id"]] \
    .groupby(["wave", "new_id"]) \
    .size() \
    .reset_index(name="nhh_nct") \
    .sort_values(by=["new_id","wave"]) \
    .rename(columns={"new_id": "id"})


# -------------------------- process household data --------------------------
tlb_hh = df_hh.loc[df_hh.hh_met_this_day=="Yes", ["wave", "new_id"]] \
    .groupby(["wave", "new_id"]) \
    .size() \
    .reset_index(name="hh_nct") \
    .sort_values(by=["new_id","wave"]) \
    .rename(columns={"new_id": "id"})


# -------------------------- process participants data --------------------------
dpart = df_part.rename(columns={'new_id': 'id', 'wave_0': 'wave', 'age_0': 'pt_age', 'sex': 'pt_sex', 'kreis_0': 'pt_region'})

dpart = dpart.loc[~dpart['pt_sex'].str.contains(r'Prefer not to answer|Don’t know|In another way'),]
dpart = dpart.loc[~dpart['age_group'].str.contains(r'Prefer not to answer|Don’t know'),]

# deal with group contacts --------------------------
cols_Q75 = ["Q75_u18_work", "Q75_u18_school", "Q75_u18_else", 
              "Q75_1864_work", "Q75_1864_school", "Q75_1864_else",
              "Q75_o64_work", "Q75_o64_school", "Q75_o64_else"]

dpart["grp_nct"] = dpart[cols_Q75].sum(axis=1, skipna=True)
dpart.loc[dpart["grp_nct"] > 100, "grp_nct"] = 100
dpart["grp_nct"] = dpart["grp_nct"].astype(int)
tlb_grp = dpart.loc[:, ["wave", "id", "grp_nct"]]

dpart = dpart.loc[:,['id','wave','date','pt_age','age_group','pt_sex','pt_region']]


# Impute for age --------------------------
dpart.age_group.value_counts()
# for ['age_group']=='<1'
dpart.loc[dpart['age_group']=='<1', 'pt_age'] = 0
# for ['age_group']=='85+'
dpart.loc[dpart['age_group']=='85+', 'pt_age'] = 85

# 9024 participants need to be imputed
df_nullage = dpart.loc[(dpart['pt_age'].isnull()) & (dpart['age_group'].str.contains(r'-')),]

np.random.seed(args['seed'])
def runif_int(string):
    '''Generate a random integer between min and max (inclusive)'''
    match = re.match(r'(\d+)-(\d+)', string)
    min, max = int(match.group(1)), int(match.group(2))
    return int(np.floor(np.random.randint(min, max+1, 1))[0])

# apply the function to the dataframe, create a new column pt_age_impute
df_nullage = df_nullage.assign(pt_age=df_nullage['age_group'].apply(runif_int))



# -------------------------- merge imputed with reported --------------------------
df_haveage = pd.concat([dpart[dpart['pt_age'].notnull()], df_nullage], axis=0)
df_haveage = df_haveage[['id', 'wave', 'pt_age']]

# merge back to dpart
dpart = dpart.drop('pt_age', axis=1)
dpart = pd.merge(dpart, df_haveage, on=['id', 'wave'], how='left')
dpart['pt_age'] = dpart['pt_age'].astype('Int64')
dpart[dpart.isna().any(axis=1)]
dpart = dpart.rename(columns={'age_group': 'pt_age_grp'})


# put pt_age_grp column to the last column
cols = dpart.columns.tolist()
cols.remove('pt_age_grp')
cols.append('pt_age_grp')
dpart = dpart[cols]




# -------------------------- merge part, grp, hh, nhh together --------------------------

# add row position number
dpart["rp_nb"] = dpart.groupby("id").cumcount() + 1

tlb_all = pd.merge(tlb_hh, tlb_nhh, on=['id', 'wave'], how='outer') # int automatically converted to float
tlb_all = pd.merge(tlb_all, tlb_grp, on=['id', 'wave'], how='right')
tlb_all["hh_nct"] = tlb_all["hh_nct"].fillna(0)
tlb_all["nhh_nct"] = tlb_all["nhh_nct"].fillna(0)
tlb_all["hh_nct"] = tlb_all["hh_nct"].astype(int)
tlb_all["nhh_nct"] = tlb_all["nhh_nct"].astype(int)

tlb_all['t_nct'] = tlb_all['hh_nct'] + tlb_all['nhh_nct'] + tlb_all['grp_nct']

df = pd.merge(tlb_all, dpart, on=['id', 'wave'], how='right')
df = df.sort_values(by=["wave", "id"])

age_group_levels = ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-34", "35-44",
                    "45-54", "55-64", "65-69", "70-74", "75-79", "80-84", "85+"]
df["pt_age_grp"] = pd.Categorical(df["pt_age_grp"], categories=age_group_levels)
df["pt_sex"] = pd.Categorical(df["pt_sex"], categories=["Male", "Female"])

df.dtypes



# -------------------------- create df_full --------------------------
df_full = df.copy()
df_full['nhh_nct'] = df_full['nhh_nct'] + df_full['grp_nct']
df_full = df_full.drop(columns=['grp_nct'])



def process_df(df):
    # create a new column mapping wave 1-33 to wave 1-2, 3-12, 13-20, 21-25, 26-33, use string to avoid sorting
    df["wave_grp"] = df["wave"].apply(lambda x: "1-2" if x <= 2 else "3-12" if x <= 12 else "13-20" if x <= 20 else "21-25" if x <= 25 else "26-33")
    wave_group_levels = ["1-2", "3-12", "13-20", "21-25", "26-33"]

    # create a new column mapping pt_age_grp to 10 years age group levels 0-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65+
    df["pt_age_grp_10"] = df["pt_age_grp"] \
        .apply(lambda x: "0-14" if x == "<1" or x == "1-4" or x == "5-9" or x == "10-14" 
            else "15-24" if x == "15-19" or x == "20-24" 
            else "25-34" if x == "25-34" 
            else "35-44" if x == "35-44" 
            else "45-54" if x == "45-54" 
            else "55-64" if x == "55-64" 
            else "65+" if x == "65-69" or x == "70-74" or x == "75-79" or x == "80-84" or x == "85+" 
            else "NA")
    age_group_levels_10 = ["0-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65+"]

    # create a new column mapping pt_age_grp to 20 years age group levels 0-24, 25-44, 45-64, 65+
    df["pt_age_grp_20"] = df["pt_age_grp"] \
        .apply(lambda x: "0-24" if x == "<1" or x == "1-4" or x == "5-9" or x == "10-14" or x == "15-19" or x == "20-24"
                else "25-44" if x == "25-34" or x == "35-44" 
                else "45-64" if x == "45-54" or x == "55-64" 
                else "65+" if x == "65-69" or x == "70-74" or x == "75-79" or x == "80-84" or x == "85+" 
                else "NA")
    age_group_levels_20 = ["0-24", "25-44", "45-64", "65+"]

    df["wave_grp"] = pd.Categorical(df["wave_grp"], categories=wave_group_levels)
    df["pt_age_grp_10"] = pd.Categorical(df["pt_age_grp_10"], categories=age_group_levels_10)
    df["pt_age_grp_20"] = pd.Categorical(df["pt_age_grp_20"], categories=age_group_levels_20)

    return df

df_full = process_df(df_full)



# -------------------------- Sanity check --------------------------
df["pt_age_grp"].isnull().sum() # 0
df["pt_sex"].isnull().sum() # 0

# count number of contacts by sex in each wave
# should be the same as Dan's paper Figure 4.4
df_tmp = df.groupby(['wave','pt_sex']).agg({"hh_nct": "sum", "nhh_nct": "sum"}).reset_index()
df_tmp['total_nct'] = df_tmp['hh_nct'] + df_tmp['nhh_nct']
df_tmp[df_tmp['wave']<=5]

# contact number 
df_tmp = df.groupby(["wave"]).agg({"hh_nct": "sum", "nhh_nct": "sum"}).reset_index()
df_tmp['total_nct'] = df_tmp['hh_nct'] + df_tmp['nhh_nct']
df_tmp[df_tmp['wave']<=5]





# -------------------------- save --------------------------
# save to local file

# drop unused columns
dpart = dpart.drop(columns=['id'])
df = df.drop(columns=['id', 'pt_region'])
df_full = df_full.drop(columns=['id', 'pt_region'])

dpart.to_csv(os.path.join(args['derived_dir'], "dpart.csv"), index=False)
df.to_csv(os.path.join(args['derived_dir'], "df_septypes.csv"), index=False)
df_full.to_csv(os.path.join(args['derived_dir'], "df_full.csv"), index=False)

# output feather type to allow R to read them
# dpart.reset_index(drop=True).to_feather(os.path.join(args['derived_dir'], "dpart.feather"))
# df.reset_index(drop=True).to_feather(os.path.join(args['derived_dir'], "df_septypes.feather"))
# df_full.reset_index(drop=True).to_feather(os.path.join(args['derived_dir'], "df_full.feather"))
import os
import re
import numpy as np
import pandas as pd
import arviz as az
from xarray import Dataset
from cmdstanpy import CmdStanModel, from_csv
from cmdstanpy.stanfit import CmdStanGQ, CmdStanMCMC
from IPython.display import display
from pathlib import Path

import scipy.stats as stats
from scipy.optimize import minimize
from scipy.special import betaln, gammaln, zeta


# -------------------------- cmdstanpy related functions --------------------------
def merge_hdi(fit, name):
    """
    Given a fit object, merge the median and hdi into a single dataframe.

    Args:
        fit (Union[Dataset, CmdStanGQ]): The fit object containing the MCMC samples.
        name (str): The name of the variable within the fit object to analyze.

    Returns:
        DataFrame: A dataframe containing the median and 90% HDI for the specified variable.
    """
    if isinstance(fit, Dataset):
        az_data = fit[name]
    elif isinstance(fit, CmdStanGQ) or isinstance(fit, CmdStanMCMC):
        az_data = fit.draws_xr(name)
    dims = len(az_data.dims) - 2
    index = [name+'_dim_'+str(i) for i in range(dims)]
    data_hdi = az.hdi(az_data, hdi_prob=0.90).to_dataframe().reset_index()
    data_hdi = data_hdi.pivot(index=index, columns='hdi', values=name)
    data_hdi = data_hdi.reset_index()

    data = az_data.to_dataframe().reset_index().drop(columns=['chain', 'draw'])
    data = data.groupby(index).median().reset_index().rename(columns={name:'median'})

    data = pd.merge(data, data_hdi, how='left', on=index)
    return data

def make_fitting_data(data_file):
    """
    Process a data file and prepare it for Stan model fitting, specifically for BNB models.

    Args:
        data_file (str): Path to the CSV data file to be processed.

    Returns:
        dict: A dictionary containing data processed and formatted for Stan model fitting.
    """
    df = pd.read_csv(data_file)

    df.loc[df["rp_nb"].isin([27,28,29,30]), "rp_nb"] = 26

    data = df[['wave', 'wave_grp', 'nhh_nct', 'pt_sex', 'pt_age', 'rp_nb']].copy()
    wave_group_mapping = { '1-2':1, '3-12':2, '13-20':3, '21-25':4, '26-33':5, }
    data.loc[:, 'wave_grp_int'] = data['wave_grp'].map(wave_group_mapping)

    def standardize_1d_array(x):
        return (x - np.mean(x)) / np.std(x)
    
    stan_data_0 = {
        "N": len(data),
        "A": data['pt_age'].nunique(),
        "G": 2, 
        "W": 5,
        "T": 33,
        "R": data['rp_nb'].max(),
        "y": data['nhh_nct'],
        "age": data['pt_age'] + 1,
        "gender": data['pt_sex'].astype('category').cat.codes.values + 1,
        "rep": data['rp_nb'],
        "wave": data['wave_grp_int'],
        "time": data['wave'],
        "wave2time": np.repeat([1,2,3,4,5], [2,10,8,5,8]),
        "T_std": standardize_1d_array(np.linspace(1, 33, 33)),
        "A_std": standardize_1d_array(np.linspace(1, 86, 86)),
    }

    return stan_data_0


class stan_model:
    """
    A wrapper for cmdstanpy that makes creating, executing and analyzing models easier.
    """
    def __init__(self, stan_file, recover=False, stan_data=None, stan_save_dir=None):
        """
        Initializes the stan_model with the necessary parameters and configurations.
        """
        self.stan_file = stan_file
        self.stan_dir = os.path.dirname(stan_file)
        self.stan_name = os.path.basename(stan_file).split(".")[0]
        self.recover = recover
        if self.recover:
            if stan_data is None:
                raise Exception("stan_data cannot be None when recover is True.")
            if stan_save_dir is None:
                raise Exception("stan_save_dir cannot be None when recover is True.")
            self.recover_from_csv(stan_data, stan_save_dir)

    def recover_from_csv(self, stan_data, stan_save_dir):
        """
        Recovers model fitting from saved CSV files.
        """
        self.stan_data = stan_data
        self.stan_save_dir = stan_save_dir if stan_save_dir else os.path.join(self.stan_dir, self.stan_name+"_save")
        if not os.path.exists(self.stan_save_dir):
            raise Exception("Cannot find the stan save dir, please check the path.")

        # Extract timestamps from the files and use files with the latest timestamp
        all_csv_files = [os.path.join(self.stan_save_dir,file) for file in os.listdir(self.stan_save_dir) if file.endswith(".csv")]
        pattern = r"(\d{9,})"  # Matches timestamps like 20230825094535
        timestamps = [int(re.search(pattern, file).group(1)) for file in all_csv_files if re.search(pattern, file)]
        latest_timestamp = max(timestamps)
        self.csv_files = [file for file in all_csv_files if str(latest_timestamp) in file]
        print('Recover fitting from csv files:')
        for file in self.csv_files:
            print(file)
        self.fit = from_csv(self.csv_files, method='sample')
        self.df = self.fit.draws_pd()
        display(self.df)
        self.fit_to_inference_data()
        display(self.az_data)

    def fit_to_inference_data(self):
        """
        Converts the cmdstanpy fit object to an ArviZ InferenceData object.
        """
        var_names = np.array(self.fit.column_names)
        var_names = var_names[~np.char.endswith(var_names, "__")]
        if_log_lik = "log_lik" if (np.sum(np.char.startswith(var_names, "log_lik"))>=1) else None
        if_y_hat =  "y_hat" if (np.sum(np.char.startswith(var_names, "y_hat"))>=1) else None
        
        coords_dict = {
            "participant": np.arange(1,self.stan_data["N"]+1),
            "pt_sex": ["Female", "Male"],
            "age": np.arange(0, 86),
            "wave": np.arange(1, 33+1),
            }
        
        r = re.compile(r'\[\d+(,\d+)*\]$')
        remove_ending = np.vectorize(lambda x: r.sub('', x))
        var_names = remove_ending(var_names)
        unique_params, counts = np.unique(var_names, return_counts=True)
        dims_dict = {
            "y": ["participant"],
        }
        for param, count in zip(unique_params, counts):
            if count > 1:
                # match count with the value length in coords_dict, return the key, add to dims_dict
                dims_dict[param] = [key for key, value in coords_dict.items() if len(value) == count]
        print(dims_dict)
        self.dims_dict = dims_dict
        self.az_data = az.from_cmdstanpy(
            posterior=self.fit,
            posterior_predictive=if_y_hat,
            log_likelihood=if_log_lik,
            observed_data={"y": self.stan_data["y"]},
            coords=coords_dict,
            dims=dims_dict,
            save_warmup=True,
        )
        if if_log_lik:
            self.loo = az.loo(self.az_data, pointwise=True, scale="log")
            print(self.loo)

    def compile(self, user_header=None, **kwargs):
        """
        Compiles the Stan model, making it ready for sampling.
        """
        self.model = CmdStanModel(stan_file=self.stan_file, compile=False, **kwargs)
        if user_header is not None:
            bnb_hpp_dir = user_header.parent / 'bnb'
            for file in Path(bnb_hpp_dir).rglob('*.hpp'):
                self.change_namespace(file)
        self.model.compile(force=False, user_header=user_header)

    def change_namespace(self, user_header):
        """
        Modifies the namespace in the user-provided header files, necessary in Stan.
        """
        filepath = user_header
        with open(filepath, 'r') as file:
            lines = file.readlines()
        with open(filepath, "w") as file:
            for line in lines:
                # Matches all characters except a single space character
                match = re.match(r'^namespace (\S+)_model_namespace {', line)
                if match:
                    new_line = f'namespace {self.stan_name}_model_namespace {{\n'
                    file.write(new_line)
                else:
                    file.write(line)

    def sample(self, stan_data, **kwargs):
        """
        Samples from the posterior distribution of the compiled Stan model, and print the summary.
        """
        self.stan_data = stan_data
        self.fit = self.model.sample(data=self.stan_data, **kwargs)
        self.df = self.fit.draws_pd()
        display(self.df)
        self.fit_to_inference_data()
        display(self.az_data)

    def save(self, stan_save_dir=None):
        """
        Saves the fit objects and outputs to specified directories.
        """
        if stan_save_dir is None:
            self.stan_save_dir = os.path.join(self.stan_dir, self.stan_name+"_save")
        else:
            self.stan_save_dir = stan_save_dir
        if not os.path.exists(self.stan_save_dir):
            os.makedirs(self.stan_save_dir)
        self.fit.save_csvfiles(dir=self.stan_save_dir)
        self.csv_files = self.fit.runset.csv_files
        # self.az_data.to_netcdf(os.path.join(self.stan_save_dir, self.stan_name+".nc"))




# -------------------------- BNB related functions --------------------------

def beta_negative_binomial_rng(r, alpha, beta, size=1, seed=None):
    """
    Generate random samples from a BNB distribution.

    Args:
        r, alpha, beta (float): Parameters of the BNB distribution.
        size (int, optional): Number of samples to generate. Default is 1.
        seed (int, optional): Seed value for random number generator.

    Returns:
        int or ndarray: Random samples from the BNB distribution. 
                        If `size` is 1, an integer is returned. Otherwise, an array of integers.
    """
    if seed is not None:
        np.random.seed(seed)
    p = stats.beta.rvs(alpha, beta, size=size)
    # N Number of successes, p probability of success
    return stats.nbinom.rvs(n=r, p=p)

def poi_mle_fit(data):
    """
    Calculate the MLE for the mean (mu) of Poisson distribution given the data.

    Args:
        data (array-like): Observed data points.

    Returns:
        float: MLE of the mean (mu) of Poisson distribution.
    """
    def poisson_log_likelihood(mu, data):
        return -np.sum(stats.poisson.logpmf(data, mu))

    result = minimize(poisson_log_likelihood, [1], args=(data), method='L-BFGS-B')
    return result.x[0]

def nb_mle_fit(data):
    """
    Calculate the MLEs for parameters of the Negative Binomial distribution given the data.

    Args:
        data (array-like): Observed data points.

    Returns:
        tuple: A tuple containing:
               - MLE of r (number of successes until the experiment is stopped).
               - MLE of p (probability of a single success).
    """
    def negative_binomial_log_likelihood(params, data):
        r, log_p = params
        p = np.exp(log_p) / (1 + np.exp(log_p))
        return -np.sum(stats.nbinom.logpmf(data, r, p))

    result = minimize(negative_binomial_log_likelihood, [1, 0], args=(data), bounds=[(0.001, None), (None, None)], method='L-BFGS-B')
    r = result.x[0]
    p = np.exp(result.x[1]) / (1 + np.exp(result.x[1]))
    return r, p

def bnb_mle_fit(data):
    """
    Calculate the MLEs for parameters of the BNB distribution given the data.

    Args:
        data (array-like): Observed data points.

    Returns:
        tuple: A tuple containing:
               - MLE of r (size parameter).
               - MLE of alpha.
               - MLE of beta.
    """
    def beta_negative_binomial_log_likelihood(params, data):
        alpha, beta, log_r = params
        r = np.exp(log_r)
        log_likelihood = (
            betaln(r + data, alpha + beta) - betaln(r, alpha)
            + gammaln(data + beta) - gammaln(data + 1) - gammaln(beta)
        )
        return -np.sum(log_likelihood)

    bounds = [(0.001, None), (0.001, None), (None, None)]
    result = minimize(beta_negative_binomial_log_likelihood, [1, 1, 0], args=(data), bounds=bounds, method='L-BFGS-B')
    alpha_mle, beta_mle, log_r_mle = result.x
    r_mle = np.exp(log_r_mle)
    return r_mle, alpha_mle, beta_mle

def beta_neg_binomial_pmf(y, r, a, b):
    """
    Compute the PMF of the BNB distribution.

    Args:
        y (array-like): Values at which to evaluate the PMF.
        r, a, b (float): Parameters of the BNB distribution.

    Returns:
        ndarray: PMF values for the provided `y` based on the BNB distribution.
    """
    lprobs = betaln(r+y,a+b) - betaln(r,a) + gammaln(y+b) - gammaln(y+1) - gammaln(b)
    return np.exp(lprobs)

def beta_neg_binomial_cdf(y, r, a, b):
    """
    Compute the CDF of the BNB distribution.

    Args:
        y (array-like): Values at which to evaluate the CDF.
        r, a, b (float): Parameters of the BNB distribution.

    Returns:
        ndarray: CDF values for the provided `y` based on the BNB distribution.
    """
    cdfs = np.zeros(len(y))
    for i, yi in enumerate(y):
        cdfs[i] = np.sum(beta_neg_binomial_pmf(np.arange(yi+1), r, a, b))
    return cdfs

def H(a, N=None):
    """
    Compute the generalized harmonic number.

    Args:
        a (float): Exponent in the harmonic function.
        N (int, optional): Upper bound for the summation. If not provided, uses the Riemann zeta function.

    Returns:
        float: Value of the generalized harmonic number.
    """
    if N is None:
        return zeta(a)
    else:
        return np.sum(1/np.arange(1,N+1)**a)

def zipf_pdf(x, s, N):
    """
    Compute the pdf of the Zipf distribution.

    Args:
        x (array-like): Values at which to evaluate the PDF.
        s (float): Exponent characterizing the distribution.
        N (int): Upper bound for the summation in the Zipf distribution.

    Returns:
        ndarray: PDF values for the provided `x` based on the Zipf distribution.
    """
    x = np.asarray(x)
    mask = (x >= 1) & (x <= N)
    pdf_values = 1 / (x[mask] ** s * H(s,N))
    result = np.zeros_like(x, dtype=float)
    result[mask] = pdf_values
    return result

def zipf_cdf(x, s, N):
    """
    Compute the CDF of the Zipf distribution.

    Args:
        x (float): Values at which to evaluate the CDF.
        s (float): Exponent characterizing the distribution.
        N (int): Upper bound for the summation in the Zipf distribution.

    Returns:
        ndarray: CDF values for the provided `x` based on the Zipf distribution.
    """
    x = np.asarray(x)
    cdf_values = [np.sum(1 / np.arange(1, xi + 1) ** s) for xi in x]
    result = np.asarray(cdf_values) / H(s,N)
    return result
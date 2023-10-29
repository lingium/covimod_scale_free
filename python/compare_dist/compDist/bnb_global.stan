functions {
  #include ../../../src/stan/bnb_functions.stan
}
data {
  int<lower=1> N;  // Number of observations
  array[N] int<lower=0> y; 
}
transformed data {
  int<lower=1> y_max = max(y);
}
parameters {
  real<lower=0> bnb_mu;
  real<lower=0> bnb_sigma;
  real<lower=sqrt(bnb_sigma/bnb_mu)> bnb_nu;
}
transformed parameters {
  real r = bnb_mu*bnb_nu/bnb_sigma;
  real a = 1/bnb_sigma+1;
  real b = 1/bnb_nu;
}
model {
  bnb_mu ~ normal(0, 1);
  bnb_sigma ~ normal(0, 1);
  bnb_nu ~ normal(0, 1);
  target += beta_neg_binomial_lpmf(y | r, a, b);
}
generated quantities {
  array[N] real log_lik;
  {
    for (i in 1:N) {
      log_lik[i] = beta_neg_binomial_lpmf(y[i] | r, a, b);
    }
  }

}

functions{
  #include ../../../src/stan/bnb_functions.stan
}
data {
  int<lower=0> N;
  array[N] int<lower=0> y; 
}
transformed data {
}
parameters {
  real<lower=0> r;
  real<lower=0> alpha;
  real<lower=0,upper=r> beta1;
}
transformed parameters {
}
model {
  profile("priors") {
  r ~ normal(0, 1);
  alpha ~ normal(0, 1);
  beta1 ~ normal(0, 1);
  }

  profile("likelihood") {
  target += beta_neg_binomial_lpmf(y | r, alpha, beta1);
  }
}

functions {
  #include ../../../src/stan/zipf_functions.stan
}
data {
  int<lower=1> N;  // Number of observations
  array[N] int<lower=1> y; 
}
transformed data {
  int<lower=1> y_max = max(y);
}
parameters {
  real<lower=0> alpha;
  real<lower=0> zipf_beta;
}
transformed parameters {
}
model {
  alpha ~ normal(0, 1);
  zipf_beta ~ normal(0, 1);
  vector[y_max] lprobs = zipfmoe_lpmf_vec(alpha, zipf_beta, y_max);
  target += zipfmoe_lpmf(y | lprobs);
}
generated quantities {
  array[N] real log_lik;
  {
    vector[y_max] lprobs;
    lprobs = zipfmoe_lpmf_vec(alpha, zipf_beta, y_max);
    for (i in 1:N) {
      log_lik[i] = zipfmoe_lpmf(y[i] | lprobs);
    }
  }

}

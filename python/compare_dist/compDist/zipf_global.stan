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
}
transformed parameters {
}
model {
  alpha ~ normal(0, 1);
  vector[y_max] lprobs = zipf_lpmf_vec(alpha, y_max);
  target += zipf_lpmf(y | lprobs);
}
generated quantities {
  array[N] real log_lik;
  {
    vector[y_max] lprobs = zipf_lpmf_vec(alpha, y_max);
    for (i in 1:N) {
      log_lik[i] = zipf_lpmf(y[i] | lprobs);
    }
  }
}

functions {
  
}
data {
  int<lower=1> N;  // Number of observations
  array[N] int<lower=0> y; 
}
transformed data {
}
parameters {
  real<lower=0> mu;
}
transformed parameters {
}
model {
  y ~ poisson(mu);
  mu ~ normal(0, 1);
}
generated quantities {
  array[N] real log_lik;
  for (i in 1:N) {
      log_lik[i] = poisson_lpmf(y[i] | mu);
  }

}

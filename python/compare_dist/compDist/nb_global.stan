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
  real<lower=0> phi;
}
transformed parameters {
}
model {
  y ~ neg_binomial_2(mu, phi);
  mu ~ normal(0, 1);
  phi ~ normal(0, 1);
}
generated quantities {
  array[N] real log_lik;
  for (i in 1:N) {
      log_lik[i] = neg_binomial_2_lpmf(y[i] | mu, phi);
  }

}

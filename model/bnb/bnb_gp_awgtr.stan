functions {
  #include ../../src/stan/bnb_functions.stan
  #include ../../src/stan/gp_functions.stan
}
data {
  int<lower=1> N;  // Number of observations
  int<lower=1> A;  // Number of unique age
  int<lower=1> G;  // Number of unique gender
  int<lower=1> R;  // Number of max repeats
  int<lower=1> W;  // Number of time points
  int<lower=1> T;  // Number of restriction phases
  array[N] int<lower=0> y; 
  array[N] int<lower=1,upper=A> age;
  array[N] int<lower=1,upper=G> gender;
  array[N] int<lower=1,upper=R> rep;
  array[N] int<lower=1,upper=W> wave;
  array[N] int<lower=1,upper=T> time;
  array[T] int<lower=1,upper=W> wave2time;
}
transformed data {
  int y_max = max(y);
  int F = 1, M = 2; // gender indexes

}
parameters {
  real beta_0;

  real gamma_0;
  vector[R-1] gamma_r;

  real<lower=0> bnb_k;

  real<lower=0> gp_w_sigma, gp_w_l;
  vector[T] gp_w_z;
  matrix<lower=0>[G,W] gp_a_sigma, gp_a_l;
  array[G] matrix[A,W] gp_a_z;
}
transformed parameters {
  array[G] matrix<lower=0>[A,T] bnb_a;

  // accelerated GP using fast Fourier transform:
  vector[T] gp_w_f = gp_exp_quad_f_rfft(T, gp_w_z, gp_w_sigma, gp_w_l);
  array[G] matrix[A,W] gp_a_f;
  for (g in 1:G) {
    for (w in 1:W) {
      gp_a_f[g,:,w] = gp_exp_quad_f_rfft(A, gp_a_z[g,:,w], gp_a_sigma[g,w], gp_a_l[g,w]);
    }
  }

  {
    array[G] matrix[A,T] gp_a_f_T;
    for (g in 1:G) {
      for (a in 1:A) {
        gp_a_f_T[g,a,:] = gp_a_f[g,a,:][wave2time];
      }
    }
    for (g in 1:G) {
      bnb_a[g] = exp( beta_0 + gp_a_f_T[g] + rep_matrix(to_row_vector(gp_w_f), A) );
    }
  }

  vector<lower=0>[R] bnb_rho = exp(gamma_0 + append_row(0,gamma_r));

}
model {
  gp_w_sigma ~ cauchy(0, 1);
  gp_w_l ~ inv_gamma(2, 2);
  gp_w_z ~ normal(0, 1);
  to_vector(gp_a_sigma) ~ cauchy(0, 1);
  to_vector(gp_a_l) ~ inv_gamma(9, 17);
  to_vector(gp_a_z[M]) ~ normal(0, 1);
  to_vector(gp_a_z[F]) ~ normal(0, 1);

  beta_0 ~ normal(-0.5, 1);
  gamma_0 ~ normal(0.5, 1);
  gamma_r ~ normal(0, 1);
  bnb_k ~ gamma(2, 2);

  vector[N] N_bnb_a;
  for (i in 1:N) {
    N_bnb_a[i] = bnb_a[gender[i], age[i], time[i]];
  }
  vector[N] N_bnb_rho = bnb_rho[rep];

  target += beta_neg_binomial_lpmf(y | N_bnb_a, N_bnb_rho, bnb_k);

}
generated quantities {
  array[N] real log_lik;
  {
    vector[N] N_bnb_a;
    for (i in 1:N) {
      N_bnb_a[i] = bnb_a[gender[i], age[i], time[i]];
    }
    vector[N] N_bnb_rho = bnb_rho[rep];
    for (i in 1:N) {
      log_lik[i] = beta_neg_binomial_lpmf(y[i] | N_bnb_a[i], N_bnb_rho[i], bnb_k);
    }
  }

}


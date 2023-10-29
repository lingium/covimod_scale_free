functions {
  #include ../../src/stan/bnb_functions.stan
}
data {
  int<lower=1> N;  // Number of observations
  int<lower=1> A;  // Number of unique age
  int<lower=1> G;  // Number of unique gender
  int<lower=1> R;  // Number of max repeats
  int<lower=1> W;  // Number of time points
  int<lower=1> T;  // Number of unique time points
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

  array[G] matrix<lower=0>[A,T] bnb_a;
  vector[T %/% 2 + 1] gp_w_cov_rfft;
  vector[T] gp_w_f;
  array[G] matrix[A %/% 2 + 1,W] gp_a_cov_rfft;
  array[G] matrix[A,W] gp_a_f;
  vector<lower=0>[R] bnb_rho;
}
transformed parameters {
}
model {
}
generated quantities {

  // mean of truncated BNB
  array[G] matrix[A,T] bnb_mu;
  {
    for (g in 1:G) {
      for (a in 1:A) {
        for (t in 1:T) {
          bnb_mu[g,a,t] = trunc_bnb_mean(bnb_a[g,a,t], bnb_rho[1], bnb_k, y_max);
        }
      }
    }
  }

  // probability of y>n
  array[G,A,T] vector[5] prop;
  {
    int n = 5;
    array[n] int prop_y = {0,1,2,4,9};
    for (g in 1:G) {
      for (a in 1:A) {
        for (t in 1:T) {
          for (i in 1:n) {
            prop[g,a,t,i] = trunc_bnb_ccdf(prop_y[i], bnb_a[g,a,t], bnb_rho[1], bnb_k, y_max);
          }
        }
      }
    }
  }


  // zero probability
  array[G,4,T,9] real zero;
  {
    array[4] int ages = {20,40,60,80};
    for (g in 1:G) {
      for (a in 1:4) {
        for (t in 1:T) {
          for (r in 1:9) {
              real C = trunc_bnb_cdf(y_max | bnb_a[g,ages[a],t], bnb_rho[r], bnb_k, y_max);
              zero[g,a,t,r] = exp(beta_neg_binomial_lpmf(0 | bnb_a[g,ages[a],t], bnb_rho[r], bnb_k)) / C;
          }
        }
      }
    }
  }


  // variance component coutour
  array[4,G,T,9] vector[4] vars;
  { 
    array[4] int ages = {20, 40, 60, 80};
    for (a in 1:4) {
      for (g in 1:G) {
          for (t in 1:T) {
            for (r in 1:9) {
              vars[a,g,t,r,:] = bnb_var_components(bnb_a[g,a,t], bnb_rho[r], bnb_k, y_max);
            }
          }
      }
    }
  }

  print("iteration complete");

}


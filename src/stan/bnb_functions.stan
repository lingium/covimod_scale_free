#include stan/util.stan
#include stan/fft1.stan

// Signatures of C++ functions

real beta_neg_binomial_lpmf(int n, real r, real alpha, real beta1);
real beta_neg_binomial_lpmf(array[] int n, real r, real alpha, real beta1);
real beta_neg_binomial_lpmf(array[] int n, vector r, real alpha, real beta1);
real beta_neg_binomial_lpmf(array[] int n, vector r, vector alpha, real beta1);
real beta_neg_binomial_lpmf(array[] int n, vector r, vector alpha, vector beta1);
real beta_neg_binomial_lcdf(int n, real r, real alpha, real beta1);
real beta_neg_binomial_lcdf(int n, vector r, real alpha, real beta1);
real beta_neg_binomial_lcdf(array[] int n, real r, real alpha, real beta1);
real beta_neg_binomial_lcdf(array[] int n, vector r, real alpha, real beta1);
real beta_neg_binomial_lcdf(array[] int n, vector r, vector alpha, real beta1);
real beta_neg_binomial_lcdf(array[] int n, vector r, vector alpha, vector beta1);
real beta_neg_binomial_lccdf(int n, real r, real alpha, real beta1);
real beta_neg_binomial_lccdf(int n, vector r, real alpha, real beta1);
real beta_neg_binomial_lccdf(array[] int n, real r, real alpha, real beta1);
real beta_neg_binomial_lccdf(array[] int n, vector r, real alpha, real beta1);
real beta_neg_binomial_lccdf(array[] int n, vector r, vector alpha, real beta1);
real beta_neg_binomial_lccdf(array[] int n, vector r, vector alpha, vector beta1);


/** Truncated BNB Log PMF Vector
  *
  * Calculates the log probability mass function of a BNB distribution for a range of y values.
  *
  * @param a, rho, k: The parameters of the BNB distribution.
  * @param y_max: The maximum value in the sequence of y.
  * @return: The log pmf of the BNB distribution for y = 0, 1, ..., y_max.
  */
vector beta_neg_binomial_lpmf_vec(real a, real rho, real k, int y_max) {
  vector[1+y_max] y = linspaced_vector(1+y_max, 0, y_max);
  vector[1+y_max] lprobs = lbeta(y+a, rho+k) + lgamma(y+k) - lgamma(y+1) - lgamma(k) - lbeta(a, rho);
  lprobs = lprobs - log_sum_exp(lprobs); // normalize the probabilities
  return lprobs;
}

/** Truncated BNB Mean
  *
  * Computes the mean of a truncated BNB distribution.
  *
  * @param a, rho, k: The parameters of the BNB distribution.
  * @param c: The truncation point for the distribution.
  * @return: The mean of the BNB distribution.
  */
real trunc_bnb_mean(real a, real rho, real k, int c) {
  vector[c+1] y = linspaced_vector(c+1,0,c);
  vector[c+1] probs = exp(beta_neg_binomial_lpmf_vec(a, rho, k, c));
  return dot_product(y,probs);
}

/** Truncated BNB Variance
  *
  * Computes the variance of a truncated BNB distribution.
  *
  * @param a, rho, k: The parameters of the BNB distribution.
  * @param c: The truncation point for the distribution.
  * @return: The variance of the BNB distribution.
  */
real trunc_bnb_var(real a, real rho, real k, int c) {
  vector[c+1] y = linspaced_vector(c+1,0,c);
  vector[c+1] probs = exp(beta_neg_binomial_lpmf_vec(a, rho, k, c));
  real EY = dot_product(y,probs);
  real EY2 = dot_product(y.^2,probs);
  return EY2 - EY^2;
}

/** Truncated BNB CDF
  *
  * Computes the cumulative distribution function (CDF) of a truncated BNB distribution at a given y.
  *
  * @param y: The point at which the CDF is evaluated.
  * @param a, rho, k: The parameters of the BNB distribution.
  * @param c: The truncation point for the distribution.
  * @return: The CDF of the BNB distribution at y.
  */
real trunc_bnb_cdf(int y, real a, real rho, real k, int c) {
  vector[c+1] probs = exp(beta_neg_binomial_lpmf_vec(a, rho, k, c));
  return sum(probs[1:y+1]);
}

/** Truncated BNB Complementary CDF
  *
  * Computes the complementary cumulative distribution function (CCDF) of a truncated BNB distribution at a given y.
  *
  * @param y: The point at which the CCDF is evaluated.
  * @param a, rho, k: The parameters of the BNB distribution.
  * @param c: The truncation point for the distribution.
  * @return: The CCDF of the BNB distribution at y.
  */
real trunc_bnb_ccdf(int y, real a, real rho, real k, int c){
  vector[c+1] probs = exp(beta_neg_binomial_lpmf_vec(a, rho, k, c));
  return sum(probs[y+2:c+1]);
}





real trunc_nb_mean(real a, real mu, int c) {
  return mu - (a+mu)*(c+1)*exp(neg_binomial_2_lpmf(c+1 | mu,a))/(a*exp(neg_binomial_2_lcdf(c | mu,a)));
}

real betaII_lpdf_real(real x, real rho, real k) {
  return pow(x,k-1)*pow(1+x,-k-rho)/beta(rho,k);
}

real nu_lpdf_real(real nu, real a, real rho, real k) {
  return betaII_lpdf_real(nu/a, rho, k)/a;
}

real pmf_nu_E_Y_nb(real nu, real xc, array[] real theta, array[] real x_r, array[] int x_i) {
  real a = theta[1];
  real rho = theta[2];
  real k = theta[3];
  int c = x_i[1];
  return trunc_nb_mean(a,nu,c) * nu_lpdf_real(nu,a,rho,k);
}

real pmf_nu_E_Y2_nb(real nu, real xc, array[] real theta, array[] real x_r, array[] int x_i) {
  real a = theta[1];
  real rho = theta[2];
  real k = theta[3];
  int c = x_i[1];
  return pow(trunc_nb_mean(a,nu,c),2) * nu_lpdf_real(nu,a,rho,k);
}

/** Truncated BNB Variance Components
  *
  * Computes various variance components of a BNB distribution up to a specified y_max.
  *
  * @param a, rho, k: The parameters of the BNB distribution.
  * @param y_max The maximum value for the support of the distribution.
  * @return A vector containing the four variance components.
  */
vector bnb_var_components(real a, real rho, real k, int y_max) {
  real E_nu = integrate_1d(pmf_nu_E_Y_nb, 0, 100000, {a,rho,k}, {0}, {y_max}, 0.01);
  real E_nu2 = integrate_1d(pmf_nu_E_Y2_nb, 0, 100000, {a,rho,k}, {0}, {y_max}, 0.01);
  real Var_nu_E_Y_nb = E_nu2 - E_nu^2;

  vector[4] vars;
  vars[1] = trunc_bnb_mean(a,rho,k,y_max);
  vars[3] = Var_nu_E_Y_nb;
  vars[4] = trunc_bnb_var(a,rho,k,y_max);
  vars[2] = vars[4] - vars[1] - vars[3];
  return vars;
}









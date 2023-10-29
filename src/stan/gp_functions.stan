/**
 * Gaussian process with exponential quadratic kernel.
 *
 * @param x     : Input data, typically representing the locations in the input space.
 * @param z     : A vector of weights or latent variables that is multiplied with the Cholesky decomposition of the GP covariance matrix.
 * @param sigma : Scaling parameter (amplitude) for the covariance function.
 * @param l     : Length-scale parameter for the covariance function.
 * @return      : Values of the Gaussian process at locations `x`.
 */
vector gp_exp_quad_f(array[] real x, vector z, real sigma, real l) {
  int A = size(x);
  matrix[A, A] gp_cov = add_diag(gp_exp_quad_cov(x, sigma, l), 1e-9);
  return cholesky_decompose(gp_cov) * z;
}

/**
 * Gaussian process with exponential quadratic kernel using real FFT.
 *
 * @param A     : The number of input points (equidistant).
 * @param z     : A vector of weights or latent variables.
 * @param sigma : Scaling parameter (amplitude) for the covariance function.
 * @param l     : Length-scale parameter for the covariance function.
 * @return      : Values of the Gaussian process.
 */
vector gp_exp_quad_f_rfft(int A, vector z, real sigma, real l) {
  vector[A %/% 2 + 1] gp_cov_rfft = gp_periodic_exp_quad_cov_rfft(A, sigma, l, A);
  return gp_inv_rfft(z, zeros_vector(A), gp_cov_rfft);
}

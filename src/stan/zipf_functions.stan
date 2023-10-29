/** Generalized Harmonic Number
  *
  * @param a: The order of the generalized harmonic number.
  * @param y_max: The length of the harmonic number sequence.
  * @return The value of the generalized harmonic number.
  */
real H(real a, int y_max) {
  vector[y_max] seq = linspaced_vector(y_max, 1, y_max);
  seq = pow(seq, -a);
  return sum(seq);
}

/** Truncated Hurwitz Zeta Function
  *
  * @param a: The order of the truncated Hurwitz zeta function.
  * @param y_min: The lower limit of the summation.
  * @param y_max: The upper limit of the summation.
  * @return The value of the truncated Hurwitz zeta function.
  */
real HZ(real a, int y_min, int y_max) {
  if (y_min > y_max) {
    return 0;
  } else {
    vector[y_max-y_min+1] seq = linspaced_vector(y_max-y_min+1, y_min, y_max);
    seq = pow(seq, -a);
    return sum(seq);
  }
}


/** Zipf Log-Probability Mass Function Vector
  *
  * @param a: The distribution parameter, typically called the "exponent".
  * @param y_max: The maximum value for which to compute the log-PMF.
  * @return A vector of log-PMF values for the Zipf distribution from 1 to `y_max`.
  */
vector zipf_lpmf_vec(real a, int y_max) {
  real Z = H(a, y_max);
  vector[y_max] lprobs = -a * log(linspaced_vector(y_max, 1, y_max)) - log(Z);
  return lprobs;
}
real zipf_lpmf(int y, vector lprobs) {
  return lprobs[y];
}
real zipf_lpmf(array[] int y, vector lprobs) {
  int N = size(y);
  vector[N] lprobs_y = lprobs[y];
  return sum(lprobs_y);
}


/** Marshall-Olkin Extended Zipf (MOEZipf) Log-Probability Mass Function Vector
  *
  * @param a: The first distribution parameter, typically called the "exponent".
  * @param b: The second distribution parameter which must be positive.
  * @param y_max: The maximum value for which to compute the log-PMF.
  * @return A vector of log-PMF values for the MOEZipf distribution from 1 to `y_max`.
  */
vector zipfmoe_lpmf_vec(real a, real b, int y_max) {
  if (b <= 0) {
    reject("b must be positive");
  }
  real Z = H(a, y_max);
  vector[y_max+1] HZ_seq;
  for (i in 1:y_max) {
    HZ_seq[i] = HZ(a,i,y_max);
  }
  HZ_seq[y_max+1] = 0;
  vector[y_max] y = linspaced_vector(y_max, 1, y_max);
  vector[y_max] lprobs = (-a*log(y) + log(b) + log(Z)) - log(Z - (1-b)*HZ_seq[1:y_max]) - log(Z - (1-b)*HZ_seq[2:y_max+1]);
  return lprobs;
}
real zipfmoe_lpmf(int y, vector lprobs) {
  return lprobs[y];
}
real zipfmoe_lpmf(array[] int y, vector lprobs) {
  int N = size(y);
  vector[N] lprobs_y = lprobs[y];
  return sum(lprobs_y);
}


/** Zipf-Poisson Extreme (Zipf-PE) Log-Probability Mass Function Vector
  *
  * @param a: The first distribution parameter, usually called the "exponent".
  * @param b: The Poisson correction term which can take any real value.
  * @param y_max: The maximum value for which to compute the log-PMF.
  * @return A vector of log-PMF values for the Zipf-PE distribution from 1 to `y_max`.
  */
vector zipfpe_lpmf_vec(real a, real b, int y_max) {
  real Z = H(a, y_max);
  vector[y_max] HZ_seq;
  for (i in 1:y_max) {
    HZ_seq[i] = HZ(a,i,y_max);
  }
  if (b == 0) {
    return zipf_lpmf_vec(a, y_max);
  } else {
    vector[y_max] y = linspaced_vector(y_max, 1, y_max);
    vector[y_max] lprobs = b + (-b * HZ_seq / Z) + log(exp(b*pow(y,-a)/Z) - 1) - log(exp(b) - 1);
    return lprobs;
  }
}
real zipfpe_lpmf(int y, vector lprobs) {
  return lprobs[y];
}
real zipfpe_lpmf(array[] int y, vector lprobs) {
  int N = size(y);
  vector[N] lprobs_y = lprobs[y];
  return sum(lprobs_y);
}


/** Zipf-Poisson Stopped Sum (Zipf-PSS) Log-Probability Mass Function Vector
  *
  * This function extends to count y = 0, 1, 2, ... up to `y_max`.
  *
  * @param a: The parameter for the Zipf distribution, usually called the "exponent".
  * @param lambda: The Poisson parameter that determines the stopping time, must be positive.
  * @param y_max: The maximum value for which to compute the log-PMF.
  * @return A vector of log-PMF values for the Zipf-PSS distribution from 0 to `y_max`.
  */
vector zipfpss_lpmf_vec(real a, real lambda, int y_max) {
  if (lambda <= 0) {
    reject("lambda must be positive");
  }
  real Z = H(a, y_max);
  vector[1+y_max] probs;
  probs[1] = exp(-lambda);
  for (i in 1:y_max) {
    real tmp = sum(pow(linspaced_vector(i, 1, i), 1 - a) .* reverse(probs[1:i]));
    probs[i+1] = (lambda / (Z * i)) * tmp;
  }
  return log(probs);
}
real zipfpss_lpmf(int y, vector lprobs) {
  return lprobs[y+1];
}
real zipfpss_lpmf(array[] int y, vector lprobs) {
  int N = size(y);
  vector[N] lprobs_y;
  for (i in 1:N) {
    lprobs_y[i] = lprobs[y[i]+1];
  }
  return sum(lprobs_y);
}

/** Zipf-Polylog (Zipf-PL) Log-Probability Mass Function Vector
  * 
  * Restrictions: When `b` is 1, `a` must be greater than 1.
  *
  * @param a: The exponent parameter for the Zipfian distribution.
  * @param b: The base parameter for the Polylog modification.
  * @param y_max: The maximum value for which to compute the log-PMF.
  * @return A vector of log-PMF values for the Zipf-Polylog distribution from 1 to `y_max`.
  */
vector zipfpl_lpmf_vec(real a, real b, int y_max) {
  if (b == 1 && a <= 1) {
    reject("a must be > 1 when b=1");
  }
  vector[y_max] seq = linspaced_vector(y_max, 1, y_max);
  vector[y_max] probs = pow(b, seq) .* pow(seq, -a);
  probs = probs ./ sum(probs);
  return log(probs);
}
real zipfpl_lpmf(int y, vector lprobs) {
  return lprobs[y];
}
real zipfpl_lpmf(array[] int y, vector lprobs) {
  int N = size(y);
  vector[N] lprobs_y = lprobs[y];
  return sum(lprobs_y);
}


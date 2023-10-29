# covimod_scale_free


## About this repository
This repository is for the MSc thesis specifically, aiming to exactly reproduces the results and graphs in the thesis. For the preprint, there will be another repository.

## Directory structure
The project are structured as follows:
```
covimod_scale_free
├── README.md
├── data
│   ├── covimod
│   ├── derived
│   └── population
├── figures
├── model
│   └── bnb
├── python
│   ├── compare_dist
│   ├── plot_scripts
│   ├── profile_stan
│   ├── plot_all.py
│   └── process_data.py
├── R
└── src
    ├── cpp
    ├── python
    └── stan
```

### Contents

-   `data`: Contains raw data and all temporary data generated during code execution
-   `figures`: Location where the generated pdf is saved after the drawing code is run
-   `model`: Stan files and corresponding python code to execute which
-   `python`: Python scripts for the project main body
-   `R`: R scripts used in the early stages of the project
-   `src`: Definitions of all reusable functions and classes, which are dependent on other parts of the project

Please report any bugs and issues to: [lingzhi255\@gmail.com](mailto:lingzhi255@gmail.com) or directly post a issue on GitHub.



## Quick Start

### Setup

Clone the repository to local
```shell
git clone https://github.com/lingium/covimod_scale_free.git
cd ./covimod_scale_free
```

Setup environment. For `conda` user:
```shell
conda create -n proj python=3.9
conda activate proj
pip3 install -r requirements.txt
```

Then install `cmdstan` if it does not exist on local machine.

```shell
conda install -c conda-forge cmdstanpy
```
This will install `cmdstan` and the required C++ toolchain. For other installation methods, please refer to the [official documentation](https://mc-stan.org/cmdstanpy/installation.html) of `cmdstanpy`.

For non-`conda` environment, a recommend way is to install `cmdstan` through the python function `install_cmdstan`. See section [function-install-cmdstan](https://mc-stan.org/cmdstanpy/installation.html#function-install-cmdstan).
```python
import cmdstanpy
cmdstanpy.install_cmdstan()
```

It is strongly recommended to use the __Python Interactive Mode__ provided by Visual Studio Code to run all the code. See https://code.visualstudio.com/docs/python/jupyter-support-py.


### Model

The code involves several sub-goals, so it cannot be completed in one run. Nevertheless, it has a clear order of execution.

1. Run `python/process_data.py`. This will prosecss raw data and output to `data/derived_dir/`.
2. Run `model/run_model.py`, the full Bayesian model.
3. Run `model/gen_quant.py` to generate more quantities given the model fitting.
4. Run every script in `python/plot_scripts`, each corresponding to a plot in the thesis. Python scripts that do not start with `result_` can be executed without performing step 2. The file `python/plot_all.py` allows to run all drawing code in one go.
5. Folders `python/profile_stan` and `python/compare_dist` are optional to play with. `python/compare_dist` needs the derived data from step 1. 




## Availability of data

Because of data agreement terms, we cannot share the COVIMOD or POLYMOD data at this stage. We will update this repository once the availability changes.

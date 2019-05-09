'''
Script ot plot the temporal autocorrelation functions (ACF) of nowcasts and observations 
that were previously generated by the script run_cascade_ar_correlation_tests.py.
The script also derives the lifetimes and plots them against the spatial scale.
'''

import pickle
from matplotlib import pyplot
from matplotlib.pyplot import cm
import numpy as np
from pysteps.verification.lifetime import lifetime
from pysteps.timeseries import autoregression

# the domain: "fmi" or "mch_hdf5"
domain          = "mch_hdf5"
n_levels        = [1,8]
recompute_flow  = False
nhours_ar       = 3      # Max n of hours to plot the ACFs
rule            = 'trapz'   # Rule to integrate the ACF and get the lifetime [1/e, trapz]
recompute_acf   = False  # Whether to recompute the ACF starting from the first two rhos

# Read results file
filename = "data/%s_ar2_corr_results_recomputeflow-%s.dat" % (domain,recompute_flow)
with open(filename, "rb") as f:
    results = pickle.load(f)
print(filename, "read.")
results_keys = list(results.keys())[0:2]

for lev in results_keys: 
    num_cascade_levels = len(results[lev]["cc_obs"]) 
    leadtimes = results[lev]["leadtimes"]
    max_leadtime_min = nhours_ar*60
    max_idx = np.min([int(max_leadtime_min/results[lev]["timestep"]),leadtimes[-1]])
    leadtimes_plot = leadtimes[0:max_idx]
    
    fig = pyplot.figure(figsize=(5, 3.75))
    ax = fig.gca()

    colors=iter(cm.Blues_r(np.linspace(0,1,num_cascade_levels+2)))
    for i in range(num_cascade_levels):
        # Derive average ACF for sufficient number of time stamps
        acf_fct = results[lev]["cc_fct"][i] / results[lev]["n_fct_samples"][i]
        acf_obs = results[lev]["cc_obs"][i] / results[lev]["n_obs_samples"][i]
        
        # Plot
        col = next(colors)
        ax.plot(leadtimes_plot, acf_fct[0:len(leadtimes_plot)], color=col, linestyle="--")
        ax.plot(leadtimes_plot, acf_obs[0:len(leadtimes_plot)], color=col)

    lines = ax.get_lines()
    l = pyplot.legend([lines[0], lines[1]], ["Forecasts", "Observations"],
                      fontsize=12, loc=(0.6, 0.92), framealpha=1.0)
    ax.add_artist(l)

    colors=iter(cm.Blues_r(np.linspace(0,1,num_cascade_levels+2)))
    max_leadtime = np.max(leadtimes_plot)
    ax.text(150.0/150*max_leadtime, 0.85, '1', fontsize=10, color=next(colors))
    ax.text(139.0/150*max_leadtime, 0.71, '2', fontsize=10, color=next(colors))
    ax.text(120.0/150*max_leadtime, 0.35, '3', fontsize=10, color=next(colors))
    ax.text(93.0/150*max_leadtime, 0.18, '4', fontsize=10, color=next(colors))
    ax.text(75.0/150*max_leadtime, 0.07, '5', fontsize=10, color=next(colors))
    ax.text(38.0/150*max_leadtime, 0.05, '6', fontsize=10, color=next(colors))
    ax.text(15.0/150*max_leadtime, 0.05, '7', fontsize=10, color=next(colors))
    ax.text(7.0/150*max_leadtime, 0.021, '8', fontsize=10, color=next(colors))
    
    if max_leadtime_min < 500:
        tick_spacing = 20
    elif max_leadtime_min < 2000:
        tick_spacing = 60
    
    if max_leadtime_min < 2000:    
        xt = np.hstack([[5], np.arange(0, np.max(leadtimes_plot)+5, tick_spacing)])
        ax.set_xticks(xt)
        ax.set_xticklabels([int(v) for v in xt])
    ax.tick_params(labelsize=10)

    pyplot.grid(True)

    pyplot.xlim(leadtimes_plot[0], leadtimes_plot[-1])
    pyplot.ylim(-0.02, 1.1)

    pyplot.xlabel("Lead time (minutes)", fontsize=12)
    pyplot.ylabel("Correlation", fontsize=12)

    figname = "figures/%s_ar2_correlations_%ilevels_recomputeflow-%s.pdf" % (domain,lev,recompute_flow)
    pyplot.savefig(figname, bbox_inches="tight")
    print(figname, 'saved.')

## Estimate lifetimes from ACF
lifetime_array = []

# Lifetime of observations
lifetime_array = np.zeros((num_cascade_levels, 4))
for i in range(0,num_cascade_levels):
    acf_obs = results[lev]["cc_obs"][i] / results[lev]["n_obs_samples"][i]
    
    if recompute_acf:
        acf_obs = autoregression.ar_acf(acf_obs[0:2].tolist(), n=len(acf_obs))
    lf_obs = lifetime(acf_obs, leadtimes, rule=rule)
    
    acf_obs_t0 = results[lev]["cc_obs_t0"][i] / results[lev]["n_obs_samples_t0"][i]
    if recompute_acf:
        acf_obs_t0 = autoregression.ar_acf(acf_obs_t0[0:2].tolist(), n=len(acf_obs_t0))
    lf_obs_t0 = lifetime(acf_obs_t0, leadtimes, rule=rule)
    
    lifetime_array[i,0] = lf_obs
    lifetime_array[i,1] = lf_obs_t0
    
    # Lifetime of forecasts
    for levi,lev in enumerate(results_keys):
        acf_fct = results[lev]["cc_fct"][i] / results[lev]["n_fct_samples"][i]
        if recompute_acf:
            acf_fct = autoregression.ar_acf(acf_fct[0:2].tolist(), n=len(acf_fct))
        lf_fx = lifetime(acf_fct, leadtimes, rule=rule)
        lifetime_array[i,levi+2] = lf_fx

# Plot log(wavelength) vs log(lifetime), i.e. the dynamic scaling plot
fig = pyplot.figure(figsize=(5, 3.75))
ax = fig.gca()

pyplot.loglog(results[results_keys[0]]["central_wavelengths"], lifetime_array[:,0], "k", marker='o', label="Observations")
#pyplot.loglog(results[results_keys[0]]["central_wavelengths"], lifetime_array[:,1], "gray", label="Observations (t=-2,-1,0)")
pyplot.ylim([1e-1,10**4.5])
pyplot.xlim([2,710])

linestyles = ["k--", "k:", "k-."]
for idx,lev in enumerate(n_levels):
    if lev == 1:
        lab_txt = "Forecasts 1-level"
    else:
        lab_txt = "Forecasts %i-levels" % lev
    pyplot.loglog(results[results_keys[0]]["central_wavelengths"], lifetime_array[:,idx+2], linestyles[idx], marker='o',label=lab_txt)

# Decorate plot
pyplot.xlabel("Wavelength [km]", fontsize=12)
pyplot.ylabel("Lifetime [min]", fontsize=12)
pyplot.legend(loc="lower right")
pyplot.grid()

rule_txt = "e" if rule == "1/e" else rule
figname = "figures/%s_ar2_wavelength-vs-lifetime_rule-%s_recomputeflow-%s_recomputeacf-%s.pdf" % (domain,rule_txt,recompute_flow,recompute_acf)
pyplot.savefig(figname, bbox_inches="tight")
print(figname, 'saved.')
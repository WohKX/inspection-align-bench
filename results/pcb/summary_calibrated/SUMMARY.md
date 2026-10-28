# Annotated-pair evaluation: summary

Pairs evaluated: 120. tau = 7.2 px (original image pixels, on the mean point error). Working long side: native.

Acceptance thresholds calibrated on results/pcb_calib (max-risk 0.05: lowest threshold with at most 5% of accepted poses wrong); methods without one keep their own rule.


Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 120 | 120 | 2.30 | 3.59 | 5.02 | 5.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/0000 | 40 | 1.97 | 3.87 | 4.53 |
| Full/0001 | 40 | 2.28 | 3.46 | 5.02 |
| Full/0002 | 40 | 2.57 | 3.37 | 4.70 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 0.60 | 2.25 | 25.28 | 94.38 | 0.84 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 120 | 1.000 | 0.067 | 0.933 | 0.000 | 0.000 | 0.000 | 25.593 | 56.932 | 25.593 | 23.103 | 0.595 | 0.024 |
| phase_correlation | dense_global | 120 | 0.625 | 0.533 | 0.092 | 0.042 | 0.333 | 0.000 | 4.851 | 7.891 | 6.344 | 2.425 | 0.362 | 30.674 |
| sift_ransac | classical_keypoints | 120 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.705 | 5.708 | 3.705 | 1.239 | 0.133 | 2224.833 |
| lightglue_disk | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.217 | 0.783 | 0.000 |  |  | 12.133 |  |  | 1978.944 |
| lightglue_sift | learned_matcher | 120 | 0.083 | 0.075 | 0.008 | 0.767 | 0.150 | 0.000 | 5.239 | 7.314 | 4.705 | 2.594 | 0.130 | 873.052 |
| contour_shape_match | shape | 120 | 0.983 | 0.983 | 0.000 | 0.017 | 0.000 | 0.000 | 3.504 | 5.290 | 3.504 | 1.024 | 0.119 | 5996.012 |
| phase_correlation+rot | dense_global | 120 | 0.625 | 0.533 | 0.092 | 0.042 | 0.333 | 0.000 | 4.851 | 7.891 | 6.344 | 2.425 | 0.362 | 1905.298 |
| sift_ransac+rot | classical_keypoints | 120 | 0.958 | 0.958 | 0.000 | 0.042 | 0.000 | 0.000 | 3.811 | 5.761 | 3.829 | 1.376 | 0.124 | 56159.600 |
| lightglue_disk+rot | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.108 | 0.892 | 0.000 |  |  | 13.427 |  |  | 49996.415 |
| lightglue_sift+rot | learned_matcher | 120 | 0.058 | 0.058 | 0.000 | 0.808 | 0.133 | 0.000 | 4.554 | 6.247 | 4.857 | 2.158 | 0.149 | 23154.369 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 7.2 px | <= 10 px | <= 14.4 px | <= 20 px |
|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.017 | 0.067 | 0.125 | 0.250 | 0.350 |
| phase_correlation | 0.000 | 0.000 | 0.033 | 0.342 | 0.533 | 0.608 | 0.625 | 0.625 |
| sift_ransac | 0.000 | 0.083 | 0.325 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.033 | 0.075 | 0.083 | 0.083 | 0.083 |
| contour_shape_match | 0.000 | 0.108 | 0.342 | 0.858 | 0.983 | 0.983 | 0.983 | 0.983 |
| phase_correlation+rot | 0.000 | 0.000 | 0.033 | 0.342 | 0.533 | 0.608 | 0.625 | 0.625 |
| sift_ransac+rot | 0.000 | 0.067 | 0.283 | 0.817 | 0.958 | 0.958 | 0.958 | 0.958 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.033 | 0.058 | 0.058 | 0.058 | 0.058 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation | 0.948 | 0.575 | 0.425 | 0.083 |
| sift_ransac |  | 1.000 | 1.000 | 0.000 |
| lightglue_disk | 0.303 | 0.217 | 0.000 | 0.867 |
| lightglue_sift | 0.532 | 0.842 | 0.058 | 0.150 |
| contour_shape_match |  | 1.000 | 1.000 | 0.000 |
| phase_correlation+rot | 0.948 | 0.575 | 0.425 | 0.083 |
| sift_ransac+rot |  | 1.000 | 1.000 | 0.000 |
| lightglue_disk+rot | 0.636 | 0.108 | 0.000 | 0.833 |
| lightglue_sift+rot | 0.520 | 0.867 | 0.167 | 0.117 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.600 | 0.475 | 0.525 | 0.600 | 0.150 | 0.675 | 0.100 | 0.725 | 0.100 | 0.700 | 0.725 |
| sift_ransac | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.225 | 0.000 | 0.000 | 0.225 | 0.025 | 0.225 | 0.025 | 0.225 | 0.025 | 0.225 | 0.225 |
| contour_shape_match | 1.000 | 0.950 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.600 | 0.475 | 0.525 | 0.600 | 0.150 | 0.675 | 0.100 | 0.725 | 0.100 | 0.700 | 0.725 |
| sift_ransac+rot | 1.000 | 0.875 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.175 | 0.000 | 0.000 | 0.175 | 0.000 | 0.175 | 0.000 | 0.175 | 0.000 | 0.175 | 0.175 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/0000 | identity | 40 | 0.075 | 0.925 | 0.000 | 0.000 | 0.000 | 18.358 | 0.024 |
| Full/0000 | phase_correlation | 40 | 0.600 | 0.150 | 0.000 | 0.250 | 0.000 | 4.509 | 30.658 |
| Full/0000 | sift_ransac | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.515 | 1940.529 |
| Full/0000 | lightglue_disk | 40 | 0.000 | 0.000 | 0.225 | 0.775 | 0.000 |  | 1973.243 |
| Full/0000 | lightglue_sift | 40 | 0.225 | 0.025 | 0.675 | 0.075 | 0.000 | 5.239 | 869.673 |
| Full/0000 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.372 | 6067.976 |
| Full/0000 | phase_correlation+rot | 40 | 0.600 | 0.150 | 0.000 | 0.250 | 0.000 | 4.509 | 1907.420 |
| Full/0000 | sift_ransac+rot | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.737 | 48301.896 |
| Full/0000 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.200 | 0.800 | 0.000 |  | 50147.627 |
| Full/0000 | lightglue_sift+rot | 40 | 0.175 | 0.000 | 0.700 | 0.125 | 0.000 | 4.554 | 23155.204 |
| Full/0001 | identity | 40 | 0.075 | 0.925 | 0.000 | 0.000 | 0.000 | 29.606 | 0.023 |
| Full/0001 | phase_correlation | 40 | 0.475 | 0.050 | 0.075 | 0.400 | 0.000 | 4.851 | 30.619 |
| Full/0001 | sift_ransac | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.267 | 2245.581 |
| Full/0001 | lightglue_disk | 40 | 0.000 | 0.000 | 0.275 | 0.725 | 0.000 |  | 1975.533 |
| Full/0001 | lightglue_sift | 40 | 0.000 | 0.000 | 0.700 | 0.300 | 0.000 |  | 873.965 |
| Full/0001 | contour_shape_match | 40 | 0.950 | 0.000 | 0.050 | 0.000 | 0.000 | 3.194 | 5894.440 |
| Full/0001 | phase_correlation+rot | 40 | 0.475 | 0.050 | 0.075 | 0.400 | 0.000 | 4.851 | 1847.142 |
| Full/0001 | sift_ransac+rot | 40 | 0.875 | 0.000 | 0.125 | 0.000 | 0.000 | 3.164 | 57692.944 |
| Full/0001 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 49972.821 |
| Full/0001 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.775 | 0.225 | 0.000 |  | 23205.240 |
| Full/0002 | identity | 40 | 0.050 | 0.950 | 0.000 | 0.000 | 0.000 | 29.300 | 0.025 |
| Full/0002 | phase_correlation | 40 | 0.525 | 0.075 | 0.050 | 0.350 | 0.000 | 5.017 | 30.722 |
| Full/0002 | sift_ransac | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.979 | 2607.330 |
| Full/0002 | lightglue_disk | 40 | 0.000 | 0.000 | 0.150 | 0.850 | 0.000 |  | 1984.739 |
| Full/0002 | lightglue_sift | 40 | 0.000 | 0.000 | 0.925 | 0.075 | 0.000 |  | 873.472 |
| Full/0002 | contour_shape_match | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.654 | 5942.347 |
| Full/0002 | phase_correlation+rot | 40 | 0.525 | 0.075 | 0.050 | 0.350 | 0.000 | 5.017 | 1927.282 |
| Full/0002 | sift_ransac+rot | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.113 | 62749.088 |
| Full/0002 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.025 | 0.975 | 0.000 |  | 49971.131 |
| Full/0002 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.950 | 0.050 | 0.000 |  | 23106.799 |

# Annotated-pair evaluation: summary

Pairs evaluated: 30. tau = 6.1 px (original image pixels, on the mean point error). Working long side: native.



Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 30 | 30 | 1.65 | 2.92 | 3.03 | 3.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 10 | 2.27 | 3.00 | 3.03 |
| Full/001 | 10 | 1.04 | 1.55 | 1.66 |
| Full/002 | 10 | 1.35 | 1.76 | 1.79 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 92.71 | 173.77 | 129.76 | 256.34 | 0.98 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 30 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 622.183 | 855.690 | 622.183 | 619.748 | 92.712 | 0.019 |
| phase_correlation | dense_global | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  |  | 636.481 |  |  | 13.328 |
| sift_ransac | classical_keypoints | 30 | 0.467 | 0.000 | 0.467 | 0.000 | 0.500 | 0.033 | 27.881 | 233.910 | 61.956 | 26.992 | 0.716 | 130.341 |
| lightglue_disk | learned_matcher | 30 | 0.600 | 0.000 | 0.600 | 0.000 | 0.333 | 0.067 | 497.282 | 832.381 | 662.653 | 496.181 | 65.861 | 2337.361 |
| lightglue_sift | learned_matcher | 30 | 0.467 | 0.100 | 0.367 | 0.000 | 0.400 | 0.133 | 15.753 | 36.900 | 34.608 | 14.435 | 0.301 | 774.909 |
| contour_shape_match | shape | 30 | 0.000 | 0.000 | 0.000 | 0.033 | 0.967 | 0.000 |  |  | 24.131 |  |  | 3921.799 |
| phase_correlation+rot | dense_global | 30 | 0.200 | 0.000 | 0.200 | 0.000 | 0.800 | 0.000 | 21.197 | 31.072 | 64.835 | 19.497 | 1.267 | 835.155 |
| sift_ransac+rot | classical_keypoints | 30 | 0.500 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 21.919 | 514.010 | 31.779 | 20.269 | 0.455 | 5035.956 |
| lightglue_disk+rot | learned_matcher | 30 | 0.967 | 0.000 | 0.967 | 0.000 | 0.033 | 0.000 | 37.218 | 780.154 | 39.455 | 36.512 | 1.148 | 55886.797 |
| lightglue_sift+rot | learned_matcher | 30 | 1.000 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 23.178 | 37.949 | 23.178 | 21.067 | 0.562 | 19998.720 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 5.8 px | <= 6.1 px | <= 10 px | <= 12.2 px | <= 20 px |
|---|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.067 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.067 | 0.067 | 0.167 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.100 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.100 | 0.167 | 0.167 | 0.333 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.067 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.100 | 0.200 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.100 | 0.167 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.067 | 0.100 | 0.167 | 0.200 | 0.433 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation |  | 0.000 | 0.000 | 1.000 |
| sift_ransac |  | 0.000 | 0.000 | 1.000 |
| lightglue_disk |  | 0.000 | 0.000 | 1.000 |
| lightglue_sift | 0.725 | 0.100 | 0.033 | 0.812 |
| contour_shape_match |  | 0.033 | 0.000 | 0.933 |
| phase_correlation+rot |  | 0.000 | 0.000 | 1.000 |
| sift_ransac+rot |  | 0.000 | 0.000 | 1.000 |
| lightglue_disk+rot |  | 0.000 | 0.000 | 1.000 |
| lightglue_sift+rot | 0.914 | 0.100 | 0.033 | 0.800 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.400 | 0.000 | 0.900 | 0.000 | 0.900 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.700 | 0.000 | 0.900 | 0.000 | 0.900 | 0.000 | 0.000 |
| lightglue_sift | 0.100 | 0.100 | 0.100 | 0.100 | 0.100 | 0.200 | 0.700 | 0.200 | 0.700 | 0.200 | 0.200 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.300 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.000 | 0.900 | 0.000 | 0.900 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.900 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.100 | 0.100 | 0.100 | 0.100 | 0.900 | 0.200 | 0.800 | 0.200 | 0.800 | 0.200 | 0.200 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 668.492 | 0.019 |
| Full/000 | phase_correlation | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 13.358 |
| Full/000 | sift_ransac | 10 | 0.000 | 0.400 | 0.000 | 0.600 | 0.000 | 56.802 | 129.476 |
| Full/000 | lightglue_disk | 10 | 0.000 | 0.700 | 0.000 | 0.200 | 0.100 | 655.609 | 2335.138 |
| Full/000 | lightglue_sift | 10 | 0.100 | 0.100 | 0.000 | 0.600 | 0.200 | 10.925 | 774.121 |
| Full/000 | contour_shape_match | 10 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 4202.299 |
| Full/000 | phase_correlation+rot | 10 | 0.000 | 0.300 | 0.000 | 0.700 | 0.000 | 22.043 | 820.407 |
| Full/000 | sift_ransac+rot | 10 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 21.919 | 4987.645 |
| Full/000 | lightglue_disk+rot | 10 | 0.000 | 0.900 | 0.000 | 0.100 | 0.000 | 47.825 | 55919.249 |
| Full/000 | lightglue_sift+rot | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 20.850 | 20022.353 |
| Full/001 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 384.087 | 0.019 |
| Full/001 | phase_correlation | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 13.296 |
| Full/001 | sift_ransac | 10 | 0.000 | 0.600 | 0.000 | 0.300 | 0.100 | 24.250 | 130.459 |
| Full/001 | lightglue_disk | 10 | 0.000 | 0.900 | 0.000 | 0.100 | 0.000 | 473.291 | 2324.412 |
| Full/001 | lightglue_sift | 10 | 0.100 | 0.600 | 0.000 | 0.200 | 0.100 | 15.563 | 797.324 |
| Full/001 | contour_shape_match | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 4090.971 |
| Full/001 | phase_correlation+rot | 10 | 0.000 | 0.300 | 0.000 | 0.700 | 0.000 | 20.351 | 828.073 |
| Full/001 | sift_ransac+rot | 10 | 0.000 | 0.600 | 0.000 | 0.400 | 0.000 | 20.423 | 4980.672 |
| Full/001 | lightglue_disk+rot | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 436.943 | 55941.190 |
| Full/001 | lightglue_sift+rot | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 22.190 | 19998.265 |
| Full/002 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 582.227 | 0.018 |
| Full/002 | phase_correlation | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 13.233 |
| Full/002 | sift_ransac | 10 | 0.000 | 0.400 | 0.000 | 0.600 | 0.000 | 30.669 | 131.260 |
| Full/002 | lightglue_disk | 10 | 0.000 | 0.200 | 0.000 | 0.700 | 0.100 | 22.210 | 2352.167 |
| Full/002 | lightglue_sift | 10 | 0.100 | 0.400 | 0.000 | 0.400 | 0.100 | 18.352 | 770.731 |
| Full/002 | contour_shape_match | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 3675.068 |
| Full/002 | phase_correlation+rot | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 844.238 |
| Full/002 | sift_ransac+rot | 10 | 0.000 | 0.400 | 0.000 | 0.600 | 0.000 | 25.610 | 5058.153 |
| Full/002 | lightglue_disk+rot | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 27.027 | 55813.254 |
| Full/002 | lightglue_sift+rot | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 23.246 | 19969.944 |

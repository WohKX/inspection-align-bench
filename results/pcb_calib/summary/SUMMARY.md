# Annotated-pair evaluation: summary

Pairs evaluated: 30. tau = 7.2 px (original image pixels, on the mean point error). Working long side: native.



Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 30 | 30 | 2.39 | 3.88 | 4.53 | 5.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/0000 | 10 | 3.11 | 3.81 | 3.90 |
| Full/0001 | 10 | 2.29 | 3.90 | 4.53 |
| Full/0002 | 10 | 2.36 | 3.29 | 3.85 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 0.45 | 1.48 | 26.50 | 58.86 | 0.55 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 30 | 1.000 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 26.894 | 56.522 | 26.894 | 24.194 | 0.455 | 0.020 |
| phase_correlation | dense_global | 30 | 0.933 | 0.667 | 0.267 | 0.000 | 0.067 | 0.000 | 5.187 | 11.974 | 5.547 | 2.802 | 0.455 | 19.974 |
| sift_ransac | classical_keypoints | 30 | 1.000 | 0.967 | 0.033 | 0.000 | 0.000 | 0.000 | 4.316 | 6.277 | 4.316 | 1.532 | 0.108 | 2205.836 |
| lightglue_disk | learned_matcher | 30 | 1.000 | 0.033 | 0.967 | 0.000 | 0.000 | 0.000 | 13.724 | 474.813 | 13.724 | 11.536 | 0.583 | 1948.057 |
| lightglue_sift | learned_matcher | 30 | 1.000 | 0.833 | 0.167 | 0.000 | 0.000 | 0.000 | 5.439 | 10.286 | 5.439 | 2.698 | 0.219 | 755.666 |
| contour_shape_match | shape | 30 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |  |  | 3.820 |  |  | 6021.680 |
| phase_correlation+rot | dense_global | 30 | 0.933 | 0.667 | 0.267 | 0.000 | 0.067 | 0.000 | 5.187 | 11.974 | 5.547 | 2.802 | 0.455 | 1267.384 |
| sift_ransac+rot | classical_keypoints | 30 | 1.000 | 0.967 | 0.033 | 0.000 | 0.000 | 0.000 | 4.177 | 6.414 | 4.177 | 1.520 | 0.121 | 54265.390 |
| lightglue_disk+rot | learned_matcher | 30 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 14.594 | 251.586 | 14.594 | 11.641 | 0.621 | 51841.176 |
| lightglue_sift+rot | learned_matcher | 30 | 1.000 | 0.767 | 0.233 | 0.000 | 0.000 | 0.000 | 5.647 | 10.041 | 5.647 | 2.803 | 0.282 | 20894.949 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 7.2 px | <= 7.8 px | <= 10 px | <= 14.4 px | <= 20 px |
|---|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.100 | 0.133 | 0.267 | 0.300 |
| phase_correlation | 0.000 | 0.000 | 0.100 | 0.433 | 0.667 | 0.667 | 0.833 | 0.933 | 0.933 |
| sift_ransac | 0.000 | 0.000 | 0.233 | 0.700 | 0.967 | 0.967 | 0.967 | 0.967 | 0.967 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.033 | 0.233 | 0.600 | 0.700 |
| lightglue_sift | 0.000 | 0.000 | 0.100 | 0.333 | 0.833 | 0.833 | 0.900 | 0.967 | 0.967 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.100 | 0.433 | 0.667 | 0.667 | 0.833 | 0.933 | 0.933 |
| sift_ransac+rot | 0.000 | 0.000 | 0.133 | 0.733 | 0.967 | 0.967 | 0.967 | 0.967 | 0.967 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.200 | 0.467 | 0.733 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.100 | 0.400 | 0.767 | 0.833 | 0.933 | 1.000 | 1.000 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation | 0.985 | 0.667 | 0.700 | 0.000 |
| sift_ransac |  | 0.967 | 1.000 | 0.067 |
| lightglue_disk |  | 0.033 | 0.000 | 1.000 |
| lightglue_sift | 0.516 | 0.833 | 0.067 | 0.133 |
| contour_shape_match |  | 1.000 | 1.000 | 0.000 |
| phase_correlation+rot | 0.985 | 0.667 | 0.700 | 0.000 |
| sift_ransac+rot |  | 0.967 | 1.000 | 0.067 |
| lightglue_disk+rot |  | 0.000 | 0.000 | 1.000 |
| lightglue_sift+rot | 0.484 | 0.767 | 0.067 | 0.267 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.600 | 0.800 | 0.600 | 0.600 | 0.400 | 0.800 | 0.200 | 0.800 | 0.200 | 0.800 | 0.800 |
| sift_ransac | 1.000 | 1.000 | 0.900 | 1.000 | 0.000 | 1.000 | 0.000 | 0.900 | 0.100 | 1.000 | 1.000 |
| lightglue_disk | 0.000 | 0.100 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.100 | 0.100 |
| lightglue_sift | 0.900 | 0.800 | 0.800 | 0.900 | 0.100 | 0.900 | 0.100 | 0.900 | 0.100 | 1.000 | 1.000 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| phase_correlation+rot | 0.600 | 0.800 | 0.600 | 0.600 | 0.400 | 0.800 | 0.200 | 0.800 | 0.200 | 0.800 | 0.800 |
| sift_ransac+rot | 1.000 | 1.000 | 0.900 | 1.000 | 0.000 | 1.000 | 0.000 | 0.900 | 0.100 | 1.000 | 1.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.800 | 0.700 | 0.800 | 0.800 | 0.200 | 0.800 | 0.200 | 0.800 | 0.200 | 1.000 | 1.000 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/0000 | identity | 10 | 0.300 | 0.700 | 0.000 | 0.000 | 0.000 | 11.295 | 0.019 |
| Full/0000 | phase_correlation | 10 | 0.600 | 0.400 | 0.000 | 0.000 | 0.000 | 4.780 | 20.031 |
| Full/0000 | sift_ransac | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.509 | 1989.858 |
| Full/0000 | lightglue_disk | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 13.824 | 1932.608 |
| Full/0000 | lightglue_sift | 10 | 0.900 | 0.100 | 0.000 | 0.000 | 0.000 | 5.638 | 752.947 |
| Full/0000 | contour_shape_match | 10 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |  | 5998.876 |
| Full/0000 | phase_correlation+rot | 10 | 0.600 | 0.400 | 0.000 | 0.000 | 0.000 | 4.780 | 1271.232 |
| Full/0000 | sift_ransac+rot | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.509 | 48171.508 |
| Full/0000 | lightglue_disk+rot | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 13.079 | 51696.341 |
| Full/0000 | lightglue_sift+rot | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 5.872 | 20877.659 |
| Full/0001 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 30.186 | 0.019 |
| Full/0001 | phase_correlation | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 5.605 | 19.879 |
| Full/0001 | sift_ransac | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.564 | 2264.748 |
| Full/0001 | lightglue_disk | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 14.275 | 2021.624 |
| Full/0001 | lightglue_sift | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 5.127 | 755.666 |
| Full/0001 | contour_shape_match | 10 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |  | 6056.737 |
| Full/0001 | phase_correlation+rot | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 5.605 | 1239.284 |
| Full/0001 | sift_ransac+rot | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 3.498 | 57215.918 |
| Full/0001 | lightglue_disk+rot | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 18.623 | 51888.596 |
| Full/0001 | lightglue_sift+rot | 10 | 0.700 | 0.300 | 0.000 | 0.000 | 0.000 | 5.290 | 20871.173 |
| Full/0002 | identity | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 30.329 | 0.023 |
| Full/0002 | phase_correlation | 10 | 0.600 | 0.200 | 0.000 | 0.200 | 0.000 | 5.547 | 20.171 |
| Full/0002 | sift_ransac | 10 | 0.900 | 0.100 | 0.000 | 0.000 | 0.000 | 4.506 | 2452.209 |
| Full/0002 | lightglue_disk | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 13.646 | 1938.027 |
| Full/0002 | lightglue_sift | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 5.589 | 759.584 |
| Full/0002 | contour_shape_match | 10 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |  | 6336.140 |
| Full/0002 | phase_correlation+rot | 10 | 0.600 | 0.200 | 0.000 | 0.200 | 0.000 | 5.547 | 1307.170 |
| Full/0002 | sift_ransac+rot | 10 | 0.900 | 0.100 | 0.000 | 0.000 | 0.000 | 4.243 | 63318.662 |
| Full/0002 | lightglue_disk+rot | 10 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 14.281 | 52066.538 |
| Full/0002 | lightglue_sift+rot | 10 | 0.800 | 0.200 | 0.000 | 0.000 | 0.000 | 5.656 | 20993.700 |

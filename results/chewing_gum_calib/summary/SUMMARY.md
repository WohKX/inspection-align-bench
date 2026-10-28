# Annotated-pair evaluation: summary

Pairs evaluated: 30. tau = 20.7 px (original image pixels, on the mean point error). Working long side: native.


Symmetry-aware scoring for: Full (a pose counts against the nearest of the part's equivalent orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in results.csv is the error without it).

Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 30 | 30 | 6.09 | 14.06 | 15.57 | 4.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 10 | 5.80 | 7.86 | 8.35 |
| Full/001 | 10 | 9.09 | 14.97 | 15.57 |
| Full/002 | 10 | 3.15 | 7.92 | 8.38 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 1.24 | 4.15 | 44.50 | 94.43 | 1.84 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | correct_via_symmetry | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 30 | 1.000 | 0.133 | 0.867 | 0.000 | 0.000 | 0.000 | 0.000 | 46.049 | 88.666 | 46.049 | 39.552 | 1.242 | 0.022 |
| phase_correlation | dense_global | 30 | 0.033 | 0.000 | 0.033 | 0.300 | 0.667 | 0.000 | 0.000 | 250.163 | 250.163 | 41.231 | 244.301 | 0.091 | 29.708 |
| sift_ransac | classical_keypoints | 30 | 0.167 | 0.000 | 0.167 | 0.033 | 0.800 | 0.000 | 0.000 | 360.607 | 550.659 | 367.355 | 353.342 | 0.450 | 573.037 |
| lightglue_disk | learned_matcher | 30 | 0.433 | 0.000 | 0.433 | 0.000 | 0.233 | 0.333 | 0.000 | 428.478 | 1029.532 | 349.088 | 422.358 | 0.604 | 2191.850 |
| lightglue_sift | learned_matcher | 30 | 0.267 | 0.033 | 0.233 | 0.100 | 0.500 | 0.133 | 0.000 | 51.910 | 351.375 | 47.029 | 48.035 | 0.547 | 889.708 |
| contour_shape_match | shape | 30 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 8.024 | 15.164 | 8.024 | 1.353 | 0.484 | 1315.669 |
| phase_correlation+rot | dense_global | 30 | 0.033 | 0.000 | 0.033 | 0.300 | 0.667 | 0.000 | 0.000 | 250.163 | 250.163 | 113.448 | 244.301 | 0.091 | 876.678 |
| sift_ransac+rot | classical_keypoints | 30 | 0.200 | 0.000 | 0.200 | 0.000 | 0.800 | 0.000 | 0.000 | 348.435 | 535.618 | 348.457 | 343.087 | 0.468 | 8459.908 |
| lightglue_disk+rot | learned_matcher | 30 | 0.433 | 0.000 | 0.433 | 0.033 | 0.500 | 0.033 | 0.000 | 428.478 | 1029.532 | 232.863 | 422.358 | 0.604 | 27556.757 |
| lightglue_sift+rot | learned_matcher | 30 | 0.300 | 0.033 | 0.267 | 0.067 | 0.567 | 0.067 | 0.000 | 46.492 | 349.797 | 52.922 | 41.401 | 0.648 | 11662.459 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 10 px | <= 20 px | <= 20.7 px | <= 28.1 px | <= 41.4 px |
|---|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.133 | 0.133 | 0.167 | 0.467 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.033 | 0.067 |
| contour_shape_match | 0.000 | 0.000 | 0.000 | 0.133 | 0.767 | 1.000 | 1.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.033 | 0.033 | 0.067 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation | 0.857 | 0.300 | 0.000 | 0.400 |
| sift_ransac |  | 0.033 | 0.000 | 0.962 |
| lightglue_disk |  | 0.000 | 0.000 | 1.000 |
| lightglue_sift | 0.568 | 0.133 | 0.000 | 0.810 |
| contour_shape_match |  | 1.000 | 1.000 | 0.000 |
| phase_correlation+rot | 0.794 | 0.300 | 0.000 | 0.467 |
| sift_ransac+rot |  | 0.000 | 0.000 | 1.000 |
| lightglue_disk+rot |  | 0.033 | 0.000 | 1.000 |
| lightglue_sift+rot | 0.607 | 0.100 | 0.000 | 0.842 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.000 | 0.100 | 0.000 | 0.100 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.700 | 0.000 | 0.800 | 0.000 | 0.800 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.100 | 0.000 | 0.400 | 0.000 | 0.500 | 0.100 | 0.600 | 0.000 | 0.100 |
| contour_shape_match | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 | 0.000 | 0.100 | 0.000 | 0.100 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.600 | 0.000 | 0.600 | 0.000 | 0.600 | 0.000 | 0.000 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.700 | 0.000 | 0.800 | 0.000 | 0.800 | 0.000 | 0.000 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.100 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 0.700 | 0.000 | 0.100 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 50.635 | 0.021 |
| Full/000 | phase_correlation | 10 | 0.000 | 0.100 | 0.500 | 0.400 | 0.000 | 250.163 | 29.624 |
| Full/000 | sift_ransac | 10 | 0.000 | 0.500 | 0.100 | 0.400 | 0.000 | 360.607 | 559.007 |
| Full/000 | lightglue_disk | 10 | 0.000 | 0.700 | 0.000 | 0.200 | 0.100 | 362.836 | 2219.187 |
| Full/000 | lightglue_sift | 10 | 0.000 | 0.400 | 0.000 | 0.300 | 0.300 | 290.451 | 889.708 |
| Full/000 | contour_shape_match | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 7.393 | 1181.945 |
| Full/000 | phase_correlation+rot | 10 | 0.000 | 0.100 | 0.500 | 0.400 | 0.000 | 250.163 | 880.554 |
| Full/000 | sift_ransac+rot | 10 | 0.000 | 0.600 | 0.000 | 0.400 | 0.000 | 348.435 | 8297.981 |
| Full/000 | lightglue_disk+rot | 10 | 0.000 | 0.700 | 0.000 | 0.300 | 0.000 | 362.836 | 27812.644 |
| Full/000 | lightglue_sift+rot | 10 | 0.000 | 0.500 | 0.000 | 0.300 | 0.200 | 250.032 | 11588.298 |
| Full/001 | identity | 10 | 0.100 | 0.900 | 0.000 | 0.000 | 0.000 | 38.015 | 0.023 |
| Full/001 | phase_correlation | 10 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 30.029 |
| Full/001 | sift_ransac | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 587.607 |
| Full/001 | lightglue_disk | 10 | 0.000 | 0.100 | 0.000 | 0.300 | 0.600 | 645.996 | 2162.919 |
| Full/001 | lightglue_sift | 10 | 0.000 | 0.100 | 0.100 | 0.800 | 0.000 | 46.492 | 918.763 |
| Full/001 | contour_shape_match | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 10.518 | 1315.669 |
| Full/001 | phase_correlation+rot | 10 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 893.815 |
| Full/001 | sift_ransac+rot | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 8691.213 |
| Full/001 | lightglue_disk+rot | 10 | 0.000 | 0.100 | 0.100 | 0.700 | 0.100 | 645.996 | 27148.475 |
| Full/001 | lightglue_sift+rot | 10 | 0.000 | 0.100 | 0.100 | 0.800 | 0.000 | 46.492 | 11684.426 |
| Full/002 | identity | 10 | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 | 43.559 | 0.022 |
| Full/002 | phase_correlation | 10 | 0.000 | 0.000 | 0.300 | 0.700 | 0.000 |  | 29.534 |
| Full/002 | sift_ransac | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 570.075 |
| Full/002 | lightglue_disk | 10 | 0.000 | 0.500 | 0.000 | 0.200 | 0.300 | 793.232 | 2191.850 |
| Full/002 | lightglue_sift | 10 | 0.100 | 0.200 | 0.200 | 0.400 | 0.100 | 40.579 | 880.291 |
| Full/002 | contour_shape_match | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 5.355 | 1563.854 |
| Full/002 | phase_correlation+rot | 10 | 0.000 | 0.000 | 0.300 | 0.700 | 0.000 |  | 871.196 |
| Full/002 | sift_ransac+rot | 10 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 8431.030 |
| Full/002 | lightglue_disk+rot | 10 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 793.232 | 27686.506 |
| Full/002 | lightglue_sift+rot | 10 | 0.100 | 0.200 | 0.100 | 0.600 | 0.000 | 40.579 | 11701.363 |

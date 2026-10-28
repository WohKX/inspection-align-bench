# Annotated-pair evaluation: summary

Pairs evaluated: 120. tau = 10.3 px (original image pixels, on the mean point error). Working long side: native.

Acceptance thresholds calibrated on results/metal_nut_calib (max-risk 0.05: lowest threshold with at most 5% of accepted poses wrong); methods without one keep their own rule.

Symmetry-aware scoring for: Full (a pose counts against the nearest of the part's equivalent orientations; correct_via_symmetry = share of pairs that are correct only because of that; err_mean_strict_px in results.csv is the error without it).

Unavailable methods: none

## 1. The annotation floor (read this first)

Mean point error of the similarity that best fits the clicked points themselves: click scatter plus the real shape difference between the two pieces. No similarity-model method can be expected to do better on a pair; differences between methods smaller than it are not interpretable. tau should be clearly above floor_p95.

| pairs | pairs_with_floor | floor_median_px | floor_p95_px | floor_max_px | gt_points_median |
|---|---|---|---|---|---|
| 120 | 120 | 3.45 | 5.16 | 7.75 | 5.00 |


The same, per golden. Each pair's floor contains the clicks and the shape of BOTH images, so every golden brings its own floor; the pooled p95 above therefore changes with the set of goldens. Fix tau once per part and keep it for every golden condition.

| group | pairs | floor_median_px | floor_p95_px | floor_max_px |
|---|---|---|---|---|
| Full/000 | 40 | 3.54 | 5.03 | 5.70 |
| Full/001 | 40 | 3.83 | 5.38 | 7.75 |
| Full/002 | 40 | 2.96 | 4.24 | 5.48 |


The poses in the data (from the ground-truth fit):


| rot_abs_median_deg | rot_abs_max_deg | shift_median_px | shift_max_px | scale_dev_max_pct |
|---|---|---|---|---|
| 25.91 | 44.80 | 2.61 | 7.55 | 1.29 |

## 2. Per method (all pairs)

Rates are fractions of pairs. err_*_accepted: mean point error over the poses the method accepted; err_median_all: over every pose it returned (also rejected ones); excess = error minus that pair's floor. `identity` is the reference line: its error is the raw misalignment.

| method | family | n_pairs | accepted | correct | silent_wrong | lost | rejected | no_pose | correct_via_symmetry | err_median_accepted_px | err_p95_accepted_px | err_median_all_px | excess_median_px | rot_err_median_abs_deg | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | none | 120 | 1.000 | 0.033 | 0.967 | 0.000 | 0.000 | 0.000 | 0.008 | 108.927 | 171.223 | 108.927 | 105.981 | 25.913 | 0.019 |
| phase_correlation | dense_global | 120 | 0.000 | 0.000 | 0.000 | 0.017 | 0.983 | 0.000 | 0.000 |  |  | 156.256 |  |  | 6.242 |
| sift_ransac | classical_keypoints | 120 | 0.000 | 0.000 | 0.000 | 0.175 | 0.817 | 0.008 | 0.000 |  |  | 180.933 |  |  | 89.031 |
| lightglue_disk | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.083 | 0.917 | 0.000 | 0.000 |  |  | 104.676 |  |  | 1484.675 |
| lightglue_sift | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.300 | 0.700 | 0.000 | 0.000 |  |  | 22.225 |  |  | 693.795 |
| contour_shape_match | shape | 120 | 0.442 | 0.442 | 0.000 | 0.408 | 0.150 | 0.000 | 0.308 | 4.444 | 7.858 | 5.531 | 1.653 | 0.568 | 258.353 |
| phase_correlation+rot | dense_global | 120 | 0.000 | 0.000 | 0.000 | 0.150 | 0.850 | 0.000 | 0.000 |  |  | 58.732 |  |  | 87.265 |
| sift_ransac+rot | classical_keypoints | 120 | 0.100 | 0.083 | 0.017 | 0.150 | 0.750 | 0.000 | 0.075 | 4.712 | 263.639 | 195.277 | 1.863 | 0.590 | 766.599 |
| lightglue_disk+rot | learned_matcher | 120 | 0.017 | 0.008 | 0.008 | 0.133 | 0.850 | 0.000 | 0.008 | 8.014 | 11.380 | 35.365 | 5.805 | 1.489 | 10446.289 |
| lightglue_sift+rot | learned_matcher | 120 | 0.000 | 0.000 | 0.000 | 0.375 | 0.625 | 0.000 | 0.000 |  |  | 14.891 |  |  | 4727.849 |

## 2b. Correct rate at other tolerances

The same poses and the same accept/reject decisions, judged with a range of tau values (the headline tau is the one fixed before the run). A method whose rate only rises at tolerances far above the floor is coarse, not wrong.

| method | <= 1 px | <= 2 px | <= 3 px | <= 5 px | <= 10 px | <= 10.3 px | <= 20 px | <= 20.6 px |
|---|---|---|---|---|---|---|---|---|
| identity | 0.000 | 0.000 | 0.008 | 0.008 | 0.033 | 0.033 | 0.108 | 0.117 |
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| contour_shape_match | 0.000 | 0.000 | 0.042 | 0.283 | 0.442 | 0.442 | 0.442 | 0.442 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.000 | 0.008 | 0.025 | 0.067 | 0.083 | 0.083 | 0.083 | 0.083 |
| lightglue_disk+rot | 0.000 | 0.000 | 0.000 | 0.008 | 0.008 | 0.008 | 0.017 | 0.017 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 3. Does the method's own score tell right from wrong?

Without any threshold. auroc: how often a right pose (error <= tau) scores higher than a wrong one, over the poses the method returned (0.5 = no better than chance; blank = fewer than 3 right or 3 wrong poses). right_pose_any_decision: share of pairs whose pose is right, whatever the method decided. coverage_at_5pct_risk: the largest share of pairs a threshold on the score can accept while at most 5% of the accepted poses are wrong (0 = no threshold achieves it). risk_at_50pct_coverage: the share of wrong poses among the accepted ones when the threshold accepts half of the pairs. The full curves are in risk_coverage.csv.

| method | auroc | right_pose_any_decision | coverage_at_5pct_risk | risk_at_50pct_coverage |
|---|---|---|---|---|
| phase_correlation |  | 0.017 | 0.000 | 0.967 |
| sift_ransac | 0.885 | 0.175 | 0.033 | 0.784 |
| lightglue_disk | 0.850 | 0.083 | 0.017 | 0.836 |
| lightglue_sift | 0.837 | 0.300 | 0.033 | 0.500 |
| contour_shape_match | 0.839 | 0.850 | 0.717 | 0.017 |
| phase_correlation+rot | 0.555 | 0.150 | 0.000 | 0.833 |
| sift_ransac+rot | 0.864 | 0.233 | 0.050 | 0.697 |
| lightglue_disk+rot | 0.699 | 0.142 | 0.008 | 0.803 |
| lightglue_sift+rot | 0.766 | 0.375 | 0.033 | 0.433 |

## 4. Several goldens

golden i alone: correct rate with that golden only. own pick of k: the method is given the first k goldens, keeps the one its own decision score likes best (the ground truth plays no part), and accepts or rejects that pose as usual: what a system that stores k goldens would get. best possible of k: share of test images for which at least one of the k goldens gives a correct pose (an upper bound no method can claim).

| method | golden 1 alone | golden 2 alone | golden 3 alone | own pick of 1: correct | own pick of 1: silent_wrong | own pick of 2: correct | own pick of 2: silent_wrong | own pick of 3: correct | own pick of 3: silent_wrong | best possible of 2 | best possible of 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_disk | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lightglue_sift | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| contour_shape_match | 0.325 | 0.325 | 0.675 | 0.325 | 0.000 | 0.500 | 0.000 | 0.775 | 0.000 | 0.500 | 0.775 |
| phase_correlation+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| sift_ransac+rot | 0.050 | 0.075 | 0.125 | 0.050 | 0.000 | 0.100 | 0.050 | 0.225 | 0.050 | 0.100 | 0.225 |
| lightglue_disk+rot | 0.025 | 0.000 | 0.000 | 0.025 | 0.000 | 0.025 | 0.000 | 0.025 | 0.025 | 0.025 | 0.025 |
| lightglue_sift+rot | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 5. Per group and method

| group | method | n_pairs | correct | silent_wrong | lost | rejected | no_pose | err_median_accepted_px | latency_median_ms |
|---|---|---|---|---|---|---|---|---|---|
| Full/000 | identity | 40 | 0.025 | 0.975 | 0.000 | 0.000 | 0.000 | 101.111 | 0.017 |
| Full/000 | phase_correlation | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 6.219 |
| Full/000 | sift_ransac | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 91.078 |
| Full/000 | lightglue_disk | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 1484.645 |
| Full/000 | lightglue_sift | 40 | 0.000 | 0.000 | 0.300 | 0.700 | 0.000 |  | 697.563 |
| Full/000 | contour_shape_match | 40 | 0.325 | 0.000 | 0.400 | 0.275 | 0.000 | 5.256 | 255.349 |
| Full/000 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 88.627 |
| Full/000 | sift_ransac+rot | 40 | 0.050 | 0.000 | 0.075 | 0.875 | 0.000 | 4.721 | 781.881 |
| Full/000 | lightglue_disk+rot | 40 | 0.025 | 0.000 | 0.200 | 0.775 | 0.000 | 4.275 | 10453.186 |
| Full/000 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.425 | 0.575 | 0.000 |  | 4736.434 |
| Full/001 | identity | 40 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 111.304 | 0.019 |
| Full/001 | phase_correlation | 40 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |  | 6.243 |
| Full/001 | sift_ransac | 40 | 0.000 | 0.000 | 0.175 | 0.825 | 0.000 |  | 88.862 |
| Full/001 | lightglue_disk | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 1490.075 |
| Full/001 | lightglue_sift | 40 | 0.000 | 0.000 | 0.250 | 0.750 | 0.000 |  | 686.436 |
| Full/001 | contour_shape_match | 40 | 0.325 | 0.000 | 0.525 | 0.150 | 0.000 | 3.962 | 263.025 |
| Full/001 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.100 | 0.900 | 0.000 |  | 83.800 |
| Full/001 | sift_ransac+rot | 40 | 0.075 | 0.050 | 0.100 | 0.775 | 0.000 | 5.729 | 770.122 |
| Full/001 | lightglue_disk+rot | 40 | 0.000 | 0.000 | 0.125 | 0.875 | 0.000 |  | 10453.937 |
| Full/001 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.350 | 0.650 | 0.000 |  | 4718.993 |
| Full/002 | identity | 40 | 0.075 | 0.925 | 0.000 | 0.000 | 0.000 | 111.490 | 0.019 |
| Full/002 | phase_correlation | 40 | 0.000 | 0.000 | 0.050 | 0.950 | 0.000 |  | 6.235 |
| Full/002 | sift_ransac | 40 | 0.000 | 0.000 | 0.250 | 0.725 | 0.025 |  | 85.936 |
| Full/002 | lightglue_disk | 40 | 0.000 | 0.000 | 0.075 | 0.925 | 0.000 |  | 1485.238 |
| Full/002 | lightglue_sift | 40 | 0.000 | 0.000 | 0.350 | 0.650 | 0.000 |  | 694.032 |
| Full/002 | contour_shape_match | 40 | 0.675 | 0.000 | 0.300 | 0.025 | 0.000 | 4.053 | 254.964 |
| Full/002 | phase_correlation+rot | 40 | 0.000 | 0.000 | 0.250 | 0.750 | 0.000 |  | 87.642 |
| Full/002 | sift_ransac+rot | 40 | 0.125 | 0.000 | 0.275 | 0.600 | 0.000 | 3.108 | 755.044 |
| Full/002 | lightglue_disk+rot | 40 | 0.000 | 0.025 | 0.075 | 0.900 | 0.000 | 11.754 | 10429.641 |
| Full/002 | lightglue_sift+rot | 40 | 0.000 | 0.000 | 0.350 | 0.650 | 0.000 |  | 4745.001 |

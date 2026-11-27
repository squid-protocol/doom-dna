# SFS update experiment, step 1: a size gate learned on one port, tested on the other

Truth: behaviourally confirmed pairs (break pattern and call profile). Unchanged matcher = every E12 pair; updated matcher = pairs whose size ratio (larger / smaller function, in lines) is at most the learned gate. The gate is chosen to maximise F1 on the training port and applied unchanged to the test port.

## Learn on managed-doom, test on prboom-plus

Gate chosen on managed-doom: size ratio <= 1.25 (F1 by gate on the training port: 1.1: 0.29, 1.25: 0.44, 1.5: 0.43, 2.0: 0.43, 3.0: 0.41, none: 0.40)

| matcher                          |   kept |   correct |   precision |   recall |   f1 |
|:---------------------------------|-------:|----------:|------------:|---------:|-----:|
| unchanged SFS (all E12 pairs)    |     75 |        45 |        0.6  |     0.62 | 0.61 |
| SFS with the size gate (<= 1.25) |     39 |        27 |        0.69 |     0.38 | 0.49 |
| SFS strong tiers only            |     37 |        25 |        0.68 |     0.35 | 0.46 |

Precision gain from the gate on the test port: +0.09 (bootstrap 95% interval -0.01 to +0.20); recall change -0.25.

## Learn on prboom-plus, test on managed-doom

Gate chosen on prboom-plus: size ratio <= 3.0 (F1 by gate on the training port: 1.1: 0.35, 1.25: 0.49, 1.5: 0.59, 2.0: 0.61, 3.0: 0.62, none: 0.61)

| matcher                         |   kept |   correct |   precision |   recall |   f1 |
|:--------------------------------|-------:|----------:|------------:|---------:|-----:|
| unchanged SFS (all E12 pairs)   |     61 |        31 |        0.51 |     0.33 | 0.4  |
| SFS with the size gate (<= 3.0) |     57 |        31 |        0.54 |     0.33 | 0.41 |
| SFS strong tiers only           |     10 |         8 |        0.8  |     0.09 | 0.16 |

Precision gain from the gate on the test port: +0.04 (bootstrap 95% interval +0.01 to +0.07); recall change +0.00.

## Step 2: a calibrated confidence score instead of a hard gate

Ranking quality (AUC of the score for behaviourally confirmed versus not) on the held-out port; the score is a logistic model fitted on the other port. The baseline is the matcher's own tier order.

| fitted_on    | tested_on    | score                                |   AUC | ci           |
|:-------------|:-------------|:-------------------------------------|------:|:-------------|
| managed-doom | prboom-plus  | tier order only (unchanged SFS)      |  0.62 | 0.50 to 0.75 |
| managed-doom | prboom-plus  | size ratio only                      |  0.68 | 0.55 to 0.81 |
| managed-doom | prboom-plus  | tier + size ratio (calibrated score) |  0.68 | 0.56 to 0.81 |
| prboom-plus  | managed-doom | tier order only (unchanged SFS)      |  0.62 | 0.48 to 0.74 |
| prboom-plus  | managed-doom | size ratio only                      |  0.87 | 0.76 to 0.95 |
| prboom-plus  | managed-doom | tier + size ratio (calibrated score) |  0.82 | 0.70 to 0.91 |

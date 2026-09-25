# Realtime depth through MPSGraph on macOS 27

Recorded 2026-09-25 on an Apple M1 Max running macOS 27.0 with Xcode 27.0
(build 27A266a). The MESS realtime session targeted 60 fps and used the
MPSMediaPipe face backend.

## Result

ZipDepth had the lowest depth cost in the captured MESS sessions. Depth Anything
V2 held the 60 fps presentation target with a median complete depth-source cost
of 17.23 ms. The user-labelled DA3 Small run was the heaviest and presented at a
56.71 fps median over its 60-frame window.

| MPSGraph engine | Capture duration | Samples | Median model time | Median depth-source time | Median presentation rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| DA3 Small (`DA3_SM_MPS`) | 15.24 s | 16 | 33.77 ms | 32.17 ms | 56.71 fps |
| Depth Anything V2 (`DA2_MPS`) | 29.78 s | 30 | 17.01 ms | 17.23 ms | 60.02 fps |
| ZipDepth Base NPU (`ZIP_MPS`) | 13.52 s | 14 | 5.29 ms | 5.44 ms | 60.00 fps |

Compared with the captured DA3 run, ZipDepth's median model time was about 6.4x
faster and its median complete depth-source time was about 5.9x faster. DA2's
complete depth-source median was about 1.9x faster than captured DA3 and 3.2x
slower than ZipDepth.

## How the capture was summarized

MESS wrote the current timing values approximately once per second. The sample at
`elapsed_s = 0` was excluded. Each reported fps value is `1000 / operation_ms`;
it is an operation-time equivalent, not a count of delivered depth frames. The
model and depth-source fields are updated by adjacent callbacks and sampled
independently, so their medians can appear slightly out of order.

Run the checked-in summarizer against a raw capture with:

```sh
python3 scripts/summarize_capture.py \
  studies/realtime-depth-macos27/captures/DA2_MPS
```

## Limits on comparison

This was not a controlled replay. The DA3 capture saw zero to four faces per
sample with 38.86 ms median face latency. DA2 saw zero to two faces with 21.52 ms
median face latency. ZipDepth saw one to two faces with 9.13 ms median face
latency. DA2 and DA3 each recorded one source-frame decode failure.

Foreground model time remained in the same range: 17.78 ms for DA3, 19.71 ms for
DA2, and 18.01 ms for ZipDepth. That supports attributing the large depth timing
differences to the depth backends, while the presentation-rate difference remains
directional.

Capture metadata did not record the selected depth model or backend. The row
identities therefore come from the user-assigned directory names. In particular,
the DA3 capture does not prove whether the 392 x 392 or 518 x 518 variant was
active.

## Standalone conversion measurements

These warm medians came from different small harnesses and exclude the full MESS
pipeline. Compare routes within a row more strongly than values between rows.

| Model | Fixed input | Core ML CPU + GPU | MPSGraph `.level0` | Context |
| --- | ---: | ---: | ---: | --- |
| Depth Anything V2 Small | 448 x 336 | 14.86 ms | 14.50 ms | Interleaved inference over 11 still images |
| ZipDepth Base NPU | 384 x 384 | 12.96 ms | 3.48 ms | Preliminary raw-model probes |
| DA3 Small native | 518 x 518 | 23.94 ms | 40.4 ms | Core ML validator and separate graph probe |
| DA3 Small reduced | 392 x 392 | 16.69 ms | 15.22 ms | Core ML validator and separate graph probe |

## Deployment-target finding

The three Depth Anything Core ML sources fail `mpsgraphtool` conversion for
macOS 26 and earlier. Their generated instance-normalization operation uses
mean, variance, gamma, and beta operands available from MPSGraph package target
version 1.3.8; Xcode 27 maps macOS 26 to 1.3.3 and macOS 15 to 1.2.1. They convert
successfully with a macOS 27 target.

ZipDepth converts successfully with a macOS 15 target. The release keeps its
macOS 27 build so every artifact matches the benchmark configuration. A future
lower-target ZipDepth release should be tested on the oldest claimed system.

## Next measurement

A controlled comparison should replay the same source segment with identical face
and effect workload, record the exact model/backend selection in capture metadata,
and capture depth request and completion deltas so delivered depth fps can be
measured directly.

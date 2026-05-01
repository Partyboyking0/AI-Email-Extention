# Hugging Face Endpoint Latency Report

| Call | Cold/Warm | Latency ms | Notes |
| --- | --- | ---: | --- |
| 1 | cold | TBD |  |
| 2 | warm | TBD |  |
| 3 | warm | TBD |  |
| 4 | warm | TBD |  |
| 5 | warm | TBD |  |

## Decision Gate

- P50 latency: TBD
- P95 latency: TBD
- If P95 exceeds 3000 ms, keep Redis caching mandatory and show explicit cold-start loading state.

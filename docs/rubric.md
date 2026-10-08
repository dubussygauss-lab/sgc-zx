# Grand Challenge track rubric

Fetched 2026-10-08 16:59 UTC by `submit/read_rubric.py` from `https://aqora.io/graphql`, `eventBySlug(slug: "quantinuum-sg-grand-challenge")`. [F] unless marked.

Event: **Quantinuum Singapore Grand Challenge** (id `AEV2ZW50AZ9cONFudoCyPTWIJlA1QQ`)

## Track: Quantinuum Singapore Grand Challenge (`quantinuum-sg-grand-challenge`, id `AENvbXBldGl0aW9uAZ9cONGGeuK3ETn8yu9zBQ`)

- noCode: `True`
- requiresApproval: `True`
- validUntil (stage deadline): `None`

### Scoring criteria

| # | title | weight | description |
|---|---|---|---|
| 1 | Problem & Value  | 0.3 | Judge on: need clarity; solution fit; quantified customer or business value Evidence to cite: problem/user validation; use-case evidence; business case or ROI |
| 2 | Technical Performance & Hardware Use | 0.3 | Judge on: correctness; benchmark gains; scalability; hardware utilization Evidence to cite: benchmark data; run logs; job metadata; demo results |
| 3 | Scientific Merit | 0.2 | Judge on: novelty; methodological rigor; improvement versus a baseline Evidence to cite: algorithm rationale; baseline comparison; error and validation analysis |
| 4 | Engineering & Reproducibility | 0.2 | Judge on: code structure; testing; documentation; repeatable setup Evidence to cite: repository; README; test results; reproduction record  |

### Submission preamble

(empty)

## Raw response

```json
{
 "eventBySlug": {
  "competitions": {
   "nodes": [
    {
     "competition": {
      "currentStage": {
       "noCode": true,
       "requiresApproval": true,
       "scoringCriteria": [
        {
         "description": "Judge on: need clarity; solution fit; quantified customer or business value\nEvidence to cite: problem/user validation; use-case evidence; business case or ROI",
         "title": "Problem & Value ",
         "weight": 0.3
        },
        {
         "description": "Judge on: correctness; benchmark gains; scalability; hardware utilization\nEvidence to cite: benchmark data; run logs; job metadata; demo results",
         "title": "Technical Performance & Hardware Use",
         "weight": 0.3
        },
        {
         "description": "Judge on: novelty; methodological rigor; improvement versus a baseline\nEvidence to cite: algorithm rationale; baseline comparison; error and validation analysis",
         "title": "Scientific Merit",
         "weight": 0.2
        },
        {
         "description": "Judge on: code structure; testing; documentation; repeatable setup\nEvidence to cite: repository; README; test results; reproduction record\n",
         "title": "Engineering & Reproducibility",
         "weight": 0.2
        }
       ],
       "submissionPreamble": null,
       "validUntil": null
      },
      "id": "AENvbXBldGl0aW9uAZ9cONGGeuK3ETn8yu9zBQ",
      "slug": "quantinuum-sg-grand-challenge",
      "title": "Quantinuum Singapore Grand Challenge"
     }
    }
   ]
  },
  "id": "AEV2ZW50AZ9cONFudoCyPTWIJlA1QQ",
  "title": "Quantinuum Singapore Grand Challenge"
 }
}
```

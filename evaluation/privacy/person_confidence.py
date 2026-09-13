import json, sys, statistics

with open(sys.argv[1]) as f:
    data = json.loads(f.readline())

scores = data["confidence_score"]
print(f"Mean: {statistics.mean(scores):.2f}")
print(f"Std:  {statistics.stdev(scores):.2f}")
print(f"Min:  {min(scores)}")
print(f"Max:  {max(scores)}")
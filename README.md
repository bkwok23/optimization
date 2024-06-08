# optimization

Primary Objective: Find a method to accurately test a funds estimated active risk

To answer this question, we will test 2 strategies to best replicate an equal weighted canadian bank portfolio under the constrainst that we need to hold a minimal cash balance.
1. The first (default) method is to keep the minimal cash balance and invest the remaining portion of the portfolio idential to the benchmark.
2. The second method is to use the estimated active risk method and minimize this value to replicate the index. This calculation will be found in the optimization.py file.

If the second replication method has a better performance then we can suggest that we have an accurate method to measure a funds estimated active risk.

Next Steps:
Break down the securities into factors rather than viewing them as individual features. This will allow us to use this method for a portfolio with more securities.
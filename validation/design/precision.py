#!/usr/bin/env python3
"""Approximate paired-binary planning only. Author: Angelis Pseftis."""
import argparse,json,math
from statistics import NormalDist

def plan(q,margin=.05,power=.8,alpha=.05,cluster_size=1,rho=0):
 if not 0<q<=1 or not 0<margin<1 or not .5<power<1 or not 0<alpha<.5 or cluster_size<1 or not 0<=rho<1:raise ValueError('Invalid planning assumptions; zero observed discordance is not zero required sample size')
 # D=C_accept-A_accept in {-1,0,1}; assume true mean zero and P(D!=0)=q.
 # One-sided large-sample normal approximation, not exact paired NI design.
 z=NormalDist().inv_cdf(1-alpha)+NormalDist().inv_cdf(power)
 n=math.ceil(z*z*q/(margin*margin));de=1+(cluster_size-1)*rho
 return {'assumed_discordance_probability':q,'assumed_true_acceptance_difference':0,'margin':margin,'power':power,'one_sided_alpha':alpha,'approx_independent_task_pairs':n,'assumed_cluster_size':cluster_size,'assumed_intracluster_correlation':rho,'heuristic_design_effect':de,'approx_tasks_with_design_effect':math.ceil(n*de),'status':'planning_sensitivity_only','limitation':'Not an exact NI test or validated sample-size commitment. Requires representative discordance assumptions, cluster-aware design, endpoint definition and simulation review before confirmation.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--margin',type=float,default=.05);p.add_argument('--cluster-size',type=int,default=1);p.add_argument('--rho',type=float,default=0);a=p.parse_args();print(json.dumps({'author':'Angelis Pseftis','scenarios':[plan(q,a.margin,cluster_size=a.cluster_size,rho=a.rho) for q in [.05,.1,.2,.4]]},indent=2))
if __name__=='__main__':main()

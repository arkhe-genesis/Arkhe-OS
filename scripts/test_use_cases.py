import torch
import numpy as np
from arkhe_os.defi import DeFiCoherenceVerifier
from arkhe_os.federated import FederatedCoherenceLearner
from arkhe_os.dao import DAOCoherenceGovernor

def test_defi():
    verifier = DeFiCoherenceVerifier()
    res = verifier.verify_contract_execution("code", {"input": 1}, {"out": 1})
    print("DeFi:", res["valid"])

def test_federated():
    learner = FederatedCoherenceLearner("arch", {})
    client_res = learner.local_training_step([1,2,3], {"round": 0}, "client1")
    agg_res = learner.aggregate_updates([client_res])
    print("Federated:", agg_res["emergence_status"])

def test_dao():
    gov = DAOCoherenceGovernor("dao1")
    prop = gov.submit_proposal("test", "user1", "type1")
    vote = gov.cast_vote(prop["proposal_id"], "voter1", "yes", 100)
    final = gov.finalize_proposal(prop["proposal_id"])
    print("DAO:", final["result"])

test_defi()
test_federated()
test_dao()

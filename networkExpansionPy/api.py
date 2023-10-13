# Skeleton for a basic API using fastAPI
from fastapi import FastAPI, Query
from lib import GlobalMetabolicNetwork
from networkExpansionPy import thermo
import numpy as np
import json
import more_itertools as iter

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "networkExpansionPy API"}


@app.get("/expand")
def expand_network(seedSet: list[str] = Query(None), thermodynamics: bool = False, coenzymes: bool = False):
    """
    Expand the network given a seed set of compounds.

    Takes a list of compound IDs and returns a dictionary with two keys:
    - rxns: a list of reaction IDs
    - compounds: a list of compound IDs

    Example:
    """
    network = GlobalMetabolicNetwork()
    network.convertToIrreversible()
    network.pruneInconsistentReactions()
    network.pruneUnbalancedReactions()
    network.setMetaboliteBounds()

    if coenzymes:
        network.addGenericCoenzymes()

    if thermodynamics:
        network.pruneThermodynamicallyInfeasibleReactions()

    compounds, rxns = network.expand(seedSet)

    tmp_str = []
    for x in rxns:
        for y in x:
            tmp_str.append(str(y))

    tmp_cln = [sub.replace('nan', '') for sub in tmp_str]
    tmp_cln = iter.grouper(tmp_cln, 2, incomplete='ignore')
    tmp_cln = [list(x) for x in tmp_cln]



    return {"seeds": seedSet, "rxns": tmp_cln, "compounds": compounds, "test": coenzymes}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)

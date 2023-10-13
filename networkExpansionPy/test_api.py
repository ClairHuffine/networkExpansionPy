# Test functions for the networkExpansion API
#install pytest then run pytest to execute


# Run this to operate on windows
import nest_asyncio
nest_asyncio.apply()

import pytest
import sys
from fastapi.testclient import TestClient
from api import app
    
client = TestClient(app)

def test_read_root():
    response = client.get("/", headers={'accept': 'application/json'})
    assert response.status_code == 200
    assert response.json() == {'message':'networkExpansionPy API'}
    
def test_expand_network():
    response = client.get("/expand?seedSet=C00037&seedSet=C00041&pH=7.0", headers={'accept': 'application/json'})
    assert response.status_code == 200
    assert response.json() == {
                              "pH": "7.0",
                              "seeds": [
                                "C00037",
                                "C00041"
                              ],
                              "rxns": [
                                [
                                  "R07651",
                                  "reverse"
                                ],
                                [
                                  "R00401",
                                  "reverse"
                                ],
                                [
                                  "R07651",
                                  "forward"
                                ],
                                [
                                  "R00401",
                                  "forward"
                                ]
                              ],
                              "compounds": [
                                "C00001",
                                "C00133",
                                "C00993",
                                "C00037",
                                "C00041"
                              ]
                            }
def test_expand_network_pH9():
    response = client.get("/expand?seedSet=C00041&seedSet=C00188&pH=9.0")
    assert response.status_code == 200
    assert response.json() == {
                              "pH": "9.0",
                              "seeds": [
                                "C00041",
                                "C00188"
                              ],
                              "rxns": [
                                [
                                  "R01467",
                                  "forward"
                                ],
                                [
                                  "R08195",
                                  "forward"
                                ],
                                [
                                  "R08196",
                                  "forward"
                                ],
                                [
                                  "R06171",
                                  "forward"
                                ],
                                [
                                  "R00751",
                                  "reverse"
                                ],
                                [
                                  "R00153",
                                  "forward"
                                ],
                                [
                                  "R07651",
                                  "reverse"
                                ],
                                [
                                  "R00997",
                                  "forward"
                                ],
                                [
                                  "R00996",
                                  "forward"
                                ],
                                [
                                  "R00401",
                                  "reverse"
                                ],
                                [
                                  "R01467",
                                  "reverse"
                                ],
                                [
                                  "R08195",
                                  "reverse"
                                ],
                                [
                                  "R00751",
                                  "forward"
                                ],
                                [
                                  "R08196",
                                  "reverse"
                                ],
                                [
                                  "R06171",
                                  "reverse"
                                ],
                                [
                                  "R00153",
                                  "reverse"
                                ],
                                [
                                  "R07651",
                                  "forward"
                                ],
                                [
                                  "R00997",
                                  "reverse"
                                ],
                                [
                                  "R00401",
                                  "forward"
                                ]
                              ],
                              "compounds": [
                                "C00109",
                                "C00001",
                                "C01234",
                                "C12317",
                                "C00084",
                                "C00133",
                                "C00993",
                                "C00188",
                                "C00080",
                                "C05359",
                                "C05361",
                                "C00037",
                                "C00041",
                                "C05519",
                                "C00014",
                                "C00820"
                              ]
                            }
    
def test_expand_network_pH5():
    response = client.get("/expand?seedSet=C00041&seedSet=C00188&pH=5.0")
    assert response.status_code == 200
    assert response.json() == {
                              "pH": "5.0",
                              "seeds": [
                                "C00041",
                                "C00188"
                              ],
                              "rxns": [
                                [
                                  "R01467",
                                  "forward"
                                ],
                                [
                                  "R08195",
                                  "forward"
                                ],
                                [
                                  "R08196",
                                  "forward"
                                ],
                                [
                                  "R06171",
                                  "forward"
                                ],
                                [
                                  "R00751",
                                  "reverse"
                                ],
                                [
                                  "R07651",
                                  "reverse"
                                ],
                                [
                                  "R00997",
                                  "forward"
                                ],
                                [
                                  "R00996",
                                  "forward"
                                ],
                                [
                                  "R00401",
                                  "reverse"
                                ],
                                [
                                  "R01467",
                                  "reverse"
                                ],
                                [
                                  "R08195",
                                  "reverse"
                                ],
                                [
                                  "R00751",
                                  "forward"
                                ],
                                [
                                  "R08196",
                                  "reverse"
                                ],
                                [
                                  "R06171",
                                  "reverse"
                                ],
                                [
                                  "R07651",
                                  "forward"
                                ],
                                [
                                  "R00997",
                                  "reverse"
                                ],
                                [
                                  "R00401",
                                  "forward"
                                ]
                              ],
                              "compounds": [
                                "C00109",
                                "C00001",
                                "C01234",
                                "C12317",
                                "C00084",
                                "C00133",
                                "C00993",
                                "C00188",
                                "C00037",
                                "C00041",
                                "C05519",
                                "C00014",
                                "C00820"
                              ]
                            }
if __name__ == "__main__":
    sys.exit(pytest.main())
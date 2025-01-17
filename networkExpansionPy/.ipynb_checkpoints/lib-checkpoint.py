from scipy.sparse import csr_matrix
import numpy as np
import pandas as pd
import ray
from random import sample
import os
from copy import copy, deepcopy

# define asset path
asset_path,filename = os.path.split(os.path.abspath(__file__))
asset_path = asset_path + '/assets'

def netExp(R,P,x,b):
    k = np.sum(x);
    k0 = 0;
    n_reactions = np.size(R,1)
    y = csr_matrix(np.zeros(n_reactions))
    while k > k0:
        k0 = np.sum(x);
        y = (np.dot(R.transpose(),x) == b);
        y = y.astype('int');
        x_n = np.dot(P,y) + x;
        x_n = x_n.astype('bool');
        x = x_n.astype('int');
        k = np.sum(x);
    return x,y

# define a new network expansion, s.t. stopping criteria is now no new compounds or reactions can be added at subsequent iterations
def netExp_cr(R,P,x,b):
    k = np.sum(x);
    k0 = 0;
    n_reactions = np.size(R,1)
    y = csr_matrix(np.zeros(n_reactions))
    l = 0
    l0 = 0;
        
    while (k > k0) | (l > l0):
        k0 = np.sum(x);
        l0 = np.sum(y)
        y = (np.dot(R.transpose(),x) == b);
        y = y.astype('int');
        x_n = np.dot(P,y) + x;
        x_n = x_n.astype('bool');
        x = x_n.astype('int');
        k = np.sum(x);
        l = np.sum(y)
    return x,y


def netExp_trace(R,P,x,b):
    
    X = []
    Y = []
    
    X.append(x)
    k = np.sum(x);
    k0 = 0;
    n_reactions = np.size(R,1)
    y = csr_matrix(np.zeros(n_reactions))
    Y.append(y)
    
    while k > k0:
        k0 = np.sum(x);
        y = (np.dot(R.transpose(),x) == b);
        y = y.astype('int');
        x_n = np.dot(P,y) + x;
        x_n = x_n.astype('bool');
        x = x_n.astype('int');
        k = np.sum(x);
        X.append(x)
        Y.append(y) 
    return X,Y


def parse_reaction_trace(reaction_trace,network):
    rxns_list = []
    for i in range(1,len(reaction_trace)):
        idx = reaction_trace[i].nonzero()[0]
        rxns = list(network.iloc[:,idx])
        rxns = pd.DataFrame(rxns,columns = ['rn','direction'])
        rxns['iter'] = i
        rxns_list.append(rxns)    
    rxns_list = pd.concat(rxns_list,axis=0)
    return rxns_list


def isRxnCoenzymeCoupled(rxn,cosubstrate,coproduct):
    g = rxn[rxn.cid.isin([cosubstrate,coproduct])]
    out = False
    if len(g) > 1:
        if g.s.sum() == 0:
            out = True
    return out

class GlobalMetabolicNetwork:
    
    def __init__(self):
        # load the data
        network = pd.read_csv(asset_path + '/KEGG/network_full.csv')
        cpds = pd.read_csv(asset_path +'/compounds/cpds.txt',sep='\t')
        thermo = pd.read_csv(asset_path +'/reaction_free_energy/kegg_reactions_CC_ph7.0.csv',sep=',')
        self.network = network
        self.compounds = cpds
        self.thermo = thermo
        self.temperature = 25
        self.seedSet = None;
        
    def copy(self):
        return deepcopy(self)
        
    def set_ph(self,pH):
        if ~(type(pH) == str):
            pH = str(pH)
        try:
            thermo = pd.read_csv(asset_path + '/reaction_free_energy/kegg_reactions_CC_ph' + pH + '.csv',sep=',')
            self.thermo = thermo
        except Exception as error:
            print('Failed to open pH files (please use 5.0-9.0 in 0.5 increments)')    
    
    
    def pruneInconsistentReactions(self):
        # remove reactions with qualitatively different sets of elements in reactions and products
        consistent = pd.read_csv(asset_path + '/reaction_sets/reactions_consistent.csv')
        self.network = self.network[self.network.rn.isin(consistent.rn.tolist())]
        
    def pruneUnbalancedReactions(self):
        # only keep reactions that are elementally balanced
        balanced = pd.read_csv(asset_path + '/reaction_sets/reactions_balanced.csv')
        self.network = self.network[self.network.rn.isin(balanced.rn.tolist())]
        
    def subnetwork(self,rxns):
        # only keep reactions that are in list
        self.network = self.network[self.network.rn.isin(rxns)]
        
    def addGenericCoenzymes(self):
        replace_metabolites = {'C00003': 'Generic_oxidant', 'C00004': 'Generic_reductant', 'C00006': 'Generic_oxidant',  'C00005': 'Generic_reductant','C00016': 'Generic_oxidant','C01352':'Generic_reductant'}
        coenzyme_pairs = {}
        coenzyme_pairs['NAD'] = ['C00003','C00004']
        coenzyme_pairs['NADP'] = ['C00006','C00005']
        coenzyme_pairs['FAD'] = ['C00016','C01352']
        coenzyme_pairs = pd.DataFrame(coenzyme_pairs).T.reset_index()
        coenzyme_pairs.columns = ['id','oxidant','reductant']
        # create reactions copies with coenzyme pairs
        new_rxns = []
        new_thermo = [];
        for idx,rxn in self.network.groupby('rn'):
            z = any([isRxnCoenzymeCoupled(rxn,row.oxidant,row.reductant) for x,row in coenzyme_pairs.iterrows()])
            if z:
                new_rxn = rxn.replace(replace_metabolites).groupby(['cid','rn']).sum().reset_index()
                new_rxn['rn'] = new_rxn['rn'] = idx + '_G'
                new_rxns.append(new_rxn)
                t = self.thermo[self.thermo['!MiriamID::urn:miriam:kegg.reaction'] == idx].replace({idx:  idx + '_G'})
                new_thermo.append(t)

        new_rxns = pd.concat(new_rxns,axis=0)
        new_thermo = pd.concat(new_thermo,axis=0)

        self.network = pd.concat([self.network,new_rxns],axis=0)
        self.thermo = pd.concat([self.thermo,new_thermo],axis=0)

    
    def convertToIrreversible(self):
        nf = self.network.copy()
        nb = self.network.copy()
        nf['direction'] = 'forward'
        nb['direction'] = 'reverse'
        nb['s'] = -nb['s']
        net = pd.concat([nf,nb],axis=0)
        net = net.set_index(['cid','rn','direction']).reset_index()
        self.network = net
    
    def setMetaboliteBounds(self,ub = 1e-1,lb = 1e-6): 
        
        self.network['ub'] = ub
        self.network['lb'] = lb
      
    def pruneThermodynamicallyInfeasibleReactions(self,keepnan = False):
        fixed_mets = ['C00001','C00080']

        RT = 0.008309424 * (273.15+self.temperature)
        rns  = []
        dirs = []
        dgs = []
        for (rn,direction), dff in self.network.groupby(['rn','direction']):
            effective_deltaG = np.nan
            if rn in self.thermo['!MiriamID::urn:miriam:kegg.reaction'].tolist():
                deltaG = self.thermo[self.thermo['!MiriamID::urn:miriam:kegg.reaction'] == rn]['!dG0_prime (kJ/mol)'].values[0]
                if direction == 'reverse':
                    deltaG = -1*deltaG

                dff = dff[~dff['cid'].isin(fixed_mets)]
                subs = dff[dff['s'] < 0]
                prods = dff[dff['s'] > 0];
                k = np.dot(subs['ub'].apply(np.log),subs['s']) + np.dot(prods['lb'].apply(np.log),prods['s'])

                effective_deltaG = RT*k + deltaG

            dgs.append(effective_deltaG)
            dirs.append(direction)
            rns.append(rn)

        res = pd.DataFrame({'rn':rns,'direction':dirs,'effDeltaG':dgs})
        if ~keepnan:
            res = res.dropna()
        
        res = res[res['effDeltaG'] < 0].set_index(['rn','direction'])
        res = res.drop('effDeltaG',axis=1)
        self.network = res.join(self.network.set_index(['rn','direction'])).reset_index()
    
    def initialize_metabolite_vector(self,seedSet):
        if seedSet is None:
            print('No seed set')
        else:
            network = self.network.pivot_table(index='cid',columns = ['rn','direction'],values='s').fillna(0)
            x0 = np.array([x in seedSet for x in network.index.get_level_values(0)]) * 1;        
            return x0
        
    def expand(self,seedSet,algorithm='naive'):
        # constructre network from skinny table and create matricies for NE algorithm
        x0 = self.initialize_metabolite_vector(seedSet)
        network = self.network.pivot_table(index='cid',columns = ['rn','direction'],values='s').fillna(0)
        S = network.values
        R = (S < 0)*1
        P = (S > 0)*1
        b = sum(R)

        # sparsefy data
        R = csr_matrix(R)
        P = csr_matrix(P)
        b = csr_matrix(b)
        b = b.transpose()

        x0 = csr_matrix(x0)
        x0 = x0.transpose()
        if algorithm.lower() == 'naive':
            x,y = netExp(R,P,x0,b)
        elif algorithm.lower() == 'cr':
            x,y = netExp_cr(R,P,x0,b)
        else:
            raise ValueError('algorithm needs to be naive (compound stopping criteria) or cr (reaction/compound stopping criteria)')
        
        # convert to list of metabolite ids and reaction ids
        if x.toarray().sum() > 0:
            cidx = np.where(x.toarray().T[0])[0]
            compounds = network.iloc[cidx].index.get_level_values(0).tolist()
        else:
            compounds = []
            
        if y.toarray().sum() > 0:
            ridx = np.where(y.toarray().T[0])[0]
            ridx = np.where(y.toarray().T[0])[0]
            reactions = list(network.iloc[:,ridx])
        else:
            reactions = [];
            
        return compounds,reactions


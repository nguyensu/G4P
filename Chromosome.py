'''
This file define the Chromosome representation using the grammar defined in 
Grammatical_Evolution_mapper.py

In particular it defines the representations of a single chromosome as a:
- genotype (a sequence of random integer genes)
- phenotype (a derivation tree builded using both genotype and Grammar rules)
- solution (a python code generated through the phenoype)

and defines the corresponding functions to generate them.
'''


from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from anytree.dotexport import RenderTreeGraph
from anytree import PreOrderIter
import numpy as np

import Grammatical_Evolution_mapper as GE


class Chromosome():
    def __init__(self, GENOTYPE_LEN):
        ''' 
        Parameters : GENOTYPE_LEN (number of genes of the genotype)
        Attributes : - genotype (list of integer that corresponds to the set of genes of the genotype)
                     - phenotype (derivation tree rappresentation of the chromosome, that corresponds to the set of genes (nodes) encoded by the genotype)
                     - solution (python code rappresentation of the chromosome, that corresponds to the set of genes (line of codes) translated by the phenotype)
                     - fitness (fitness score of this chromosome)
        '''
        self.genotype = [np.random.randint(1,3)]+list(np.random.randint(0,1000,size=GENOTYPE_LEN-1)) # ensure that it starts with rule 1 or 2
        self.phenotype = None
        self.solution = None
        self.fitness = None

    def generate_phenotype(self, method, MAX_DEPTH, MAX_WRAP=5, to_png=False, to_shell=False):
        '''
        Generate phenotype from genotype (derivation tree from a list of int )
        Genotype-phenotype mapping function is the MOD operator between genes of the genotype and rules of the Grammar. 

        Parameters : MAX_DEPTH (maximum depth of the generated phenotypes' derivation trees)
                     MAX_WRAP  (maximum number of time that wrapping operator is applied to genotype)
        '''
        root = Node('('+str(0)+')expr-start', label='expr', code='')                      # root of derivation tree
        self.phenotype = GE.start_derivating(self.genotype, root, method, MAX_DEPTH, MAX_WRAP, _initial_gene_seq = self.genotype)

        if to_shell:
            for pre, _, node in RenderTree(self.phenotype):                                # print tree on terminal
                print("{}{}".format(pre, node.name)) 
        if to_png:
            RenderTreeGraph(self.phenotype, nodeattrfunc=lambda node: 'label="{}"'.format( # export tree .png file
                node.label)).to_picture("tree_phenotype.png")                              #


    def generate_solution(self, write_to_file=False):
        '''
        Generate solution (python program)
        Pprogram representation of the phenotype obtained doing PRE-ORDER starting from root node (phenotype)
        and collecting all node.code properties, concatenating them in a string variable.
        '''
        program_chromosome="def get_action(observation, states):\n\t"                   # Prepare program whit func def and return value
        for node in PreOrderIter(self.phenotype):   
            program_chromosome+= node.code                                              # get generated program
        program_chromosome+="\n\treturn action"                                          #
        
        self.solution = program_chromosome

        if write_to_file:
            file = open('program_solution.py', 'w')                                    # Create file and write in generated programs'string
            file.write(self.solution)                                                  #
            file.close()   

    def execute_solution(self, observation, states):
        '''
        Execute self.solution as python program
        Parameters : observation (list of states of the environment)
                     states (list of all possible states of an observation of the environment)
        Return value: an action
        '''
        loc={}
        exec(self.solution, {}, loc)
        try:
            action=loc['get_action'](observation, states)
        except UnboundLocalError:   #observation did not pass through any if else
            print('Assign low fitness')
            action= np.random.randint(0,2) #there (action_space.n)
        
        return action
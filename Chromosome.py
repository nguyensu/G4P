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
import os

from Grammatical_Evolution_mapper import Parser


class Chromosome():
    ''' 
    Chromosome defines the representations of a single individuals as:
    its genotype (sequence of int), phenotype (tree) and solution (string code)
    
    Args:
        GENOTYPE_LEN (int): number of genes of the genotype
    
    Attributes: 
        genotype (list(int)): the set of genes of the genotype
        phenotype (AnyTree.Node): derivation tree rappresentation of the chromosome, that corresponds to the set of genes (nodes) encoded by the genotype
        solution (str): python code rappresentation of the chromosome, that corresponds to the set of genes (line of codes) translated by the phenotype
    '''
    def __init__(self, i, GENOTYPE_LEN):
        self.genotype = [np.random.randint(1,3)]+list(np.random.randint(0,1000,size=GENOTYPE_LEN-1)) # ensure that it starts with rule 1 or 2
        self.phenotype = None
        self.solution = None
        self.cid = i
        self.fit=None

    def generate_phenotype(self, environment, method, MAX_DEPTH, MAX_WRAP, to_png=False, to_shell=False):
        '''
        Generate phenotype from genotype (derivation tree from a list of int).
        Genotype-phenotype mapping function is the MOD operator between genes of the genotype and rules of the Grammar. 
        
        Args:
            environment (Environment)
            method (str): method used for generate the tree (full or grow)
            MAX_DEPTH (int): maximum depth of the generated phenotypes' derivation trees
            MAX_WRAP  (int): maximum number of time that wrapping operator is applied to genotype
            to_png (boolean): export tree on png file
        '''
        root = Node('('+str(0)+')expr-start', label='expr', code='', color='/greys9/1', border='/greys9/9')                     # root of derivation tree
        parser = Parser(self.genotype, root, environment, method, MAX_DEPTH, MAX_WRAP)
        
        self.phenotype = parser.start_derivating('expr')
        if to_shell:
            for pre, _, node in RenderTree(self.phenotype):                                # print tree on terminal
                print("{}{}".format(pre, node.name)) 
        if to_png:
            self.tree_to_png(generation=0)


    def generate_solution(self, generation=0, to_file=False):
        '''
        Generate solution (python program)
        The program representation of the phenotype is obtained doing PRE-ORDER starting from root node (phenotype)
        and collecting all node.code properties, concatenating them in a string variable.

        Args:
            to_file (bool): write program to a file
        '''
        program_chromosome="def get_action(observation, all_obs):\n\t"                   # Prepare program whit func def and return value
        for node in PreOrderIter(self.phenotype):   
            program_chromosome+= node.code                                              # get generated program
        program_chromosome+="\n\treturn action"                                          #
        
        self.solution = program_chromosome

        if to_file:
            if not os.path.exists('./outputs/GEN-{}'.format(generation)):
                os.mkdir('./outputs/GEN-{}'.format(generation))
            file = open("./outputs/GEN-{}/{}-{}.py".format(generation, self.cid,str(self).rsplit('<Chromosome.Chromosome object at ')[1][:-1]), 'w')                                    # Create file and write in generated programs'string
            file.write(self.solution)                                                  #
            file.close()   

    def execute_solution(self, observation, all_obs):
        '''
        Execute self.solution as python program
        
        Args:
            observation (list(float)): list of all_obs of the environment
            all_obs (list(list(float))): list of all possible all_obs of an observation of the environment
        
        Returns: an action
        '''
        loc={}
        try:
            exec(self.solution, {}, loc)
        except SyntaxError as e:
            import sys
            print(e.msg)
            self.tree_to_png(0)
            self.generate_solution(0, True)
            for pre, _, node in RenderTree(self.phenotype):                                # print tree on terminal
                print("{}{}".format(pre, node.name)) 

            sys.exc_info()
            sys.exit()
        try:
            action=loc['get_action'](observation, all_obs)
        except UnboundLocalError:   #observation did not pass through any if else
            # print('Assign low fitness')
            action= 0
            # action = None
        
        return action
    
    def tree_to_png(self, generation):
        if not os.path.exists('./outputs/GEN-{}'.format(generation)):
            os.mkdir('./outputs//GEN-{}'.format(generation))
        DotExporter(self.phenotype, 
            nodeattrfunc=lambda node: 'label="{}", style=filled, color="{}", fillcolor="{}"'.format(node.label, node.border, node.color),
            edgeattrfunc=lambda node,child: 'color="{}"'.format(node.border)
            ).to_picture("./outputs/GEN-{}/{}-{}.png".format(generation, self.cid, str(self).rsplit('<Chromosome.Chromosome object at ')[1][:-1]))
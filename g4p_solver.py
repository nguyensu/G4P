'''
This is the main execution files that use class utilities from Genetic_Gym.py

In particular it defines:
- evolve() function that describe the population flow (init, evaluate, select, crossingover, mutate, ...)
- main() function execute evolve() using parametrized Genetic_Gym.Population and Genetic_Gym.Environment,
plotting all single generation chromosomes and their population informations in multiple graphs
and finally (and eventually) showing the evolved chromosome in action
'''


import numpy as np
import time
import gym
import gym.wrappers as wrappers
import gym.spaces as spaces
from collections import deque
import matplotlib.pyplot as plt         
from mpl_toolkits.mplot3d import Axes3D
from multiprocessing import Pool
import multiprocessing

from anytree.exporter import DotExporter
import os, shutil

from Genetic_Gym import Population, Environment



def evolve(population, environment, initial_n_chr, n_generations, genotype_len, MAX_DEPTH, seed):
    np.random.seed(seed)
    environment.seed = seed

    all_populations=[]

    ##-------INIT POPULATION--------##
    # get initial chromosomes generated by the set of genotype 
    population.initialize_chromosomes(initial_n_chr, genotype_len, MAX_DEPTH, MAX_WRAP=2)
    pool = Pool(multiprocessing.cpu_count())
    #------------------------------#
    
    for generation in range(n_generations):
        #--------------EVALUATE MODELS--------------#
        population.chromosomes_scores   = environment.parallel_evaluate_population(population, pool, to_file=False)

        population.chromosomes_fitness  = np.mean(population.chromosomes_scores, axis=1)
        #------------------------------#

        #-------------EXIT IF CONVERGED-------------#
        print('\n ****** Generation', generation+1, 'max score = ', max(population.chromosomes_fitness), ' elite_threashold = ',np.mean(population.chromosomes_fitness),' ******\n')
        population.best_individual = population.chromosomes[np.argmax(population.chromosomes_fitness)]
        all_populations.append(population)
        if environment.converged:
            break
        #------------------------------#

        #-------------NATURAL SELECTION-------------#
        population.survival_threashold  = np.mean(population.chromosomes_fitness)

        # for i,chromosome in enumerate(population.chromosomes):
        #     if population.chromosomes_fitness[i]>=population.survival_threashold:
        #         chromosome.tree_to_png(generation)
        #         chromosome.generate_solution(generation, to_file=True)

        population.do_natural_selection()
        
        elites_len = len(population.chromosomes)
        #------------------------------#

        #--------------CROSSING OVER--------------# 
        
        ranks = list(reversed(np.argsort(population.chromosomes_fitness)))

        offsprings = []
        jobs=[]
        random_seeds=[]
        for i in range(elites_len):
            seed_i=[]
            for j in range(i+1, elites_len):
                seed_i.append(np.random.randint(2**32 - 1))
            random_seeds.append(seed_i)

        for i in range(elites_len):
            for j in range(i+1,elites_len):
                jobs.append(pool.apply_async(population.crossover, [
                            population.chromosomes[ranks[i]], population.chromosomes[ranks[j]],
                            random_seeds[i][j-i-1]
                            ]))
        for j in jobs:
            child1,child2=j.get()
            offsprings.append(child1)
            offsprings.append(child2)        
        #------------------------------#

        #----------------MUTATION----------------#
        mutated_offsprings = [population.mutate(child) for child in offsprings]    

        #------------------------------#

        #-----------NEXT GENERATION-----------# 
        # population = elite
        population = Population(mutation_prob=population.mutation_prob, crossover_prob=population.crossover_prob, max_elite=population.max_elite, bins=environment.bins)
        population.chromosomes = mutated_offsprings
        print('( childs=', len(offsprings), ' tot_pop=', len(population.chromosomes),' )\n\n')
        #------------------------------#
        
    pool.close()
    return all_populations





if __name__ == '__main__':
    if os.path.exists('./outputs'):
        shutil.rmtree('./outputs')
    os.mkdir('./outputs')

    sid = input('Input seed for RNG    [ENTER for default, r for random]    ')
    if sid=='':
        sid=1234
    if sid=='r':
        sid=np.random.randint(2**32 - 1)
        print('using ', sid)
    else:
        sid=int(sid)

    abs_time_start = time.time()
    environment = Environment(
            env_id          = 'CartPole-v0',
            n_episodes      = 150,
            bins            = (6,3,6,5)
        )
    population = Population(
        mutation_prob   = 0.9,
        crossover_prob  = 0.9,
        max_elite       = 10,
        bins            = environment.bins
    )
    

    all_populations = evolve(
        population, 
        environment, 
        initial_n_chr = 200, 
        n_generations = 5,
        seed          = sid,
        genotype_len  = 20,
        MAX_DEPTH     = 5
    )
    # env, best_policy, all_populations = evolve('MountainCar-v0', 200, 50, (7,2), sid=sid, mut_prob=0.17, max_elite=11)#333555669

    abs_time= time.time() - abs_time_start
    
    #---------------plotting-------------#
    print('Plotting ... ')


    for generation, population in enumerate(all_populations):
        population.best_individual.tree_to_png(generation)
        population.best_individual.generate_solution(generation, to_file=True)

    ep_len = len(all_populations[0].chromosomes_scores[0])
    z_axys = np.arange(ep_len)
    for i,population in enumerate(all_populations):
        ax= plt.figure(figsize=(20, 19)).add_subplot(111, projection='3d')
        best_idx = np.argmax(population.chromosomes_fitness)
        if len(population.chromosomes_scores)>12:
            low =  0 if best_idx-5<0 else best_idx-10 if best_idx+5>=len(population.chromosomes_scores) else best_idx-5
            high = len(population.chromosomes_scores) if best_idx+5>=len(population.chromosomes_scores)-1 else best_idx+5
            scores = np.array(population.chromosomes_scores)[range(low, high)] 
        else:
            scores = population.chromosomes_scores
        print(len(population.chromosomes_scores), len(scores))
        ax.set_xticks( np.arange(len(scores)) )
        for j,score in enumerate(scores):
            ax.plot(np.full(ep_len, j, int)  , z_axys, score, zorder=j)

        ax.set_zlabel("Rewards")
        ax.set_ylabel("Episode")
        ax.set_xlabel("Chromosome")
        
        title=  environment.env.spec.id+" solved in {} generations\n".format(len(all_populations)-1)
        title += "time elapsed = {} sec\n".format(abs_time)
        title += "GENERATION [ {} / {} ]".format(i, len(all_populations)-1)
        plt.title(title)
        save_dir = './outputs/GEN-{}/'.format(i)
        plt.savefig(save_dir+'plot.png', bbox_inches='tight')
    print('used seed = ', sid)
    #--------------evaluate--------------------#
    wrap = input('Do you want to run the evolved policy and save it?    [y/N]    ')
    if wrap=='y':
        import os
        save_dir = './outputs/'+environment.env.spec.id+'_results/' + str(time.time()) + '/'
        # env.seed(0)
        environment.env = wrappers.Monitor(environment.env, save_dir, force=True)
        best_policy = all_populations.pop().best_individual
        for episode in range(ep_len):
            environment.run_one_episode(environment.env, best_policy, episode, prnt=True)
        environment.env.env.close()
    else:
        environment.env.close()
    

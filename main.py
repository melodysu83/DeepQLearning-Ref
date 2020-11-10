#!/usr/bin/env python
import param
from train import Trainer
from evaluate import Evaluator
from visualize import Progress_viz
from environments import environment_setup, DogAdventure, DogAdventureEnvironment

if __name__ == '__main__':

    print("Step 1: Environment Setup")
    dogEnvironment = DogAdventureEnvironment(DogAdventure())
    train_env, eval_env = environment_setup(dogEnvironment)

    print("Step 2: Trainer Setup")
    dogTrainer = Trainer(train_env, n_iterations=param.TRAIN_ITER, visual_flag=param.VIZ_FLAG)

    # generate training trajectories
    dogTrainer.data_generation()

    # run under common to improve efficiency
    dogTrainer.make_common()

    print("Step 3: Train the Model")
    metrics, losses = dogTrainer.train_agent()

    print("Step 4: Evaluate Learning Result")
    # Reset the train step
    dogTrainer._agent.train_step_counter.assign(0)

    # Evaluate the agent's policy once before training.
    dogEvaluator = Evaluator(eval_env, dogTrainer._agent, dogTrainer._replay_buffer, 
                             dogTrainer._train_step, episodes=param.EVAL_EPISODE, 
                             visual_flag=param.VIZ_FLAG)
    dogEvaluator.evaluate_agent()

    print("Step 5: Checkpoint Saver")
    dogEvaluator.save_model()
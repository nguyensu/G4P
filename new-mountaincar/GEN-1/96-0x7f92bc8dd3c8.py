def get_action(observation, all_obs):
	if observation[1] > all_obs[1][7]:
		if observation[1] <= all_obs[1][6]:
			if observation[1] <= all_obs[1][0]:
				action = 0

		else:
			action = 1

			action = 2

	else:
		if observation[0] <= all_obs[0][4]:
			if observation[1] <= all_obs[1][6]:
				action = 0

			else:
				action = 1

		else:
			action = 1

			action = 0

	return action
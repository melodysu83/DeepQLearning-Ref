import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import param


def get_loopstep(timestep):
	# repeat animation when timestep larger than animation length
	loopstep = timestep % (2*param.ANIMATION_LENGTH)
	if loopstep >= param.ANIMATION_LENGTH:
		loopstep = 2*param.ANIMATION_LENGTH - loopstep -1
		flipped = True
	else:
		flipped = False
	return loopstep, flipped


def breath_deform_factor(breathdata, loopstep):
	# decide breathing factor based on timestep
	assert loopstep >= 0 and loopstep < param.ANIMATION_LENGTH
	deform_factor = breathdata[0,loopstep]
	deform_factor = deform_factor/38+1
	return deform_factor

def dynamic_camZ_from_data(breathdata, normX, normY, timestep):
	# find camera height based on timestep
	loopstep, flipped = get_loopstep(timestep)
	deform_factor = breath_deform_factor(breathdata, loopstep)
	normZ = deform_factor * np.sqrt(- normX*normX - normY*normY + 2)
	return normZ

def dynamic_toolinfo_from_data(tooldata, timestep):
	# get the dynamic tool pose information from the mat file
	loopstep, flipped = get_loopstep(timestep)
	toolinfo = tooldata[loopstep,:]
	for i in range(param.TOOL_STATE_DIM):
		if i == 3 or i == 4:
			toolinfo[i] = toolinfo[i] * 2.0 / np.pi      		        # normalize angles
		else:
			toolinfo[i] = toolinfo[i] * 1.0 / param.BELLY_EDGE_LENGTH	# normalize pos and vel
	if flipped is True:
		toolinfo[5] = - toolinfo[5]                             # flip velocity direction
		toolinfo[6] = - toolinfo[6]   
	return toolinfo


def calculate_angle(camZ, camP, toolZ, toolP):
	# calculate the rotation angle in direction P
	angle = np.arctan2(camP - toolP, camZ - toolZ)
	norm_angle = angle*2 / np.pi
	if norm_angle <= -1.0 and norm_angle >= 1.0:
		print("[WARNING]: camera angle exceeds pi/2 limit. The system will keep running.")

	return norm_angle

def calculate_action_reward(response):
	# calculate part of the reward value based on action consequences
	if response == param.ActionResult.END_GAME:
		action_reward = 10.0
	elif response == param.ActionResult.ILLEGAL_MOVE:
		action_reward = -2.0
	else:
		action_reward =  0.3
	return action_reward

def calculate_reconst_reward(surgicaldata,state,timestep):
	# calculate part of the reward value based on reconstructability
	reconst_reward = 0.0 # TODO
	return reconst_reward

def get_tool_pose(obs, tool_idx):
	# get the pose of the ith tool from observations
    assert obs.shape[0] == param.CAM_STATE_DIM*param.CAM_COUNT + param.TOOL_STATE_DIM*param.TOOL_COUNT
    assert tool_idx >= 0 and  tool_idx < param.TOOL_COUNT
    offset = param.CAM_STATE_DIM*param.CAM_COUNT
    return obs[offset+param.TOOL_STATE_DIM*tool_idx:offset+param.TOOL_STATE_DIM*(tool_idx+1)]

def get_cam_pose(obs, cam_idx):
	# get the pose of the ith camera from observations
    assert obs.shape[0] == param.CAM_STATE_DIM*param.CAM_COUNT + param.TOOL_STATE_DIM*param.TOOL_COUNT
    assert cam_idx >= 0 and  cam_idx < param.CAM_COUNT
    return obs[param.CAM_STATE_DIM*cam_idx:param.CAM_STATE_DIM*(cam_idx+1)] 

def revert_normalize_cam(campose):
	# revert feature normalization for campose
    campose[:3] = campose[:3] * param.BELLY_EDGE_LENGTH
    campose[3:] = campose[3:] * np.pi / 2
    return campose
        
def revert_normalize_tool(toolpose):
	# revert feature normalization for toolpose
    for i in range(param.TOOL_STATE_DIM):
        if i == 3 or i == 4:
        	toolpose[i] = toolpose[i] * np.pi / 2.0     		        # normalize angles
        else:
        	toolpose[i] = toolpose[i] * param.BELLY_EDGE_LENGTH	        # normalize pos and vel
    return toolpose

def truncated_cam_cone(campose, conesize, coneR1):
    # plot the truncated cone representing the camera view
    p_base = campose[:3]
    # vector in direction of axis
    tanx = np.tan(campose[3])
    tany = np.tan(campose[4])
    v = [-conesize*tanx, -conesize*tany, -conesize]
    # find magnitude of vector
    mag = np.linalg.norm(v)
    # unit vector in direction of axis
    v = v / mag
    # make some vector not in the same direction as v
    not_v = np.array([1, 1, 0])
    if (v == not_v).all():
        not_v = np.array([0, 1, 0])
    # make vector perpendicular to v
    n1 = np.cross(v, not_v)
    # print n1,'\t',norm(n1)
    # normalize n1
    n1 /= np.linalg.norm(n1)
    # make unit vector perpendicular to v and n1
    n2 = np.cross(v, n1)
    # surface ranges over t from 0 to length of axis and 0 to 2*pi
    n = 20
    t = np.linspace(0, mag, n)
    theta = np.linspace(0, 2 * np.pi, n)
    # use meshgrid to make 2d arrays
    t, theta = np.meshgrid(t, theta)
    R = np.linspace(param.CONE_R0, coneR1, n)
    # generate coordinates for surface
    X, Y, Z = [p_base[i] + v[i] * t + R *
               np.sin(theta) * n1[i] + R * np.cos(theta) * n2[i] for i in [0, 1, 2]]

    return X, Y, Z

    
def mkdir_p(mypath):
    # Creates a directory. equivalent to using mkdir -p on the command line
    from errno import EEXIST
    from os import makedirs,path

    try:
        makedirs(mypath)
    except OSError as exc: # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else: raise

import numpy as np
import time
import pickle
import matplotlib.pyplot as plt

from dm_noise_simulator_wrapper import dm_noise_simulator_instantaneous_wrapper
from get_noise_distribution import not_autocorr_stdv

def get_baseline_counts():
    x = np.arange(m1)
    y = np.arange(m2)

    xx, yy = np.meshgrid(x,y)
    xx = xx.flatten()
    yy = yy.flatten()

    p = np.vstack([xx,yy]).T #positions

    baseline_counts = {}
    for i in range(m1*m2):
        for j in range(i,m1*m2):
            b = tuple(p[j]-p[i])
            if b in baseline_counts.keys():
                baseline_counts[b] += 1
            else:
                baseline_counts[b] = 1

    baselines = np.asarray(list(baseline_counts.keys()),dtype = np.float32) * np.array([L1, L2])
    counts = np.asarray(list(baseline_counts.values()),dtype=np.int32) 
    return baselines, counts

def ang2vec (theta,phi):
    return np.array([np.cos(phi)*np.sin(theta),np.sin(phi)*np.sin(theta), np.cos(theta)]).T

def get_tan_plane_pixelvecs (nx,ny, base_theta, base_phi, extent1, extent2):
    basevec = ang2vec(base_theta, base_phi)
    v1 = ang2vec(base_theta - np.pi/2, base_phi)
    v2 = np.cross(v1, basevec)
    
    xls = np.linspace(-1,1,nx) * np.tan(extent1)
    yls = np.linspace(-1,1,ny) * np.tan(extent2)
    testvecs = (basevec[np.newaxis, np.newaxis, :]
      + v1[np.newaxis, np.newaxis, :] * yls[:, np.newaxis, np.newaxis]
      + v2[np.newaxis, np.newaxis, :] * xls[np.newaxis, :, np.newaxis])

    #normalizing
    norms = np.linalg.norm(testvecs, axis=2)
    np.divide(testvecs[:,:,0],norms, testvecs[:,:,0])
    np.divide(testvecs[:,:,1],norms, testvecs[:,:,1])
    np.divide(testvecs[:,:,2],norms, testvecs[:,:,2])
    return testvecs

def get_radec_pixelvecs (nx,ny, base_theta, base_phi, delta_theta, delta_phi):
	vecs = np.empty([nx*ny,3])
	phi_array = np.linspace(base_phi-delta_phi/2, base_phi+delta_phi/2, nx)
	theta_array = np.linspace(base_theta-delta_theta/2, base_theta+delta_theta/2, ny)
	for i in range(nx*ny):
		vecs[i] = ang2vec(theta_array[i//nx], phi_array[i%nx])
	return vecs

if __name__ == "__main__":
    t1 = time.time()
    
    m1 = 22 #ew
    m2 = 24 #ns
    L1 = 6.3
    L2 = 8.5
    baselines, baseline_counts = get_baseline_counts()
    wavelength = 0.21
    
    base_theta = np.deg2rad(90-49.322)
    base_phi = 0
    nx = 600
    ny = 150
    extent1 = np.deg2rad(12)
    extent2 = np.deg2rad(3)
    
    chord_dec = 49.322
    dish_diameter = 6 #m
    ang_resolution = 2 #deg
    ntimesamples = int(360/ang_resolution)
    noise = not_autocorr_stdv(3600.0*24/ntimesamples) / 1000 #mJy

    #u = get_tan_plane_pixelvecs(nx,ny, base_theta, base_phi, extent1, extent2).reshape([nx*ny,3])
    u = get_radec_pixelvecs (nx,ny, base_theta, base_phi, extent2, extent1)
    
    dirtymap = dm_noise_simulator_instantaneous_wrapper (noise, u, baselines, baseline_counts, wavelength, chord_dec, dish_diameter)
    dirtymap = np.reshape(dirtymap, [ny,nx])
    
    t2 = time.time()
    print("Dirtymap noise simulator took", t2-t1, "seconds")

    plt.imshow(dirtymap, interpolation="none", origin="lower")
    plt.savefig("instantaneous noise map", bbox_inches = 'tight', pad_inches = 0.5)

from astropy.io import fits
from astropy.utils.console import ProgressBar
import os
from astropy import units as u
from astropy import coordinates
from astropy.table import Table, Column
from astropy.nddata.utils import Cutout2D
from astropy import wcs
import numpy as np
from matplotlib import pyplot as plt
from copy import deepcopy
import radio_beam
from utils import rms, plot_grid, mask, grabfileinfo, grabcatname
import regions
import argparse
import warnings
warnings.filterwarnings('ignore')

def reject(imfile, catfile, threshold):
    """Reject noisy detections.
    
    Parameters
    ----------
    imfile : str
        The path to the radio image file
    catfile : str
        The path to the source catalog, as obtained from detect.py
    threshold : float
        The signal-to-noise threshold below which sources are rejected
    """
    # Extract information from filename
    outfile = os.path.basename(catfile).split('cat_')[1].split('.dat')[0]
    region = outfile.split('region')[1].split('_band')[0]
    band = outfile.split('band')[1].split('_val')[0]
    min_value = outfile.split('val')[1].split('_delt')[0]
    min_delta = outfile.split('delt')[1].split('_pix')[0]
    min_npix = outfile.split('pix')[1]
    print("\nSource rejection for region {} in band {}".format(region, band))

    print("Loading image file")
    contfile = fits.open(imfile)
    data = contfile[0].data.squeeze()                   
    mywcs = wcs.WCS(contfile[0].header).celestial
    
    catalog = Table(Table.read(catfile, format='ascii'), masked=True)
    
    beam = radio_beam.Beam.from_fits_header(contfile[0].header)
    pixel_scale = np.abs(mywcs.pixel_scale_matrix.diagonal().prod())**0.5 * u.deg
    ppbeam = (beam.sr/(pixel_scale**2)).decompose().value
    
    data = data/ppbeam
    
    # Remove existing region files
    if os.path.isfile('./reg/reg_'+outfile+'_annulus.reg'):
        os.remove('./reg/reg_'+outfile+'_annulus.reg')
    if os.path.isfile('./reg/reg_'+outfile+'_filtered.reg'):
        os.remove('./reg/reg_'+outfile+'_filtered.reg')
    
    # Load in manually accepted and rejected sources
    override_accepted = []
    override_rejected = []
    if os.path.isfile('./.override/accept_'+outfile+'.txt'):
        override_accepted = np.loadtxt('./.override/accept_'+outfile+'.txt').astype('int')
    if os.path.isfile('./.override/reject_'+outfile+'.txt'):
        override_rejected = np.loadtxt('./.override/reject_'+outfile+'.txt').astype('int')
    print("\nManually accepted sources: ", set(override_accepted))
    print("Manually rejected sources: ", set(override_rejected))
    
    print('\nCalculating RMS values within aperture annuli')
    pb = ProgressBar(len(catalog))
    
    data_cube = []
    masks = []
    rejects = []
    snr_vals = []
    mean_backgrounds = []
    
    for i in range(len(catalog)):
        x_cen = catalog['x_cen'][i] * u.deg
        y_cen = catalog['y_cen'][i] * u.deg
        major_fwhm = catalog['major_fwhm'][i] * u.deg
        minor_fwhm = catalog['minor_fwhm'][i] * u.deg
        position_angle = catalog['position_angle'][i] * u.deg
        dend_flux = catalog['dend_flux_band{}'.format(band)][i]
        
        annulus_width = 1e-5*u.deg
        center_distance = 1e-5*u.deg
        
        # Define some ellipse properties in pixel coordinates
        position = coordinates.SkyCoord(x_cen, y_cen, frame='icrs', unit=(u.deg,u.deg))
        pix_position = np.array(position.to_pixel(mywcs))
        pix_major_fwhm = major_fwhm/pixel_scale
        pix_minor_fwhm = minor_fwhm/pixel_scale
        
        # Cutout section of the image we care about, to speed up computation time
        size = (center_distance+annulus_width+major_fwhm)*2.2
        cutout = Cutout2D(data, position, size, mywcs, mode='partial')
        cutout_center = regions.PixCoord(cutout.center_cutout[0], cutout.center_cutout[1])
        
        # Define the aperture regions needed for SNR
        ellipse_reg = regions.EllipsePixelRegion(cutout_center, pix_major_fwhm*2., pix_minor_fwhm*2., angle=position_angle) # Make sure you're running the dev version of regions, otherwise the position angles will be in radians!
        
        innerann_reg = regions.CirclePixelRegion(cutout_center, center_distance/pixel_scale+pix_major_fwhm)
        outerann_reg = regions.CirclePixelRegion(cutout_center, center_distance/pixel_scale+pix_major_fwhm+annulus_width/pixel_scale)
        
        # Make masks from aperture regions
        ellipse_mask = mask(ellipse_reg, cutout)
        annulus_mask = mask(outerann_reg, cutout) - mask(innerann_reg, cutout)
        
        # Plot annulus and ellipse regions
        data_cube.append(cutout.data)
        masks.append([annulus_mask, ellipse_mask])
        
        # Calculate the SNR and aperture flux sums
        bg_rms = rms(cutout.data[annulus_mask.astype('bool')])
        peak_flux = np.max(cutout.data[ellipse_mask.astype('bool')])
        flux_rms_ratio = peak_flux / bg_rms
        snr_vals.append(flux_rms_ratio)
        
        # Reject bad sources below some SNR threshold
        rejected = False
        if flux_rms_ratio <= threshold:
            rejected = True
        
        # Process manual overrides
        if catalog['_idx'][i] in override_accepted:
            rejected = False
        if catalog['_idx'][i] in override_rejected:
            rejected = True
        rejects.append(int(rejected))
        
        # Add non-rejected source ellipses to a new region file
        fname = './reg/reg_'+outfile+'_filtered.reg'
        with open(fname, 'a') as fh:
            if os.stat(fname).st_size == 0:
                fh.write("icrs\n")
            if not rejected:
                fh.write("ellipse({}, {}, {}, {}, {}) # text={{{}}}\n".format(x_cen.value, y_cen.value, major_fwhm.value, minor_fwhm.value, position_angle.value, i))
        pb.update()
    
    # Plot the grid of sources
    plot_grid(data_cube, masks, rejects, snr_vals, catalog['_idx'])
    plt.suptitle('region={}, band={}, min_value={}, min_delta={}, min_npix={}, threshold={:.4f}'.format(region, band, min_value, min_delta, min_npix, threshold))  
    plt.show(block=False)
    
    # Get overrides from user
    print('Manual overrides example: type "r319, a605" to manually reject source #319 and accept source #605.')
    overrides = input("\nType manual override list, or press enter to continue:\n").split(', ')
    accepted_list = [s[1:] for s in list(filter(lambda x: x.startswith('a'), overrides))]
    rejected_list = [s[1:] for s in list(filter(lambda x: x.startswith('r'), overrides))]
    
    # Save the manually accepted and rejected sources
    fname = './.override/accept_'+outfile+'.txt'
    with open(fname, 'a') as fh:
        for num in accepted_list:
            fh.write('\n'+str(num))
    fname = './.override/reject_'+outfile+'.txt'
    with open(fname, 'a') as fh:
        for num in rejected_list:
            fh.write('\n'+str(num))
    print("Manual overrides written to './.override/' and saved to source catalog. New overrides will be displayed the next time the rejection script is run.")
    
    # Process the new overrides, to be saved into the catalog
    rejects = np.array(rejects)
    acc = np.array([a[-2:] for a in accepted_list], dtype=int)
    rej = np.array([r[-2:] for r in rejected_list], dtype=int)
    rejects[acc] = 0
    rejects[rej] = 1

    # Save the catalog with new columns for SNR
    catalog.add_column(Column(snr_vals), name='snr_band'+band)
    catalog.add_column(np.invert(catalog.mask['snr_band'+band]).astype(int), name='detected_band'+band)
    catalog.add_column(Column(rejects), name='rejected')
    catalog.write('./cat/cat_'+outfile+'_filtered.dat', format='ascii')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Reject sources below some SNR threshold')
    parser.add_argument('region', metavar='region', type=str, help='name of the region as listed in "imgfileinfo.dat"')
    parser.add_argument('band', metavar='band', type=int, help='integer representing the ALMA band of observation')
    args = parser.parse_args()
    region = str(args.region)
    band = args.band

    imfile = grabfileinfo(region, band)[0]
    catfile = grabcatname(region, band)
    reject(imfile, catfile, 6.)

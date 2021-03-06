## To Do
 - [X] Write code to generate a DS9 region file from a fits file, using dendrograms
 - [X] Iterate through different min_value, min_delta, min_npix settings to find best/cleanest source extraction parameters
 - [X] Define annulus regions around sources, calculate pixel RMS within those regions
 - [X] Compare annulus RMS with peak flux in the center
 - [X] Reject bad sources, create new region file with only good ones
 - [X] Constrain source detection to only dendrogram leaves
 - [X] Use dendrogram catalog instead of region file for data handling between scripts
 - [X] Multiply ellipse dimensions by 2.35 to convert to FWHM instead of sigma
 - [X] Add columns to dendrogram catalog for circular aperture sum, dendrogram contour sum
 - [X] Add ability to manually accept and reject sources
 - [X] Use astropy regions to create elliptical apertures / masks
 - [X] Take union of detected sources between images to create source IDs and master catalog, so that flux measurements can be made consistently across bands
    - [X] Common bounding ellipse properties
    - [X] Dendrogram fluxes in each band (when available, empty if not)
    - [X] Peak fluxes in each band
    - [X] Mean background in annulus in each band
 - [X] Rework how image files are read in, for easier switching between bands and regions
 - [X] Enable argument parsing
 - [X] Use master catalog to photometer sources in all bands, adding new columns to the master catalog for each type of aperture and each band
    - Common bounding ellipse, fixed radius circles of several radii
    - Noise level aperture sum for non-detections, to set an upper constraint
 - [X] Make flux v. flux plots with spectral index lines
     - [X] Include error bars
     - [X] Log scale
 - [X] Incorporate 'rejected' and 'accepted' as columns in the source catalog, so that sources can be rejected at any point in the procedure
 - [X] Reject sources that have negative aperture sums
 - [X] Use final master catalog to create flux histograms
 - [ ] Rewrite as an object-oriented Astropy package
 - [ ] Improve detection / rejection algorithms to reduce number of high-eccentricity ellipses
 - [ ] Add centroiding, to ensure circular apertures are centered on the source
 - [ ] Repeat analysis on W51IRS2, AKA W51n


## Bugs
 - SNR for noise is higher than actual sources
     - [SOLVED] When finding the peak flux, the whole image was being searched as opposed to the cutout region. Still, the image mask should have restricted those values anyway, so this might need some more looking into.
 - Lots of overlapping dendrogram regions (maybe this is ok?)
     - [SOLVED] Use only dendrogram leaves, not branches or trunks.
 - Aperture sum for circular apertures is a factor of 100x larger than for dendrogram contour apertures
     - [SOLVED] Units were in Jy/Beam instead of Jy. Divided by ppbeam factor of 101.72 to correct.
 - sourcematch.py crashes due to an indexing error on i=26, as a result of trying to take the average of x center values between the test star and the match
    - [SOLVED] The matched star's table data was being erased when trying to delete the matched star's row in the stacked table, so the program was trying to take an average using an empty table. Solved using deepcopy.
    - It reported an indexing error because the matched star is the last entry in the stacked column. Maybe in other cases where this happened, the iterator was taking the next row in front of the missing data?
- Convolution for nearly identical ellipses returns a larger ellipse with position angle 0
    - [AVOIDED] Convolution sucks anyway.
- Trying to find where both "detected_bandX" fields are true returns all the rows of the master catalog.
    - [SOLVED] The "detected_bandX" columns are now binary (0 or 1) instead of boolean (True or False). The astropy table was storing the boolean as a string ('True' or 'Fals'), so that if you say `np.where(table['detected_bandX'])`, it would find data in every field since they're all strings, and return everywhere.
- Values for alpha calculated from fluxes/nus don't match up with values of alpha indicated by where the data fall on the flux/flux plot
    - [SOLVED] Spectral index equation was wrong. New equation: `alpha = np.log(f1/f2)/np.log(nu1/nu2)`

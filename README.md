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
 - [ ] Take union of detected sources between images to create source IDs and master catalog, so that flux measurements can be made consistently across bands
    - Convolved ellipse properties
    - Dendrogram fluxes in each band (when available, empty if not)
 - [ ] Use master catalog to photometer sources in all bands, adding new columns to the master catalog for each type of aperture and each band
    - Convolved ellipse, averaged ellipse, fixed radius circle (of several radii)
    - Noise level aperture sum for non-detections, to set an upper constraint (flagged?)
    - Mean background flux (from annular regions) instead of background subtraction
 - [ ] Use final master catalog to create flux histograms
 - [ ] Repeat analysis on W51IRS2, AKA W51n

## Bugs
 - SNR for noise is higher than actual sources
     - [SOLVED] When finding the peak flux, the whole image was being searched as opposed to the cutout region. Still, the image mask should have restricted those values anyway, so this might need some more looking into.
 - Lots of overlapping dendrogram regions (maybe this is ok?)
     - [SOLVED] Use only dendrogram leaves, not branches or trunks.
 - Aperture sum for circular apertures is a factor of 100x larger than for dendrogram contour apertures
     - [SOLVED] Units were in Jy/Beam instead of Jy. Divided by ppbeam factor of 101.72 to correct.

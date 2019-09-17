#!/usr/bin/env python

import numpy as np
import pandas as pd
import nibabel as nib
from nibabel.processing import resample_from_to

import os
import warnings

NETWORK_MAPPING = {
    1: "VisCent",
    2: "VisPeri",
    3: "SomMotA",
    4: "SomMotB",
    5: "DorsAttnA",
    6: "DorsAttnB",
    7: "SalVentAttnA",
    8: "SalVentAttnB",
    9: "LimbicA",
    10: "LimbicB",
    11: "ContC",
    12: "ContA",
    13: "ContB",
    14: "TempPar",
    15: "DefaultC",
    16: "DefaultA",
    17: "DefaultB",
}


def merge_atlases(atlases, voxel_reference=None, tsv=None, names=None):
    """
    This code merges the schaefer atlases together, so I have access to
    the cortical, subcortical, and cerebellar components

    Parameters
    ----------

    atlases : list
        list of atlases to merge together (first one being the base)
    voxel_reference : str
        the nifti file with the voxel dimensions wanted for output
    tsv : str or None
        tsv file that has the columns "regions" and "index"
    names : list or None
        list of names to append to the Network Mappings to know
        where the regions are coming from (e.g. subcortical or cerebellar)
    """
    if len(atlases) == 1:
        warnings.warn("only one atlas, returning original atlas")
        return atlases[0]

    # load and resample the base atlas if necessary
    base_atlas_img = nib.load(atlases[0])
    if voxel_reference:
        base_atlas_img = resample_from_to(
            base_atlas_img, nib.load(voxel_reference), order=0, mode='nearest')

    # generate names from filenames if not passed in
    # (only makes a difference if tsv is used)
    if not names:
        names = [os.path.basename(atlas).split('.')[0]
                 for atlas in atlases[1:]]

    # to collect all the tsv information at the end of atlas iteration
    if tsv:
        lut = pd.read_csv(tsv, sep='\t')
        df_collector = [lut]

    # the atlas should be integers (one region: one number)
    base_atlas_data = base_atlas_img.get_data().astype(int)

    # tracking the highest index so numbers do not overlap in the final atlas
    max_idx = base_atlas_data.max()

    # keeping track of the final atlas structure
    built_atlas_data = base_atlas_data
    # iterate over the names and atlases
    for name, atlas in zip(names, atlases[1:]):
        # had to squeeze in case image is fuax 4d (e.g. (x,y,z,1))
        atlas_img = nib.funcs.squeeze_image(nib.load(atlas))

        # the order is 0 splines so that nearest neighbors keeps integers
        # (I don't want any fancy processing for edges to bleed values)
        if not np.array_equal(atlas_img.affine, base_atlas_img.affine):
            atlas_img = resample_from_to(
                atlas_img, base_atlas_img, order=0, mode='nearest')

        # atlases should be treated as integers (not floats)
        atlas_data = atlas_img.get_data().astype(int)

        # make boolean masks to uniquely identify atlas voxels
        atlas_mask = atlas_data > 0
        built_atlas_mask = built_atlas_data > 0

        # clip off any voxels that are already a part of the built atlas
        atlas_mask_uniq = np.logical_xor(atlas_mask,
                                         (atlas_mask & built_atlas_mask))

        # see what schaefer networks are missing in the atlas
        atlas_idxs = set(np.unique(atlas_data[atlas_mask_uniq]))
        network_idxs = set(NETWORK_MAPPING.keys())
        missing_idxs = network_idxs - atlas_idxs

        # print out the missing networks
        missing_networks = [NETWORK_MAPPING[net] for net in missing_idxs]
        warnings.warn(
            'Missing from atlas {file}:'.format(file=atlas) +
            ' '.join(missing_networks))

        # add the max value from the current built
        # atlas so there is no overlap
        atlas_data[atlas_mask_uniq] += max_idx

        # add the current atlas data to the built atlas
        built_atlas_data[atlas_mask_uniq] += atlas_data[atlas_mask_uniq]

        # add new entries to the tsv
        if tsv:
            entries = [('-'.join([name, net]), num + max_idx)
                       for num, net in NETWORK_MAPPING.items()
                       if num in atlas_idxs]
            df_collector.append(
            pd.DataFrame.from_records(
                entries, columns=['regions', 'index']))
        
        # get the new max of the built atlas
        max_idx = built_atlas_data.max()

    # after all dataframes are processed, merge them all together
    # and write out a file.
    if tsv:
        out_lut = pd.concat(df_collector, ignore_index=True)
        out_lut.to_csv('lut.tsv', sep='\t', index=False)

    # write out the built atlas with all the pieces.
    out = 'mergedAtlas.nii.gz'
    base_atlas_img.__class__(built_atlas_data,
                             base_atlas_img.affine,
                             base_atlas_img.header).to_filename(out)


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description='merge_atlases.py: merge schaefer atlases')
    parser.add_argument('-a', '--atlases', action='store', nargs='+')
    parser.add_argument('-r', '--reference', action='store')
    parser.add_argument('-t', '--tsv', action='store')
    parser.add_argument('-n', '--names', action='store', nargs='+')

    opts = parser.parse_args()
    merge_atlases(opts.atlases,
                  voxel_reference=opts.reference,
                  tsv=opts.tsv,
                  names=opts.names)


if __name__ == "__main__":
    main()

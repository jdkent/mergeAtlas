# Quickstart

## Create Environment
`conda env create -f atlas_env_simple.yml`

## Call File

```bash
merge_atlases.py: merge schaefer atlases

optional arguments:
  -h, --help            show this help message and exit
  -a ATLASES [ATLASES ...], --atlases ATLASES [ATLASES ...]
  -r REFERENCE, --reference REFERENCE
  -t TSV, --tsv TSV
  -n NAMES [NAMES ...], --names NAMES [NAMES ...]
```

## Example Usage

```
./merge_atlas.py \
-a Schaefer2018_400Parcels_17Networks_order_FSLMNI152_2mm.nii.gz \
   Choi2012_17Networks_MNI152_FreeSurferConformed2mm_TightMask.nii.gz \
   Buckner2011_17Networks_MNI152_FreeSurferConformed1mm_TightMask.nii.gz \
   -r ../combined_atlas_3mm.nii.gz \
   -t ../../schaefer_parcel-400_network-17.tsv \
   -n Striatal Cerebellar
```

Note: `-r` sets the voxel size of the output atlas.
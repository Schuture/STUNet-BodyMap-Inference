# STUNet-BodyMap-Inference
Use STUNet fine-tuned on DAP Atlas to inference BodyMap CT samples and get the masks.

### 1. Getting Started

#### 1.1 Installing STU-Net

Install STU-Net using the [link](https://github.com/uni-medical/STU-Net). 

#### 1.2 Downloading pre-trained weights

We use DAP Atlas (144) classes to fine-tune STU-Net pre-trained on TotalSegmentator for 500 epochs. Download the weights (Task102_DAP_Atlas.zip), unzip it to your nnUNet result directory (e.g., .../nnU-Net/nnUNet_results/nnUNet/3d_fullres/).

#### 1.3 Preparing data

Please ensure your original data directory seems like this:

```
- Your_BodyMap_Dir/
  - BDMAP_00000001/
    - segmentations/
    - ct.nii.gz
  - BDMAP_00000002/
    - segmentations/
    - ct.nii.gz
  - BDMAP_00000003/
    - segmentations/
    - ct.nii.gz
  - ...
```

**1.3.1** We use a bash script to convert the original directory to target directory. Caution: To save your disk space, we only create soft links.

```
#!/bin/bash

# original
src_dir="Your_BodyMap_Dir/"  # replace this
# target
target_dir=".../BodyMap/STUNet_inference_data/"  # replace this as you want

# create target dir
mkdir -p "$target_dir"

# traverse all subdirs in original data dir
for subdir in "$src_dir"*/
do
    # name of the subdir
    dir_name=$(basename "$subdir")
    # name of the new ct file
    new_filename="${dir_name}_0000.nii.gz"
    # original file path
    src_file="${subdir}ct.nii.gz"
    # target file path
    target_file="${target_dir}${new_filename}"

    # create soft link
    ln -s "$src_file" "$target_file"
done
```

After running the code, you have the following target directory:

```
- Your_Target_Dir/
  - BDMAP_00000001_0000.nii.gz
  - BDMAP_00000001_0000.nii.gz
  - BDMAP_00000001_0000.nii.gz
  - ...
```

**1.3.2** We split the data into slices in order to run the '''all_in_gpu''' mode. First, modify the "input_dir" to your dir for converted data and "output_dir" to a new target dir. And then run 

```
python split_niigz_slices.py
```

After running the code, you have the following directory for sliced CT samples:

```
- Your_New_Target_Dir/
  - BDMAP_00000001_slice_1_0000.nii.gz
  - BDMAP_00000001_slice_2_0000.nii.gz
  - BDMAP_00000001_slice_3_0000.nii.gz
  - ...
```

### 2. Inference with STUNet

#### 2.1 Inference

To conduct inference, you can use following command:

```
nnUNet_predict -i [Your_New_Target_Dir] -o [Your_Sliced_Mask_Dir] -t 102 -m 3d_fullres -f 0 -tr STUNetTrainer_large_ft -chk model_ep_500 --step_size 0.9 --disable_tta --mode fast --all_in_gpu True
```

#### 2.2 Merge

We need to merge the sliced masks to the original size of the CT scans. First, modify the "input_dir" to your \[Your_Sliced_Mask_Dir\] and "output_dir" to a new mask dir. And then run 

```
python merge_niigz_slices.py
```

Then the new mask dir would be like

```
- Your_New_Mask_Dir/
  - BDMAP_00000001.nii.gz
  - BDMAP_00000002.nii.gz
  - BDMAP_00000003.nii.gz
  - ...
```

































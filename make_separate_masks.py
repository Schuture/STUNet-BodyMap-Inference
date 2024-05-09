import os
import SimpleITK as sitk
import pandas as pd

# 文件路径
input_dir = "/data2/yixiong/BodyMap/HGFC_inference_merged_data"
output_dir = "/data2/yixiong/BodyMap/HGFC_inference_separate_data"
label_csv = "/data2/yixiong/BodyMap/BodyMap_label_name.csv"

# 读取标签名
label_names = pd.read_csv(label_csv)


def merge_masks_and_save(masks, output_file):
    # Initialize the output mask as zeros with the same shape as the first input mask
    merged_image = sitk.ReadImage(masks[0])
    merged_array = sitk.GetArrayFromImage(merged_image)
    merged_array = (merged_array > 0).astype('uint8')  # Ensure binary mask

    # Read and combine all other masks
    for mask in masks[1:]:
        mask_image = sitk.ReadImage(mask)
        mask_array = sitk.GetArrayFromImage(mask_image)
        merged_array |= (mask_array > 0).astype('uint8')  # Combine using OR operation

    # Convert the merged array back to SimpleITK image
    merged_image = sitk.GetImageFromArray(merged_array)
    merged_image.CopyInformation(sitk.ReadImage(masks[0]))
    
    # Save the merged image
    sitk.WriteImage(merged_image, output_file)
    print(f'Merged and saved to: {output_file}')


def process_files(input_dir, output_dir, label_names):
    filenames = sorted(os.listdir(input_dir))
    for idx, filename in enumerate(filenames):
        if not 0 < (idx+1) <= 2500:
            continue
        if filename.endswith(".nii.gz"):
            print(f'processing [{idx+1}/{len(filenames)}] file: {filename}')
            file_path = os.path.join(input_dir, filename)
            base_name = filename[:-7]  # 移除 .nii.gz

            # 读取NIFTI文件
            img = sitk.ReadImage(file_path)

            # 创建目标文件夹
            base_output_dir = os.path.join(output_dir, base_name)
            segmentations_dir = os.path.join(base_output_dir, "segmentations")
            os.makedirs(segmentations_dir, exist_ok=True)

            # 处理并保存每个标签
            for index, row in label_names.iterrows():
                label_image = sitk.BinaryThreshold(img, lowerThreshold=row['Label'], upperThreshold=row['Label'], insideValue=1, outsideValue=0)
                label_image_uint8 = sitk.Cast(label_image, sitk.sitkUInt8)  # 转换为uint8
                output_file_path = os.path.join(segmentations_dir, f"{row['Name']}.nii.gz")
                sitk.WriteImage(label_image_uint8, output_file_path)

            # 复制原始文件到新位置并重命名
            combined_labels_path = os.path.join(base_output_dir, "combined_labels.nii.gz")
            sitk.WriteImage(img, combined_labels_path)

            # 合并lung的标签
            left_masks = [
                os.path.join(segmentations_dir, 'lung_lower_lobe_left.nii.gz'),
                os.path.join(segmentations_dir, 'lung_upper_lobe_left.nii.gz')
            ]
            if all(os.path.isfile(mask) for mask in left_masks):
                merge_masks_and_save(left_masks, os.path.join(segmentations_dir, 'lung_left.nii.gz'))
            right_masks = [
                os.path.join(segmentations_dir, 'lung_lower_lobe_right.nii.gz'),
                os.path.join(segmentations_dir, 'lung_middle_lobe_right.nii.gz'),
                os.path.join(segmentations_dir, 'lung_upper_lobe_right.nii.gz')
            ]
            if all(os.path.isfile(mask) for mask in right_masks):
                merge_masks_and_save(right_masks, os.path.join(segmentations_dir, 'lung_right.nii.gz'))

# 运行脚本
process_files(input_dir, output_dir, label_names)

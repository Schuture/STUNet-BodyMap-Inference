'''
将数据集中的样本逐一切片并另存到另一个目录中
经过实验，50个patch会占30GB显存（all in gpu模式）
因此切片的高度为两层patch，一层5x5的大小
'''
import SimpleITK as sitk
import nibabel as nib
import numpy as np
import os

# 输入和输出的目录
input_dir = "/data2/yixiong/BodyMap/STUNet_inference_data"
output_dir = "/data2/yixiong/BodyMap/STUNet_inference_sliced_data"

def adjust_axes_and_spacing(image):
    # 假设原始顺序是 XYZ，需要调整为 ZYX
    new_order = [2, 1, 0]  # 这里的数字代表原始轴的索引
    permuted_image = sitk.PermuteAxes(image, new_order)
    
    # 调整 spacing，假设原始spacing也需要调整
    original_spacing = image.GetSpacing()
    new_spacing = [original_spacing[i] for i in new_order]
    permuted_image.SetSpacing(new_spacing)
    
    return permuted_image

def cal_n(height, overlap, min_slice_height, max_slice_height):
    '''
    找到切分的最少片数，以及对应每一片的高度（已经取整）
    '''
    if height <= min_slice_height:  # 如果z轴太短，只切一片
        return 1, height
    for n in range(1, 100):
        slice_height = (height + (n-1)*overlap) / n
        if min_slice_height <= slice_height <= max_slice_height:
            return n, int(slice_height)
    return None  # 如果无法找到合适的切片方案，则返回None

def split_and_save_slices(file_path, output_dir):
    try:
        # 尝试使用SimpleITK
        img = sitk.ReadImage(file_path)
        spacing = img.GetSpacing()
        # 纠错：第一个维度同时小于/大于后两个维度（后两个维度都是512），将 zyx => xyz
        if (spacing[0] - spacing[1]) * (spacing[0] - spacing[2]) > 0.01:
            print('***Caution: zyx => xyz')
            img = adjust_axes_and_spacing(img)
            spacing = img.GetSpacing()
        array = sitk.GetArrayFromImage(img)
        z_size = img.GetDepth()
    except Exception as e:
        # 如果SimpleITK失败，尝试使用nibabel
        print(f"SimpleITK failed with error {e}, switching to nibabel.")
        nib_img = nib.load(file_path)
        array = nib_img.get_fdata()
        array = np.swapaxes(array, 0, 2)  # 交换轴以匹配SimpleITK的z, y, x顺序
        z_size = array.shape[0]  # 更新z_size为数组的第一个维度
        spacing = nib_img.header.get_zooms()

    # 切片参数
    overlap = 40
    min_slice_height = 80 * 2.5 / spacing[2]  # 模型训练时是2.5，但是有的推理样本间距特别小，例如0.7
    max_slice_height = 145 * 2.5 / spacing[2]

    # 使用cal_n函数确定最佳切片数和高度
    result = cal_n(z_size, overlap, min_slice_height, max_slice_height)
    if result is None:
        print(f"无法为 {file_path} 找到合适的切片方案。")
        return
    num_slices, slice_height = result
    
    print(f'z_size: {z_size}, spacing: {spacing}, num_slices: {num_slices}, slice_height: {slice_height}')

    # 开始切片
    start_z = 0
    for slice_index in range(1, num_slices + 1):
        # 对最后一个切片直接使用图像高度, 注意正确的切片维度顺序
        end_z = start_z + slice_height - 1 if slice_index < num_slices else z_size - 1
        # 纠错：后两个维度都是512，出现于sitk导入了特殊样本，此时spacing都正常
        if array.shape[1] == 512 and array.shape[2] == 512:
            slice_array = array[start_z:end_z + 1, :, :]  # z轴在第一个维度
        else:
            slice_array = array[:, :, start_z:end_z + 1]
        print(f'slice_array.shape: {slice_array.shape}, start_z: {start_z}, end_z: {end_z}')

        # 文件名和路径
        original_filename = os.path.basename(file_path)
        new_filename = original_filename.replace("_0000.nii.gz", f"_slice_{slice_index}_0000.nii.gz")
        output_filepath = os.path.join(output_dir, new_filename)

        # 统一使用sitk库保存图像切片
        slice_img = sitk.GetImageFromArray(slice_array)
        slice_img.SetSpacing((float(spacing[0]), float(spacing[1]), float(spacing[2])))
        sitk.WriteImage(slice_img, output_filepath)

        # 更新start_z为下一个切片的开始
        start_z = end_z - overlap + 1

# 遍历目录中的所有.nii.gz文件
for i, filename in enumerate(sorted(os.listdir(input_dir))):
    if filename.endswith(".nii.gz"):
        file_path = os.path.join(input_dir, filename)
        split_and_save_slices(file_path, output_dir)
        print(f'[{i+1}/{len(os.listdir(input_dir))}] {file_path}切片已保存')

print("切片处理和保存完成。")

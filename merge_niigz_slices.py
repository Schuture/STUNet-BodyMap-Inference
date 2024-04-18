import SimpleITK as sitk
import os
import re
from collections import defaultdict

# 输入和输出的目录
input_dir = "/data2/yixiong/BodyMap/STUNet_inference_sliced_results/"
output_dir = "/data2/yixiong/BodyMap/STUNet_inference_results/"

def merge_slices(slice_dict):
    for original_ct, slices in list(slice_dict.items()):
        # 根据切片序号对切片进行排序
        sorted_slices = sorted(slices, key=lambda x: int(re.search(r"_slice_(\d+)", x).group(1)))
        full_image = None
        
        # 合并切片
        for i, slice_file in enumerate(sorted_slices):
            img = sitk.ReadImage(slice_file)
            if full_image is None:
                # 创建一个空的图像，用于合并所有切片
                full_size = list(img.GetSize())
                # 调整计算方式，仅在中间切片减少重叠部分
                full_size[2] = sum([sitk.ReadImage(s).GetDepth() for s in sorted_slices]) - 40 * (len(sorted_slices) - 1)
                print('图像全尺寸', full_size)
                full_image = sitk.Image(full_size, img.GetPixelID())
                
                # 手动设置空间定位信息
                full_image.SetOrigin(img.GetOrigin())
                full_image.SetSpacing(img.GetSpacing())
                full_image.SetDirection(img.GetDirection())
                current_slice = 0

            # 设置提取区域
            start_z = 20 if i > 0 else 0  # 第一个切片不去掉开头
            end_z = img.GetDepth() - (20 if i < len(sorted_slices) - 1 else 0)  # 最后一个切片不去掉结尾
            extractor = sitk.RegionOfInterestImageFilter()
            extractor.SetSize([full_size[0], full_size[1], end_z - start_z])
            extractor.SetIndex([0, 0, start_z])
            img_cropped = extractor.Execute(img)

            # 复制当前切片到全图像中
            full_image = sitk.Paste(full_image, img_cropped, img_cropped.GetSize(), destinationIndex=[0, 0, current_slice])
            current_slice += img_cropped.GetSize()[2]  # 更新当前Z轴的索引

        # 保存合并后的图像
        output_filename = os.path.join(output_dir, original_ct + ".nii.gz")
        sitk.WriteImage(full_image, output_filename)
        print('已保存', output_filename)

# 读取所有文件，并按原始 CT 图像进行分类
slice_dict = defaultdict(list)
for idx, filename in enumerate(sorted(os.listdir(input_dir))):
    if filename.endswith(".nii.gz"):
        #match = re.match(r"(AutoPET_[\da-f]+_\d+)_slice_\d+", filename)
        match = re.match(r"(BDMAP_\d+)_slice_\d+\.nii\.gz", filename)
        if match:
            original_ct = match.group(1)  # CT名
            slice_dict[original_ct].append(os.path.join(input_dir, filename))

# 合并每个原始 CT 的所有切片
print(f"共{len(list(slice_dict.items()))}样本需要合并。")
merge_slices(slice_dict)

print("所有CT mask切片合并完成。")

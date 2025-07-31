import os
import boto3
import requests
from PIL import Image
from io import BytesIO
import concurrent.futures
from tqdm import tqdm
import tempfile
import logging
import glob
import re
import tabulate
import time
from collections import defaultdict
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        print(f"✓ 已加载环境配置文件: {env_file}")
    else:
        print(f"⚠ 未找到 .env 文件: {env_file}")

# Load .env file at startup
load_env_file()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# R2 configuration
R2_ENDPOINT = os.environ.get('R2_ENDPOINT')
R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')
R2_PUBLIC_URL = os.environ.get('R2_PUBLIC_URL', '')

# Compression configuration
MAX_WIDTH = 1200  # Maximum width in pixels
MAX_SIZE_MB = 1  # Maximum file size in MB after compression
PNG_COMPRESSION_LEVEL = 9  # PNG compression level (0-9, 9 being max compression)
JPEG_QUALITY = 85  # JPEG quality (0-100, higher is better quality)
WEBP_QUALITY = 85  # WebP quality (0-100, higher is better quality)
AVIF_QUALITY = 85  # AVIF quality (0-100, higher is better quality)

# Stats tracking
compression_stats = defaultdict(list)

# Supported image formats
SUPPORTED_FORMATS = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
    '.avif': 'image/avif'
}

def create_s3_client():
    """Create and return an S3 client configured for Cloudflare R2."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )

def list_images(prefix, pattern=None):
    """List all images in the specified directory structure.
    
    Args:
        prefix: The directory prefix to search in (e.g., 'uiprompt/themes/')
        pattern: Optional regex pattern for matching specific files. If None, 
                 matches all supported image files in the prefix and subdirectories.
    """
    s3_client = create_s3_client()
    
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=R2_BUCKET_NAME, Prefix=prefix)
    
    # If no pattern is provided, create one based on the prefix and supported formats
    if pattern is None:
        # This matches any file with supported extensions in the prefix and subdirectories
        extensions = '|'.join([ext.replace('.', '\\.') for ext in SUPPORTED_FORMATS.keys()])
        if prefix:
            # For non-empty prefix, match: prefix + any path + supported extension
            pattern = re.compile(f'{re.escape(prefix)}.*({extensions})$', re.IGNORECASE)
        else:
            # For empty prefix, match any file with supported extension
            pattern = re.compile(f'.*({extensions})$', re.IGNORECASE)
    else:
        pattern = re.compile(pattern, re.IGNORECASE)
    
    image_keys = []
    image_sizes = {}
    all_files = []  # 用于调试，存储所有文件
    
    print(f"\n🔍 调试信息: 扫描 R2 存储桶 '{R2_BUCKET_NAME}' 前缀 '{prefix}'")
    print(f"📋 匹配模式: {pattern.pattern}")
    print(f"📁 支持的格式: {list(SUPPORTED_FORMATS.keys())}")
    print("-" * 80)
    
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                size = obj['Size']
                all_files.append((key, size))
                
                if pattern.match(key):
                    image_keys.append(key)
                    image_sizes[key] = size
                    print(f"✅ 匹配: {key} ({size/1024:.1f} KB)")
                else:
                    print(f"❌ 跳过: {key} ({size/1024:.1f} KB)")
    
    print("-" * 80)
    print(f"📊 扫描统计:")
    print(f"   总文件数: {len(all_files)}")
    print(f"   匹配文件数: {len(image_keys)}")
    print(f"   跳过文件数: {len(all_files) - len(image_keys)}")
    
    if not all_files:
        print(f"⚠️  在前缀 '{prefix}' 下未找到任何文件")
        print("💡 建议:")
        print("   1. 检查前缀路径是否正确")
        print("   2. 确认存储桶中有文件")
        print("   3. 尝试使用空前缀 --prefix '' 来列出所有文件")
    elif not image_keys:
        print(f"⚠️  在前缀 '{prefix}' 下找到 {len(all_files)} 个文件，但没有匹配的图片文件")
        print("💡 建议:")
        print("   1. 检查文件扩展名是否在支持列表中")
        print("   2. 尝试使用自定义正则表达式模式 --pattern")
        print("   3. 检查文件路径结构是否符合默认模式")
    
    logger.info(f"Found {len(image_keys)} images matching the pattern in '{prefix}'")
    return image_keys, image_sizes

def get_image_format(key):
    """Get the image format and content type based on file extension."""
    ext = os.path.splitext(key.lower())[1]
    
    if ext in SUPPORTED_FORMATS:
        content_type = SUPPORTED_FORMATS[ext]
        # Convert extension to PIL format name
        if ext == '.jpg' or ext == '.jpeg':
            format_name = 'JPEG'
        elif ext == '.avif':
            format_name = 'AVIF'
        else:
            format_name = ext[1:].upper()
        return format_name, content_type
    
    # Default to PNG if extension not recognized
    return 'PNG', 'image/png'

def download_image(key):
    """Download an image from R2 and return its content."""
    s3_client = create_s3_client()
    
    try:
        response = s3_client.get_object(Bucket=R2_BUCKET_NAME, Key=key)
        return BytesIO(response['Body'].read())
    except Exception as e:
        logger.error(f"Error downloading {key}: {e}")
        return None

def compress_image(image_data, key):
    """Compress the image data and return the compressed image.
    
    All images will be converted to AVIF format for best compression.
    """
    try:
        img = Image.open(image_data)
        
        # Get original format info for logging
        original_ext = os.path.splitext(key.lower())[1]
        print(f"  原始格式: {original_ext} → 目标格式: AVIF")
        
        # Calculate new dimensions maintaining aspect ratio
        orig_width, orig_height = img.size
        if orig_width > MAX_WIDTH:
            ratio = MAX_WIDTH / orig_width
            new_width = MAX_WIDTH
            new_height = int(orig_height * ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            print(f"  调整尺寸: {orig_width}x{orig_height} → {new_width}x{new_height}")
        
        # Prepare compressed image - always use AVIF
        output = BytesIO()
        
        # Convert to AVIF format (supports transparency and excellent compression)
        img.save(output, format='AVIF', quality=AVIF_QUALITY)
        
        # If still too large, reduce quality further
        current_size_mb = output.tell() / (1024 * 1024)
        quality = AVIF_QUALITY
        
        while current_size_mb > MAX_SIZE_MB and quality > 30:
            output = BytesIO()
            quality -= 10
            img.save(output, format='AVIF', quality=quality)
            current_size_mb = output.tell() / (1024 * 1024)
            
        print(f"  最终AVIF质量: {quality}")
        
        output.seek(0)
        return output, 'image/avif'
    except Exception as e:
        logger.error(f"Error compressing {key}: {e}")
        return None, None

def upload_image(image_data, key, content_type):
    """Upload the compressed image back to R2 with .avif extension and optionally delete original."""
    s3_client = create_s3_client()
    
    try:
        # Change file extension to .avif
        base_key = os.path.splitext(key)[0]
        new_key = f"{base_key}.avif"
        
        # Upload the compressed image data
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=new_key,
            Body=image_data.getvalue(),
            ContentType=content_type
        )
        logger.info(f"Uploaded as: {new_key}")
        
        # If the original file has a different extension, ask to delete it
        original_ext = os.path.splitext(key)[1].lower()
        if original_ext != '.avif':
            return True, key  # Return the original key for potential deletion
        else:
            return True, None  # No need to delete if already AVIF
            
    except Exception as e:
        logger.error(f"Error uploading {key}: {e}")
        return False, None

def delete_original_file(key):
    """Delete the original file from R2."""
    s3_client = create_s3_client()
    
    try:
        s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        logger.info(f"Deleted original file: {key}")
        return True
    except Exception as e:
        logger.error(f"Error deleting original file {key}: {e}")
        return False

def process_image(key, original_size=None):
    """Process a single image: download, compress, and upload.
    
    Returns:
        tuple: (success, original_size, compressed_size, compression_ratio, process_time, original_key_to_delete)
    """
    # Start time
    start_time = time.time()
    
    # Download image
    original_data = download_image(key)
    if original_data is None:
        return False, 0, 0, 0, 0, None
    
    # Get original size for comparison
    if original_size is None:
        original_size = original_data.getbuffer().nbytes
    
    # Compress the image
    compressed_data, content_type = compress_image(original_data, key)
    if compressed_data is None:
        return False, original_size, 0, 0, 0, None
    
    compressed_size = compressed_data.getbuffer().nbytes
    compression_ratio = (original_size - compressed_size) / original_size * 100
    process_time = time.time() - start_time
    
    # Only upload if compression achieved meaningful reduction
    if compressed_size < original_size * 0.95:  # At least 5% reduction
        upload_success, original_key_to_delete = upload_image(compressed_data, key, content_type)
        if upload_success:
            logger.info(f"Processed {key}: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({compression_ratio:.1f}% reduction)")
            return True, original_size, compressed_size, compression_ratio, process_time, original_key_to_delete
        else:
            return False, original_size, 0, 0, process_time, None
    else:
        logger.info(f"Skipped {key}: Compression only achieved {compression_ratio:.1f}% reduction")
        return True, original_size, original_size, 0, process_time, None

def display_image_list(image_keys, image_sizes):
    """Display the list of images that will be processed."""
    print("\n将处理以下图片文件:")
    
    # Prepare data for table
    data = []
    total_size = 0
    
    for key in image_keys:
        size = image_sizes.get(key, 0)
        format_name, _ = get_image_format(key)
        
        # Add to table data
        data.append([
            key,
            format_name,
            f"{size/1024:.1f} KB",
            f"{size/(1024*1024):.2f} MB"
        ])
        
        total_size += size
    
    # Add total row
    data.append([
        "总计",
        f"{len(image_keys)} 文件",
        f"{total_size/1024:.1f} KB",
        f"{total_size/(1024*1024):.2f} MB"
    ])
    
    # Print table
    print(tabulate.tabulate(data, headers=["文件路径", "格式", "大小(KB)", "大小(MB)"], tablefmt="grid"))
    
    return total_size

def generate_compression_report(stats):
    """Generate a detailed compression report from stats."""
    print("\n图片压缩结果报告:")
    
    # Prepare data for table
    report_data = []
    
    total_original = 0
    total_compressed = 0
    total_saved = 0
    
    # Format per file stats
    for key, result in stats.items():
        for original, compressed, ratio, time in result:
            saved = original - compressed
            total_original += original
            total_compressed += compressed
            total_saved += saved
            
            report_data.append([
                key,
                f"{original/1024:.1f} KB",
                f"{compressed/1024:.1f} KB", 
                f"{saved/1024:.1f} KB",
                f"{ratio:.1f}%",
                f"{time:.1f}s"
            ])
    
    # Add summary rows
    total_ratio = (total_saved / total_original * 100) if total_original > 0 else 0
    report_data.append([
        "总计",
        f"{total_original/1024:.1f} KB",
        f"{total_compressed/1024:.1f} KB",
        f"{total_saved/1024:.1f} KB",
        f"{total_ratio:.1f}%",
        "-"
    ])
    
    # Format totals in MB for easier reading
    mb_original = total_original / (1024 * 1024)
    mb_compressed = total_compressed / (1024 * 1024)
    mb_saved = total_saved / (1024 * 1024)
    
    report_data.append([
        "总计(MB)",
        f"{mb_original:.2f} MB",
        f"{mb_compressed:.2f} MB",
        f"{mb_saved:.2f} MB",
        f"{total_ratio:.1f}%",
        "-"
    ])
    
    # Print table
    print(tabulate.tabulate(
        report_data, 
        headers=["文件", "原始大小", "压缩后大小", "节省空间", "压缩率", "处理时间"],
        tablefmt="grid"
    ))
    
    # Print summary
    file_count = len(stats)
    print(f"\n共处理 {file_count} 个文件")
    print(f"总节省空间: {mb_saved:.2f} MB")
    print(f"平均压缩率: {total_ratio:.1f}%")

def main(prefix, pattern=None, max_workers=5):
    """Main function to process all images.
    
    Args:
        prefix: The directory prefix to search in
        pattern: Optional regex pattern for file matching
        max_workers: Number of parallel workers
    """
    global compression_stats
    compression_stats = defaultdict(list)
    
    # Validate environment variables
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
        logger.error("Missing required environment variables. Please set R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_BUCKET_NAME.")
        return
    
    # Get list of image keys
    image_keys, image_sizes = list_images(prefix, pattern)
    if not image_keys:
        logger.info(f"No images found matching the criteria in '{prefix}'")
        return
    
    # Display the list of images and get user confirmation
    total_size = display_image_list(image_keys, image_sizes)
    
    # Ask for user confirmation
    confirm = input(f"\n将处理 {len(image_keys)} 个文件，总大小 {total_size/(1024*1024):.2f} MB。确认继续？(y/n): ")
    if confirm.lower() != 'y':
        print("用户取消操作")
        return
    
    # Process images in parallel
    success_count = 0
    error_count = 0
    files_to_delete = []  # 收集需要删除的原始文件
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {
            executor.submit(process_image, key, image_sizes.get(key)): key 
            for key in image_keys
        }
        
        for future in tqdm(concurrent.futures.as_completed(future_to_key), total=len(image_keys), desc="Processing images"):
            key = future_to_key[future]
            try:
                success, original_size, compressed_size, ratio, process_time, original_key_to_delete = future.result()
                
                # Record stats for successful compressions
                if success:
                    success_count += 1
                    if compressed_size > 0:
                        compression_stats[key].append((original_size, compressed_size, ratio, process_time))
                    # 收集需要删除的原始文件
                    if original_key_to_delete:
                        files_to_delete.append(original_key_to_delete)
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Exception processing {key}: {e}")
                error_count += 1
    
    logger.info(f"Processing complete: {success_count} images processed successfully, {error_count} errors")

    # Generate and display compression report
    generate_compression_report(compression_stats)
    
    # Handle deletion of original files
    if files_to_delete:
        print(f"\n🗑️  原始文件清理")
        print(f"以下 {len(files_to_delete)} 个原始文件已被转换为 AVIF 格式，可以删除以节省存储空间:")
        print("-" * 80)
        
        total_original_size = 0
        for file_key in files_to_delete:
            size = image_sizes.get(file_key, 0)
            total_original_size += size
            print(f"  📄 {file_key} ({size/1024:.1f} KB)")
        
        print("-" * 80)
        print(f"💾 总计可节省存储空间: {total_original_size/1024:.1f} KB ({total_original_size/(1024*1024):.2f} MB)")
        
        confirm_delete = input(f"\n❓ 是否删除这些原始文件？(y/n): ")
        if confirm_delete.lower() == 'y':
            deleted_count = 0
            failed_count = 0
            
            print("\n🧹 正在删除原始文件...")
            for file_key in tqdm(files_to_delete, desc="Deleting original files"):
                if delete_original_file(file_key):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            print(f"\n✅ 删除完成: {deleted_count} 个文件删除成功, {failed_count} 个失败")
            if deleted_count > 0:
                print(f"💰 节省存储空间: {total_original_size/(1024*1024):.2f} MB")
        else:
            print("⏭️  跳过删除，原始文件保留")
    else:
        print("\n🎯 所有处理的文件都已经是 AVIF 格式，无需删除原始文件")

if __name__ == "__main__":
    import argparse
    
    # Check if tabulate is installed
    try:
        import tabulate
    except ImportError:
        print("Installing tabulate package...")
        import subprocess
        subprocess.check_call(["pip", "install", "tabulate"])
        import tabulate
    
    parser = argparse.ArgumentParser(description="Download, compress, and re-upload images from Cloudflare R2")
    parser.add_argument("--prefix", type=str, default="uiprompt/themes/", 
                      help="Directory prefix in R2 to process images from (default: uiprompt/themes/)")
    parser.add_argument("--pattern", type=str, default=None, 
                      help="Custom regex pattern for matching files (default: matches [prefix]/*/any_image_file)")
    parser.add_argument("--workers", type=int, default=5, 
                      help="Number of worker threads (default: 5)")
    parser.add_argument("--max-width", type=int, default=1200, 
                      help="Maximum width in pixels (default: 1200)")
    parser.add_argument("--max-size", type=float, default=1.0, 
                      help="Maximum file size in MB (default: 1.0)")
    parser.add_argument("--compression-level", type=int, default=9, 
                      help="PNG compression level (0-9, default: 9)")
    parser.add_argument("--jpeg-quality", type=int, default=85,
                      help="JPEG compression quality (0-100, default: 85)")
    parser.add_argument("--webp-quality", type=int, default=85,
                      help="WebP compression quality (0-100, default: 85)")
    parser.add_argument("--avif-quality", type=int, default=85,
                      help="AVIF compression quality (0-100, default: 85)")
    parser.add_argument("--test", action="store_true", 
                      help="Test mode - list files that would be processed without actually processing them")
    
    args = parser.parse_args()
    
    # Update global configuration
    MAX_WIDTH = args.max_width
    MAX_SIZE_MB = args.max_size
    PNG_COMPRESSION_LEVEL = args.compression_level
    JPEG_QUALITY = args.jpeg_quality
    WEBP_QUALITY = args.webp_quality
    AVIF_QUALITY = args.avif_quality
    
    # Test mode - just list the files that would be processed
    if args.test:
        logger.info("TEST MODE: Listing files that would be processed")
        image_keys, image_sizes = list_images(args.prefix, args.pattern)
        display_image_list(image_keys, image_sizes)
        print("\nTEST MODE: No files were actually processed")
    else:
        # Run the main function
        main(prefix=args.prefix, pattern=args.pattern, max_workers=args.workers) 
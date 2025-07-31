# R2 Image Compression Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文文档](README_CN.md)

A tool for downloading, compressing, and re-uploading images in Cloudflare R2 buckets, supporting various image formats and custom paths.

**This forked version converts all images to AVIF format for optimal compression, instead of keeping the original format. AVIF support is added.**

## Features

- Download images from R2 storage
- Support for multiple input image formats (PNG, JPEG, WebP, GIF, AVIF)
- **All images are converted to AVIF format for best compression**
- Resize large images (maintain aspect ratio)
- AVIF format advantages:
  - 50%+ better compression than JPEG
  - 20%+ better compression than WebP
  - Supports transparency and lossless compression
  - Widely supported by modern browsers
- Upload compressed images back to R2 with .avif extension
- Process multiple images in parallel
- Custom directory prefix and file matching patterns
- Test mode to preview which files will be processed
- Display file list and request user confirmation before processing
- Generate detailed compression report and ask whether to delete original files after processing

## Installation

### Prerequisites

- Python 3.6 or higher
- Cloudflare R2 account with bucket and access credentials

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/zhangchenchen/reduce_cloudfare_image.git
   cd r2-image-compression-tool
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

   Or with Pixi:
   ```bash
   pixi install
   ```

3. Set up environment variables:
   
   **Option 1: Use environment file**
   
   Copy the example environment file and edit it:
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```
   
   **Option 2: Use setup script**
   
   Copy the example setup script and edit it:
   ```bash
   cp set_env.sh.example set_env.sh
   # Edit set_env.sh with your credentials
   chmod +x set_env.sh
   source set_env.sh
   ```

## Usage

```bash
python compress_r2_images.py [options]
```

### Command Line Options

- `--prefix PATH`: Directory prefix in R2 bucket to process (default: "uiprompt/themes/")
- `--pattern REGEX`: Custom regex pattern for matching files (default: matches [prefix]/*/any supported image format)
- `--workers NUMBER`: Number of worker threads for parallel processing (default: 5)
- `--max-width PIXELS`: Maximum width in pixels for resizing (default: 1200)
- `--max-size SIZE_MB`: Target maximum file size in MB (default: 1.0)
- `--avif-quality QUALITY`: AVIF compression quality (0-100, default: 85)
- `--test`: Test mode - only list files that would be processed without actually processing them

### Examples

```bash
# Process all PNG files in the 2025/07/ directory
python compress_r2_images.py --prefix "2025/07/" --pattern ".*\.png$"

# Process PNG and JPG files in the 2025/07/ directory
python compress_r2_images.py --prefix "2025/07/" --pattern ".*\.(png|jpg|jpeg)$"

# Process all supported image formats in the 2025/07/ directory (recommended)
python compress_r2_images.py --prefix "2025/07/"

# Test mode, only show files that would be processed
python compress_r2_images.py --test --prefix "2025/07/" --pattern ".*\.(png|jpg|jpeg)$"

# Process a specific file
python compress_r2_images.py --prefix "2025/07/" --pattern ".*20250719121931679\.png$"

# Use higher AVIF quality (larger file, better quality)
python compress_r2_images.py --prefix "2025/07/" --avif-quality 95

# Use more worker threads for faster processing
python compress_r2_images.py --prefix "2025/07/" --workers 10
```

## Supported Image Formats

The script supports the following **input** image formats:

- **PNG (.png)**: Preserves transparency
- **JPEG (.jpg, .jpeg)**: Standard lossy format
- **WebP (.webp)**: Modern lossy/lossless format
- **GIF (.gif)**: Animated and static images
- **AVIF (.avif)**: Modern high-efficiency format

**All images will be converted to AVIF format for output** for best compression and quality balance.
- **AVIF (.avif)**: High-efficiency format, supports transparency (requires AVIF codec support)

## How It Works

1. List all image files matching the pattern under the specified prefix in the R2 bucket
2. Display file list and request user confirmation
3. Download each image
4. Resize the image if its width exceeds the maximum width
5. **Convert all images to AVIF format**, applying quality optimization:
   - Start with configurable quality (default 85)
   - If file is still too large, gradually reduce quality until it meets the size requirement
   - Preserve transparency
6. Upload the compressed image back to R2 with .avif extension
7. Only upload when at least 5% size reduction is achieved
8. Generate detailed compression report
9. Ask whether to delete the original files after processing

## Notes

- Execution time depends on the number of images, sizes, and network speed
- Processing progress is displayed via progress bar and log messages
- Test mode helps you preview the files that will be processed before actual processing
- Some already optimized images may not be further compressed

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
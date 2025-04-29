# Contributing to R2 Image Compression Tool

Thank you for considering contributing to the R2 Image Compression Tool! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. Harassment or abusive behavior will not be tolerated.

## How to Contribute

There are several ways you can contribute to this project:

1. **Bug Reports**: Report bugs by creating an issue in the issue tracker.
2. **Feature Requests**: Suggest new features or improvements.
3. **Documentation**: Help improve the documentation.
4. **Code Contributions**: Submit pull requests with bug fixes or new features.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/R2-Image-Compression-Tool.git`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `env.example` to `.env` and set your Cloudflare R2 credentials
5. Run the script in test mode to ensure everything works: `python compress_r2_images.py --test`

## Pull Request Process

1. Create a new branch for your feature or bug fix: `git checkout -b feature/your-feature-name` or `git checkout -b fix/your-bug-fix`
2. Make your changes and commit them with descriptive commit messages
3. Push your branch to your fork: `git push origin feature/your-feature-name`
4. Create a pull request against the main repository's main branch
5. Ensure your code follows the project's coding standards
6. Update documentation as needed

## Code Style Guidelines

- Follow PEP 8 style guidelines for Python code
- Write descriptive comments
- Add docstrings to functions and classes
- Use meaningful variable names

## Testing

- Add tests for new features
- Ensure existing tests pass before submitting a pull request
- Run tests with pytest

## Documentation

When adding new features or making changes, please update the relevant documentation, including:

- Code comments and docstrings
- README.md
- Other documentation files as needed

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 
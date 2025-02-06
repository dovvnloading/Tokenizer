# Tokenz Machine

A modern, intuitive desktop application for text tokenization visualization and analysis, built with PyQt5 and Hugging Face transformers.

![MIT License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/python-v3.6+-blue.svg)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)

----

![Screenshot 2025-02-06 073749](https://github.com/user-attachments/assets/8cb18349-ac6e-4699-8620-a8265069b114)



## Overview

Tokenz Machine is a powerful desktop application designed to help developers, researchers, and language enthusiasts understand and visualize how different transformer models tokenize text. The application provides real-time token visualization, with support for multiple popular transformer models including GPT-2, BERT, RoBERTa, T5, and DistilBERT.

## Features

- **Real-time Tokenization**: Instantly see how your text is broken down into tokens
- **Multiple Model Support**: Switch between different transformer models (GPT-2, BERT, RoBERTa, T5, DistilBERT)
- **Visual Token Analysis**: Color-coded token visualization with 29 different color schemes
- **Rich Text Editor**: Built-in code editor with line numbers and syntax highlighting
- **Token Statistics**: Real-time tracking of token count, character count, and word count
- **Custom UI**: Modern, Nord-themed interface with customizable token highlighting
- **File Management**: Open and save text files directly within the application
- **Search Functionality**: Built-in find and replace capabilities
- **Token Information**: Hover over tokens to see their IDs and details
- **Keyboard Shortcuts**: Efficient workflow with keyboard shortcuts for common operations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tokenz-machine.git
cd tokenz-machine
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python tokenz_machine.py
```

## Requirements

- Python 3.6+
- PyQt5
- transformers
- torch (for transformer models)

## Usage

1. Launch the application
2. Select your desired transformer model from the dropdown
3. Choose a color gradient for token visualization
4. Enter or paste your text in the left panel
5. Click "Tokenize" or press Ctrl+T to see the visualization
6. Hover over tokens to see additional information
7. Use the toolbar or keyboard shortcuts for various operations

### Keyboard Shortcuts

- `Ctrl+T`: Tokenize text
- `Ctrl+S`: Save file
- `Ctrl+O`: Open file
- `Ctrl+F`: Find/Replace
- `Ctrl+L`: Clear text

## Contributing

Contributions are welcome! Whether you want to fix bugs, add new features, improve documentation, or suggest enhancements, please feel free to:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Creator

- **Matt Wesney** - Initial work and maintenance

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Nord Theme for the color scheme inspiration
- Hugging Face for the transformers library
- PyQt5 for the GUI framework

---

**Release Date:** February 6, 2025

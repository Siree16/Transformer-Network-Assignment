# 🖥️ Deep Learning Assignment 2

Welcome to the Deep Learning Assignment 2 repository for CSL7590. This assignment involves implementing a transformer network in Python using PyTorch for multi-class classification on an audio dataset. The project is divided into three tasks. Follow the guidelines and instructions provided below to understand the solutions thoroughly.

## 📄 Table of Contents
- [General Instructions](#general-instructions)
- [Submission Guidelines](#submission-guidelines)
- [Objective](#objective)
- [Tasks](#tasks)
  - [Task 1: Convolution-Based Feature Extraction](#task-1-convolution-based-feature-extraction)
  - [Task 2: Hybrid Convolution and Transformer Network](#task-2-hybrid-convolution-and-transformer-network)
  - [Task 3: Model Analysis and Evaluation](#task-3-model-analysis-and-evaluation)
- [Solution Summary](#solution-summary)
- [Contact Information](#contact-information)

---

## General Instructions 📋
1. Clearly mention any assumptions you have made.
2. Report any resources you used while attempting the assignment.
3. Submissions in any other format or after the deadline will not be evaluated.
4. Add references to the resources used.
5. Plagiarism will result in zero marks for both code and report.
6. Select your dataset correctly.

## Submission Guidelines 📑
1. Prepare a Python code file named `YourRollNo.py`. There should be only one .py file.
2. Submit a single report named `YourRollNo.pdf`, containing methods, results, and observations.
3. Provide your Colab file link in the report.
4. Upload both the code and report directly on Google Classroom.
5. Do not upload .ipynb files or screenshots in the report.

## Objective 🎯
Implement a transformer network in Python using the PyTorch framework. The network should be able to train on a simple audio dataset for multi-class classification.

## Tasks 🧪

### Task 1: Convolution-Based Feature Extraction
1. **Feature Extraction**:
   - Use 1D-convolution for feature extraction.
   - The base network should be at least three layers deep.
   - Implement a fully connected layer for multi-class classification.

2. **Network Architecture**:
   - You are free to use any number of layers, strides, kernel size, number of filters, activation functions, pooling, and other parameters.
   - Use PyTorch only.

### Task 2: Hybrid Convolution and Transformer Network
1. **Feature Extraction**:
   - Use the same base network as in Task 1.

2. **Transformer Encoder**:
   - Implement a transformer encoder network on top of the base network.
   - Include a multi-head self-attention mechanism and an MLP head for classification.
   - The model should have at least two attention blocks with different numbers of heads (1, 2, 4).

3. **Detailed Analysis**:
   - Analyze which model achieves the best accuracy and explain why.
   - Implement self-attention from scratch for a 10-class classification problem using PyTorch.

### Task 3: Model Analysis and Evaluation
1. **Training**:
   - Train both architectures for 100 epochs.
   - Plot accuracy and loss per epoch using Weight and Biases (WandB) platform.

2. **Validation**:
   - Perform k-fold validation with k=4.

3. **Metrics**:
   - Prepare accuracy, confusion matrix, F1-scores, and AUC-ROC curve for the test set for all combinations of the network.
   - Report total trainable and non-trainable parameters.
   - Perform hyper-parameter tuning and report the best hyper-parameter set.

## Solution Summary 📝
### Task 1: Convolution-Based Feature Extraction
- **Dataset**: Environmental audio recordings categorized into 10 classes.
- **Network Architecture**: Three 1D convolution layers followed by a fully connected layer for classification.
- **Training Configuration**: Various hyperparameters explored to optimize the model's performance.

### Task 2: Hybrid Convolution and Transformer Network
- **Feature Extraction**: Same 1D convolution base network as Task 1.
- **Transformer Encoder**: Multi-head self-attention mechanism with an MLP head for classification.
- **Analysis**: Detailed analysis of different attention head configurations to understand the optimal setup for audio classification.

### Task 3: Model Analysis and Evaluation
- **Training**: Conducted for 100 epochs with accuracy and loss tracked on WandB.
- **Validation**: Performed k-fold validation and comprehensive evaluation metrics for all network configurations.
- **Hyper-Parameter Tuning**: Best set of hyperparameters reported to enhance model performance.


# -*- coding: utf-8 -*-
"""M23CSE023_two

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dcQ9RTZVnV0wwD9YzsoMgRKlRc-MtQ0h
"""

!pip install wandb lightning

from google.colab import drive
drive.mount('/content/drive')

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from pathlib import Path
import torchaudio
from torchvision.transforms import Compose
import torchaudio.transforms as T
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_auc_score, roc_curve, auc
from sklearn.model_selection import StratifiedKFold
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import wandb


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, embed_dim, num_heads=1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.scaling = self.embed_dim ** -0.5

        self.query = nn.Linear(embed_dim, embed_dim)
        self.key = nn.Linear(embed_dim, embed_dim)
        self.value = nn.Linear(embed_dim, embed_dim)

        self.out_proj = nn.Linear(embed_dim, embed_dim)

    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_heads, self.embed_dim // self.num_heads)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(self, x):
        q = self.query(x)
        k = self.key(x)
        v = self.value(x)

        q = self.transpose_for_scores(q)
        k = self.transpose_for_scores(k)
        v = self.transpose_for_scores(v)

        attn_weights = torch.matmul(q, k.transpose(-1, -2))
        attn_weights *= self.scaling
        attn_weights = torch.nn.functional.softmax(attn_weights, dim=-1)

        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.transpose(1, 2).reshape(attn_output.size(0), -1, self.embed_dim)
        attn_output = self.out_proj(attn_output)

        return attn_output


class TransformerBlock(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout=0.1):
        super().__init__()
        self.attention = MultiHeadSelfAttention(embed_dim, num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

        self.ffn = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(embed_dim, embed_dim),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        attn_output = self.attention(x)
        x = x + self.dropout(attn_output)
        x = self.norm1(x)

        ffn_output = self.ffn(x)
        x = x + self.dropout(ffn_output)
        x = self.norm2(x)

        return x


class CustomConvNet(nn.Module):
    def __init__(self, num_classes, num_channels=40, transformer_heads=[1, 2, 4]):
        super(CustomConvNet, self).__init__()

        self.conv = nn.Sequential(
            nn.Conv1d(num_channels, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.MaxPool1d(kernel_size=2, stride=2),

            nn.Conv1d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.MaxPool1d(kernel_size=2, stride=2),

            nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.MaxPool1d(kernel_size=2, stride=2),
        )

        transformer_blocks = []
        for num_heads in transformer_heads:
            transformer_blocks.append(TransformerBlock(128, num_heads))

        self.transformer = nn.Sequential(*transformer_blocks)

        self.cls_token = nn.Parameter(torch.randn(1, 1, 128))  # Adding <cls> token

        self.classifier = nn.Sequential(
            nn.Linear(128, num_classes),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        x = self.conv(x)
        x = x.permute(0, 2, 1)
        cls_token = self.cls_token.expand(x.size(0), -1, -1)
        x = torch.cat([cls_token, x], dim=1)
        x = self.transformer(x)
        x = x.mean(dim=1)
        x = self.classifier(x)
        return x


def preprocess_audio(batch, sample_rate=44100):
    waveforms = []
    targets = []

    for audio_file, target in batch:
        waveform, _ = torchaudio.load(audio_file, normalize=True)

        transform = Compose([
            T.Resample(orig_freq=sample_rate, new_freq=16000),
            T.MFCC(),
            T.TimeMasking(time_mask_param=20),
            T.FrequencyMasking(freq_mask_param=30)
        ])

        processed_waveform = transform(waveform)
        waveforms.append(processed_waveform)
        targets.append(target)

    return torch.stack(waveforms).squeeze(1), torch.tensor(targets)


def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs, device, wandb_log=True):
    best_val_loss = float('inf')
    patience = 5
    epochs_no_improve = 0

    if wandb_log:
        wandb.watch(model, log='all')

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct_predictions = 0
        total_samples = 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            correct_predictions += (predicted == targets).sum().item()
            total_samples += targets.size(0)

        train_loss = running_loss / len(train_loader)
        train_accuracy = correct_predictions / total_samples

        # Validation
        val_loss, val_accuracy = evaluate_model(model, val_loader, criterion, device)

        if wandb_log:
            wandb.log({'epoch': epoch + 1, 'train_loss': train_loss, 'train_accuracy': train_accuracy,
                       'val_loss': val_loss, 'val_accuracy': val_accuracy})

        print(f"Epoch [{epoch+1}/{num_epochs}], Train Loss: {train_loss:.4f}, Train Accuracy: {train_accuracy:.4f}, "
              f"Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}")

        # if val_loss < best_val_loss:
        #     best_val_loss = val_loss
        #     epochs_no_improve = 0
        # else:
        #     epochs_no_improve += 1
        #     if epochs_no_improve == patience:
        #         print("Early stopping!")
        #         break

    print("Training completed.")


def evaluate_model(model, test_loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct_predictions = 0
    total_samples = 0

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            correct_predictions += (predicted == targets).sum().item()
            total_samples += targets.size(0)

    loss = running_loss / len(test_loader)
    accuracy = correct_predictions / total_samples

    return loss, accuracy


def count_parameters(model):
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    non_trainable_params = total_params - trainable_params
    return total_params, trainable_params, non_trainable_params


def main():
    path = '/content/drive/MyDrive/Archive/audio'
    df = pd.read_csv('/content/drive/MyDrive/Archive/meta/esc50.csv')

    esc_10_flag = True
    if esc_10_flag:
        df = df[df['esc10'] == True]

    wandb.init(project='Archi2_k_fold_', name='missclassyfyed', config={'epochs': 100, 'learning_rate': 0.001})

    kfold = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    fold = 1

    best_accuracy = 0.0
    best_hyperparameters = {}

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    label_encoder = LabelEncoder()
    df['target'] = label_encoder.fit_transform(df['category'])
    num_classes = len(label_encoder.classes_)

    for num_epochs in [100]:
        for learning_rate in [0.001]:
            for batch_size in [32, 64]:
                all_accuracies = []
                all_auc_roc_scores = []
                all_confusion_matrices = []
                all_f1_scores = []

                for train_indices, test_indices in kfold.split(df[['filename', 'target']], df['target']):
                    train_data, test_data = df.iloc[train_indices], df.iloc[test_indices]

                    model = CustomConvNet(num_classes=num_classes, num_channels=40)
                    model.to(device)

                    criterion = nn.CrossEntropyLoss()
                    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

                    train_dataset = [(Path(path) / filename, target) for filename, target in
                                     zip(train_data['filename'], train_data['target'])]
                    test_dataset = [(Path(path) / filename, target) for filename, target in
                                    zip(test_data['filename'], test_data['target'])]

                    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True,
                                              collate_fn=preprocess_audio)
                    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False,
                                             collate_fn=preprocess_audio)

                    val_size = int(0.1 * len(train_loader.dataset))
                    train_size = len(train_loader.dataset) - val_size
                    train_dataset, val_dataset = torch.utils.data.random_split(train_loader.dataset, [train_size, val_size])

                    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True,
                                              collate_fn=preprocess_audio)
                    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False,
                                            collate_fn=preprocess_audio)

                    train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs, device)

                    test_loss, test_accuracy = evaluate_model(model, test_loader, criterion, device)
                    print(f"Fold {fold}, Test Loss: {test_loss}, Test Accuracy: {test_accuracy}")

                    all_accuracies.append(test_accuracy)

                    y_true, y_pred = [], []
                    with torch.no_grad():
                        for inputs, targets in test_loader:
                            inputs, targets = inputs.to(device), targets.to(device)
                            outputs = model(inputs)
                            _, predicted = torch.max(outputs, 1)
                            y_true.extend(targets.cpu().numpy())
                            y_pred.extend(predicted.cpu().numpy())

                    confusion_matrix_fold = confusion_matrix(y_true, y_pred)
                    all_confusion_matrices.append(confusion_matrix_fold)

                    f1_scores_fold = classification_report(y_true, y_pred, output_dict=True)['macro avg']['f1-score']
                    all_f1_scores.append(f1_scores_fold)

                    all_y_true = []
                    all_y_probs = []

                    with torch.no_grad():
                        for inputs, targets in test_loader:
                            inputs, targets = inputs.to(device), targets.to(device)
                            outputs = model(inputs)
                            _, predicted = torch.max(outputs, 1)

                            all_y_true.extend(targets.cpu().numpy())
                            all_y_probs.extend(torch.nn.functional.softmax(outputs, dim=1).cpu().numpy())

                    auc_roc_score_fold = roc_auc_score(all_y_true, all_y_probs, multi_class='ovr')
                    all_auc_roc_scores.append(auc_roc_score_fold)

                    fold += 1

                average_accuracy = sum(all_accuracies) / len(all_accuracies)
                average_auc_roc_score = sum(all_auc_roc_scores) / len(all_auc_roc_scores)

                average_confusion_matrix = sum(all_confusion_matrices) / len(all_confusion_matrices)
                average_f1_score = sum(all_f1_scores) / len(all_f1_scores)

                print(f"\nHyperparameters: {num_epochs} epochs, {learning_rate} learning rate, {batch_size} batch size")
                print(f"Average Accuracy: {average_accuracy}")
                print("Average Confusion Matrix:\n", average_confusion_matrix)
                print(f"Average F1 Score: {average_f1_score}")
                print(f"Average AUC-ROC Score: {average_auc_roc_score}")

                if average_accuracy > best_accuracy:
                    best_accuracy = average_accuracy
                    best_hyperparameters = {'num_epochs': num_epochs, 'learning_rate': learning_rate,
                                            'batch_size': batch_size}

    model = CustomConvNet(num_classes=num_classes, num_channels=40)
    total_params, trainable_params, non_trainable_params = count_parameters(model)
    print(f"\nTotal Trainable Parameters: {trainable_params}")
    print(f"Total Non-trainable Parameters: {non_trainable_params}")

    print("\nBest Hyperparameters:", best_hyperparameters)

    wandb.finish()


if __name__ == "__main__":
    main()






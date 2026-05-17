import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

print("STEP 3: EVALUASI MODEL")

train_df = pd.read_csv("dataset/train.csv")
test_df = pd.read_csv("dataset/test.csv")

print("Data train:", train_df.shape)
print("Data test :", test_df.shape)

X_train = train_df.drop("loan_status", axis=1).values
y_train = train_df["loan_status"].values

X_test = test_df.drop("loan_status", axis=1).values
y_test = test_df["loan_status"].values

def euclidean_distance(data1, data2):
    """
    Menghitung jarak Euclidean antara
    data testing dan data training
    """

    return np.sqrt(np.sum((data1 - data2) ** 2))


def knn_predict(X_train, y_train, test_data, k=3):
    """
    Melakukan prediksi menggunakan:
    - Euclidean Distance
    - K Nearest Neighbor
    """

    distances = []

    for i in range(len(X_train)):

        distance = euclidean_distance(test_data, X_train[i])

        distances.append((distance, y_train[i]))

    distances.sort(key=lambda x: x[0])

    k_neighbors = distances[:k]

    labels = [label for _, label in k_neighbors]

    prediction = Counter(labels).most_common(1)[0][0]

    return prediction

predictions = []

print("\nHASIL PREDIKSI:\n")

for i in range(len(X_test)):

    pred = knn_predict(X_train, y_train, X_test[i], k=3)

    predictions.append(pred)

    print(f"Data ke-{i+1}")
    print("Actual   :", y_test[i])
    print("Prediksi :", pred)
    print("-" * 30)

accuracy = accuracy_score(y_test, predictions)

print("\n===================================")
print("HASIL EVALUASI MODEL")
print("===================================")

print(f"Akurasi Model : {accuracy * 100:.2f}%")

cm = confusion_matrix(y_test, predictions)

print("\nConfusion Matrix:")
print(cm)

report = classification_report(y_test, predictions)

print("\nClassification Report:")
print(report)
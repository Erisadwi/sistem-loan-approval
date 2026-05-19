from flask import Blueprint, render_template
import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import accuracy_score, confusion_matrix

evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route("/evaluation")
def evaluation():

    # LOAD DATA
    train_df = pd.read_csv("evaluation/dataset/train.csv")
    test_df = pd.read_csv("evaluation/dataset/train.csv")

    total_dataset = len(train_df) + len(test_df)

    X_train = train_df.drop("loan_status", axis=1).values
    y_train = train_df["loan_status"].values

    X_test = test_df.drop("loan_status", axis=1).values
    y_test = test_df["loan_status"].values

    # EUCLIDEAN
    def euclidean_distance(data1, data2):
        return np.sqrt(np.sum((data1 - data2) ** 2))

    # KNN
    def knn_predict(X_train, y_train, test_data, k=3):

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

    for i in range(len(X_test)):

        pred = knn_predict(X_train, y_train, X_test[i], k=3)

        predictions.append(pred)

    # AKURASI
    accuracy = accuracy_score(y_test, predictions)

    # CONFUSION MATRIX
    cm = confusion_matrix(y_test, predictions)

    tn, fp, fn, tp = cm.ravel()

    return render_template(
        "evaluation.html",
        total_dataset=total_dataset,
        train_count=len(train_df),
        test_count=len(test_df),
        accuracy=round(accuracy * 100, 2),
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp
    )
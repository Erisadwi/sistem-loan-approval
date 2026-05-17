import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

print("STEP 1: LOAD DATASET")
df = pd.read_csv("dataset/loan_raw.csv", skipinitialspace=True)
df.columns = df.columns.str.strip()

df = df.drop(columns=[
    "loan_id",
    "education",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value"
]) 

df["self_employed"] = df["self_employed"].astype(str).str.strip().map({
    "Yes": 1,
    "No": 0
})

df["loan_status"] = df["loan_status"].map({"Approved":1,"Rejected":0})

X = df.drop("loan_status", axis=1)
y = df["loan_status"]


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

scaler = MinMaxScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

train = pd.DataFrame(X_train, columns=X.columns)
train["loan_status"] = y_train.values
train.to_csv("dataset/train.csv", index=False)

test = pd.DataFrame(X_test, columns=X.columns)
test["loan_status"] = y_test.values
test.to_csv("dataset/test.csv", index=False)

print("SELESAI → train.csv & test.csv dibuat")
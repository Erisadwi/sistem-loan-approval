import pandas as pd

# Membaca dataset
df = pd.read_csv('train.csv')

# Memisahkan fitur dan label
X = df.drop('loan_status', axis=1)
y = df['loan_status']

# Menampilkan ukuran data
print("Jumlah data:", df.shape)
print("Jumlah fitur:", X.shape)
print("Jumlah label:", y.shape)
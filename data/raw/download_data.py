import os
import zipfile
import requests

# URLs của tập dữ liệu
train_url = "https://sid.erda.dk/share_redirect/3jCZUrrrDJ"
test_url = "https://sid.erda.dk/share_redirect/fdy6T4QVeP"

# Thư mục lưu trữ
os.makedirs("data", exist_ok=True)

# Hàm tải và giải nén file zip
def download_and_extract(url, output_path):
    filename = os.path.join("data", output_path)
    response = requests.get(url)
    with open(filename, "wb") as file:
        file.write(response.content)
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall("data")
    print(f"Đã tải và giải nén {output_path}")

# Tải và giải nén dữ liệu
download_and_extract(train_url, "GTSRB_Final_Training_Images.zip")
download_and_extract(test_url, "GTSRB_Final_Test_Images.zip")

print("Hoàn tất tải dữ liệu!")

import requests
from diff_handler import read_diff_files

# 1. Read the local diff file
diff_text = read_diff_files("tests/fixtures/sample_diff.txt")

# 2. Construct the JSON payload (matching what your API expects)
payload = {"diff": diff_text}

# 3. Send the POST request to the local Flask server
print("Sending request to server...")
response = requests.post("http://localhost:5000/review", json=payload)

# 4. Print the results
print(f"Status Code: {response.status_code}")
print("Response JSON:")
print(response.json())
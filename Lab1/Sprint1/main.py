import requests
import pandas as pd
import time
from tqdm import tqdm
from datetime import datetime

# Insira seu token do GitHub aqui
GITHUB_TOKEN = " "

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

# Função para obter os 1000 repositórios mais estrelados
def fetch_top_repositories():
    repos = []
    for page in range(1, 11):
        url = f"https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            repos.extend(r.json()["items"])
        else:
            print(f"Erro na página {page}: {r.status_code}")
            break
        time.sleep(1)
    return repos

# Função para contar releases
def get_releases_count(full_name):
    url = f"https://api.github.com/repos/{full_name}/releases"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return len(r.json())
    return None

# Função para contar pull requests aceitos (merged)
def get_pull_requests_count(full_name):
    url = f"https://api.github.com/repos/{full_name}/pulls?state=closed&per_page=100"
    r = requests.get(url, headers=HEADERS)
    count = 0
    if r.status_code == 200:
        prs = r.json()
        for pr in prs:
            if pr.get("merged_at"):
                count += 1
    return count
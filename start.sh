
git config --global user.email "1"
git config --global user.name "1"

python3 -m venv .venv 
source .venv/bin/activate
pip install uv 
uv pip install scrapy
virtualenv binance_venv --python=python3.10
source binance_venv/bin/activate
pip3 list
pip3 freeze > requirements.txt
pip3 install -r requirements.txt
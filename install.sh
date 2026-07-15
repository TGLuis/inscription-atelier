which python3
if [[ $? ]]; then
  sudo apt-get install python3
fi
sudo apt install python3-pip
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
chmod +x solve.py

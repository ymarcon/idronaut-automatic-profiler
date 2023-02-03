cd /home/user/idronaut-automatic-profiler

/home/user/.pyenv/versions/pylake/bin/python scripts/main.py live

/home/user/.pyenv/versions/pylake/bin/python scripts/upload_remote_data.py -d -w

curl "https://api.datalakes-eawag.ch/update/666"
curl "https://api.datalakes-eawag.ch/update/667"

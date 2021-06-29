# Cron and git already installed

# before running, enter these commands

# sudo git clone https://github.com/maskauen/binance-bot.git
# sudo chmod 777 binance-bot/
# sudo chmod +x binance-bot/ubuntu_setup.sh

###### Postgres #####################
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt install postgresql -y


###########################################


########## Python #########################
# Install python distribution inluding pip
sudo apt install python3 -y
sudo apt install python3-pip

# Install python libraries using pip
pip3 install -r requirements.txt

# Need to install ta-lib aswell with some extra steps
tar -xvf ta-lib-0.4.0-src.tar.gz

##########################################


# Restart
sudo systemctl restart postgresql


# Redis commands
wget https://download.redis.io/releases/redis-6.2.1.tar.gz
tar xzf redis-6.2.1.tar.gz

sudo apt install redis-tools

# Run this too
#cd redis-6.2.1
#make
#src/redis-server &

# Add crontabs via file
crontab /home/ubuntu/binance-bot/static/my_cron.txt
